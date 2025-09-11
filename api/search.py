"""
Vercel serverless function pour la recherche de films
Remplace l'ancien moteur ChromaDB par Supabase Vector
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import traceback
from typing import List, Dict, Any, Optional
from urllib.parse import parse_qs, urlparse

# Import des dépendances Vercel-compatibles
try:
    from supabase import create_client, Client
    from sentence_transformers import SentenceTransformer
    import numpy as np
except ImportError as e:
    # Fallback pour le développement local
    print(f"Importing fallback modules: {e}")

class SupabaseVectorEngine:
    """Moteur de recherche vectorielle avec Supabase"""
    
    def __init__(self):
        # Configuration Supabase
        self.supabase_url = "https://utzflwmghpojlsthyuqf.supabase.co"
        self.supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV0emZsd21naHBvamxzdGh5dXFmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc1NDQxOTAsImV4cCI6MjA3MzEyMDE5MH0.j5qMspjG6FTN69DPwI0otqjw7Yp5lbbFadflpkjNvYc"
        
        # Client Supabase (utilise la clé anon pour les lectures)
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        
        # Modèle d'embedding (chargé à la demande pour éviter les cold starts)
        self._model = None
    
    @property
    def model(self):
        """Chargement lazy du modèle d'embedding"""
        if self._model is None:
            self._model = SentenceTransformer('all-MiniLM-L6-v2')
        return self._model
    
    def generate_query_embedding(self, query: str) -> List[float]:
        """Génère l'embedding pour une requête"""
        try:
            embedding = self.model.encode(query, normalize_embeddings=True)
            return embedding.tolist()
        except Exception as e:
            print(f"Error generating embedding: {e}")
            # Retourner un embedding par défaut de 768 dimensions (zeros)
            return [0.0] * 768
    
    def search_movies(self, 
                     query: str, 
                     limit: int = 10, 
                     similarity_threshold: float = 0.6,
                     platforms: Optional[List[str]] = None,
                     genres: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Recherche de films par similarité vectorielle
        
        Args:
            query: Requête de recherche en texte libre
            limit: Nombre maximum de résultats
            similarity_threshold: Seuil de similarité minimum
            platforms: Liste de plateformes de streaming (optionnel)
            genres: Liste de genres (optionnel)
        """
        try:
            # Générer l'embedding de la requête
            query_embedding = self.generate_query_embedding(query)
            
            # Construire les filtres de genre si fournis
            genre_filter = None
            if genres:
                genre_filter = genres
            
            # Appeler la fonction de recherche Supabase
            result = self.supabase.rpc('match_movies', {
                'query_embedding': query_embedding,
                'match_threshold': similarity_threshold,
                'match_count': limit,
                'filter_genres': genre_filter
            }).execute()
            
            if not result.data:
                return []
            
            # Filtrer par plateforme si spécifié
            movies = result.data
            if platforms:
                filtered_movies = []
                for movie in movies:
                    streaming_platforms = movie.get('streaming_platforms', {})
                    if isinstance(streaming_platforms, dict):
                        available_platforms = streaming_platforms.get('streaming', [])
                        if any(platform.lower() in [p.lower() for p in available_platforms] for platform in platforms):
                            filtered_movies.append(movie)
                movies = filtered_movies
            
            # Formater les résultats
            formatted_movies = []
            for movie in movies:
                formatted_movie = {
                    'id': movie['tmdb_id'],
                    'title': movie['title'],
                    'overview': movie['overview'] or '',
                    'genres': movie['genres'] or [],
                    'release_date': movie['release_date'],
                    'vote_average': movie['vote_average'] or 0,
                    'poster_path': movie['poster_path'],
                    'streaming_platforms': movie['streaming_platforms'] or {},
                    'similarity': float(movie['similarity'])
                }
                formatted_movies.append(formatted_movie)
            
            return formatted_movies
            
        except Exception as e:
            print(f"Error in search_movies: {e}")
            traceback.print_exc()
            return []

# Instance globale du moteur (réutilisée entre les appels)
search_engine = None

def get_search_engine():
    """Récupère ou crée l'instance du moteur de recherche"""
    global search_engine
    if search_engine is None:
        search_engine = SupabaseVectorEngine()
    return search_engine

class handler(BaseHTTPRequestHandler):
    """Handler pour la fonction Vercel"""
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            # Parser l'URL et les paramètres
            parsed_url = urlparse(self.path)
            params = parse_qs(parsed_url.query)
            
            # Récupérer les paramètres de recherche
            query = params.get('query', [''])[0]
            limit = int(params.get('limit', ['10'])[0])
            similarity_threshold = float(params.get('threshold', ['0.6'])[0])
            
            # Paramètres de filtrage
            platforms = params.get('platforms[]', [])
            genres = params.get('genres[]', [])
            
            if not query.strip():
                self._send_error(400, "Query parameter is required")
                return
            
            # Effectuer la recherche
            engine = get_search_engine()
            results = engine.search_movies(
                query=query,
                limit=limit,
                similarity_threshold=similarity_threshold,
                platforms=platforms if platforms else None,
                genres=genres if genres else None
            )
            
            # Réponse JSON
            response_data = {
                'query': query,
                'results': results,
                'count': len(results)
            }
            
            self._send_json_response(200, response_data)
            
        except Exception as e:
            print(f"Error in handler: {e}")
            traceback.print_exc()
            self._send_error(500, f"Internal server error: {str(e)}")
    
    def do_POST(self):
        """Handle POST requests"""
        try:
            # Lire le body JSON
            content_length = int(self.headers.get('content-length', 0))
            if content_length == 0:
                self._send_error(400, "Request body is required")
                return
            
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)
            
            # Extraire les paramètres
            query = data.get('query', '').strip()
            limit = data.get('limit', 10)
            similarity_threshold = data.get('threshold', 0.6)
            platforms = data.get('platforms', [])
            genres = data.get('genres', [])
            
            if not query:
                self._send_error(400, "Query is required")
                return
            
            # Effectuer la recherche
            engine = get_search_engine()
            results = engine.search_movies(
                query=query,
                limit=limit,
                similarity_threshold=similarity_threshold,
                platforms=platforms if platforms else None,
                genres=genres if genres else None
            )
            
            # Réponse JSON
            response_data = {
                'query': query,
                'results': results,
                'count': len(results)
            }
            
            self._send_json_response(200, response_data)
            
        except json.JSONDecodeError:
            self._send_error(400, "Invalid JSON in request body")
        except Exception as e:
            print(f"Error in POST handler: {e}")
            traceback.print_exc()
            self._send_error(500, f"Internal server error: {str(e)}")
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self._send_cors_headers()
        self.send_response(200)
        self.end_headers()
    
    def _send_json_response(self, status_code: int, data: Dict[str, Any]):
        """Envoie une réponse JSON avec CORS"""
        self.send_response(status_code)
        self._send_cors_headers()
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        response_json = json.dumps(data, ensure_ascii=False, indent=2)
        self.wfile.write(response_json.encode('utf-8'))
    
    def _send_error(self, status_code: int, message: str):
        """Envoie une réponse d'erreur JSON avec CORS"""
        self.send_response(status_code)
        self._send_cors_headers()
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        error_data = {
            'error': message,
            'status': status_code
        }
        
        response_json = json.dumps(error_data, ensure_ascii=False)
        self.wfile.write(response_json.encode('utf-8'))
    
    def _send_cors_headers(self):
        """Ajoute les headers CORS"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Max-Age', '86400')