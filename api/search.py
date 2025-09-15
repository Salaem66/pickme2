"""
Vercel serverless function pour la recherche de films
Version optimisée sans modèles lourds - utilise les embeddings pré-calculés
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
    import numpy as np
    import requests
except ImportError as e:
    # Fallback pour le développement local
    print(f"Importing fallback modules: {e}")

class SupabaseVectorEngine:
    """Moteur de recherche vectorielle avec Supabase - Version Vercel optimisée"""
    
    def __init__(self):
        # Configuration Supabase
        self.supabase_url = "https://utzflwmghpojlsthyuqf.supabase.co"
        self.supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV0emZsd21naHBvamxzdGh5dXFmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc1NDQxOTAsImV4cCI6MjA3MzEyMDE5MH0.j5qMspjG6FTN69DPwI0otqjw7Yp5lbbFadflpkjNvYc"
        
        # Client Supabase (utilise la clé anon pour les lectures)
        self.supabase = create_client(self.supabase_url, self.supabase_key)
    
    def generate_query_embedding_api(self, query: str) -> List[float]:
        """
        Génère l'embedding via sentence-transformers local (plus fiable)
        """
        try:
            # Essayer d'importer et utiliser sentence-transformers
            from sentence_transformers import SentenceTransformer

            # Charger le même modèle que pour les films
            model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
            embedding = model.encode(query).tolist()

            print(f"✅ Embedding généré via sentence-transformers: {len(embedding)} dimensions")
            return embedding

        except ImportError:
            print("⚠️ sentence-transformers non disponible, utilisation du fallback")
            return self.generate_keyword_embedding(query)
        except Exception as e:
            print(f"Error generating embedding via sentence-transformers: {e}")
            return self.generate_keyword_embedding(query)
    
    def generate_keyword_embedding(self, query: str) -> List[float]:
        """
        Génère un embedding simple basé sur des mots-clés
        Fallback léger sans modèle ML
        """
        # Mapping de mots-clés vers des dimensions d'embedding
        keyword_map = {
            # Genres
            'action': [0.8, 0.2, 0.1, 0.3],
            'comedy': [0.1, 0.9, 0.2, 0.1],
            'drama': [0.3, 0.1, 0.8, 0.4],
            'horror': [0.9, 0.1, 0.1, 0.7],
            'romance': [0.2, 0.7, 0.6, 0.8],
            'thriller': [0.7, 0.1, 0.3, 0.9],
            'sci-fi': [0.6, 0.3, 0.2, 0.5],
            'fantasy': [0.4, 0.5, 0.7, 0.6],
            
            # Émotions/Moods
            'triste': [0.2, 0.1, 0.9, 0.3],
            'heureux': [0.1, 0.8, 0.2, 0.7],
            'nostalgique': [0.4, 0.3, 0.7, 0.5],
            'excité': [0.8, 0.6, 0.2, 0.4],
            'relaxé': [0.3, 0.4, 0.5, 0.2],
            'romantique': [0.2, 0.7, 0.6, 0.8],
            'peur': [0.9, 0.1, 0.2, 0.8],
            
            # Mots français communs
            'film': [0.5, 0.5, 0.5, 0.5],
            'movie': [0.5, 0.5, 0.5, 0.5],
            'voir': [0.4, 0.6, 0.3, 0.4],
            'regarder': [0.4, 0.6, 0.3, 0.4],
        }
        
        # Créer un embedding de 384 dimensions (compatible avec all-MiniLM-L6-v2)
        embedding = [0.0] * 384
        words = query.lower().split()
        
        for word in words:
            if word in keyword_map:
                base_vec = keyword_map[word]
                # Répéter le pattern pour atteindre 384 dimensions
                for i in range(384):
                    embedding[i] += base_vec[i % len(base_vec)]
        
        # Normaliser
        if sum(x*x for x in embedding) > 0:
            norm = (sum(x*x for x in embedding)) ** 0.5
            embedding = [x/norm for x in embedding]
        else:
            # Embedding par défaut
            embedding = [1.0/384**0.5] * 384
        
        return embedding
    
    def search_movies(self,
                     query: str,
                     limit: int = 10,
                     similarity_threshold: float = 0.3,  # Plus bas pour le fallback
                     platforms: Optional[List[str]] = None,
                     genres: Optional[List[str]] = None,
                     fallback_limit: int = 5) -> Dict[str, Any]:
        """
        Recherche de films par similarité vectorielle avec système de fallback intelligent
        """
        try:
            # Générer l'embedding de la requête
            query_embedding = self.generate_query_embedding_api(query)

            # Détecter si la requête demande des comédies
            comedy_keywords = ['rire', 'drôle', 'marrant', 'comique', 'amusant', 'rigolo', 'hilarant', 'comédie']
            is_comedy_request = any(keyword in query.lower() for keyword in comedy_keywords)

            # Construire les filtres de genre si fournis
            genre_filter = None
            if genres:
                genre_filter = genres
            elif is_comedy_request:
                # Auto-filtrer sur les comédies si détecté
                genre_filter = ['Comedy', 'Comédie']

            # Appeler la fonction de recherche Supabase (prendre plus de résultats pour le filtrage)
            result = self.supabase.rpc('match_movies_v2', {
                'query_embedding': query_embedding,
                'match_threshold': similarity_threshold,
                'match_count': limit * 3,  # Récupérer plus pour compenser le filtrage
                'filter_genres': genre_filter
            }).execute()

            if not result.data:
                return {"preferred_results": [], "fallback_results": [], "total_count": 0}

            all_movies = result.data
            preferred_movies = []  # Films sur les plateformes préférées
            other_movies = []      # Films sur d'autres plateformes

            # Séparer les films selon leur disponibilité
            if platforms:
                for movie in all_movies:
                    streaming_platforms = movie.get('streaming_platforms', {})
                    if isinstance(streaming_platforms, dict):
                        available_platforms = streaming_platforms.get('streaming', [])

                        # Vérifier si le film est sur les plateformes préférées
                        is_on_preferred = any(platform.lower() in [p.lower() for p in available_platforms] for platform in platforms)

                        if is_on_preferred:
                            movie['availability_status'] = 'preferred'
                            preferred_movies.append(movie)
                        else:
                            movie['availability_status'] = 'other'
                            other_movies.append(movie)
            else:
                # Si aucune plateforme spécifiée, tous les films sont "préférés"
                preferred_movies = all_movies
                for movie in preferred_movies:
                    movie['availability_status'] = 'preferred'

            # Stratégie intelligente de fallback
            final_results = []

            # 1. Prendre d'abord les films préférés
            final_results.extend(preferred_movies[:limit])

            # 2. Si on n'a pas assez de résultats, compléter avec les autres
            remaining_slots = limit - len(final_results)
            if remaining_slots > 0 and len(preferred_movies) < fallback_limit:
                # Seulement faire le fallback si on a très peu de résultats préférés
                fallback_movies = other_movies[:remaining_slots]
                final_results.extend(fallback_movies)

            return {
                "preferred_results": preferred_movies[:limit],
                "fallback_results": other_movies[:remaining_slots] if remaining_slots > 0 and len(preferred_movies) < fallback_limit else [],
                "total_count": len(final_results),
                "fallback_used": len(preferred_movies) < fallback_limit and remaining_slots > 0
            }

        except Exception as e:
            print(f"Error searching movies: {e}")
            return {"preferred_results": [], "fallback_results": [], "total_count": 0}

# Instance globale pour la réutilisation
vector_engine = None

def get_vector_engine():
    """Singleton pattern pour l'engine"""
    global vector_engine
    if vector_engine is None:
        vector_engine = SupabaseVectorEngine()
    return vector_engine

class handler(BaseHTTPRequestHandler):
    """Handler pour les requêtes Vercel"""
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            # Parse URL
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            
            # Extraire les paramètres
            search_query = query_params.get('q', [''])[0]
            limit = int(query_params.get('limit', ['10'])[0])
            platforms = query_params.get('platforms', [])
            if platforms:
                platforms = platforms[0].split(',')
            
            if not search_query:
                self.send_error_response(400, "Missing query parameter 'q'")
                return
            
            # Effectuer la recherche
            engine = get_vector_engine()
            search_results = engine.search_movies(
                query=search_query,
                limit=limit,
                platforms=platforms
            )

            # Combiner les résultats pour la réponse
            all_results = search_results["preferred_results"] + search_results["fallback_results"]

            # Réponse JSON
            self.send_json_response({
                "query": search_query,
                "results": all_results,
                "count": len(all_results),
                "fallback_used": search_results["fallback_used"],
                "preferred_count": len(search_results["preferred_results"]),
                "fallback_count": len(search_results["fallback_results"])
            })
            
        except Exception as e:
            print(f"Error in GET handler: {e}")
            print(traceback.format_exc())
            self.send_error_response(500, f"Internal server error: {str(e)}")
    
    def do_POST(self):
        """Handle POST requests"""
        try:
            # Lire le body de la requête
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
            except json.JSONDecodeError:
                self.send_error_response(400, "Invalid JSON in request body")
                return
            
            # Extraire les paramètres
            search_query = data.get('query', '').strip()
            limit = data.get('limit', 10)
            platforms = data.get('platforms', [])
            genres = data.get('genres', [])
            
            if not search_query:
                self.send_error_response(400, "Missing 'query' field")
                return
            
            # Effectuer la recherche
            engine = get_vector_engine()
            search_results = engine.search_movies(
                query=search_query,
                limit=limit,
                platforms=platforms,
                genres=genres
            )

            # Combiner les résultats pour la réponse
            all_results = search_results["preferred_results"] + search_results["fallback_results"]

            # Réponse JSON
            self.send_json_response({
                "query": search_query,
                "results": all_results,
                "count": len(all_results),
                "fallback_used": search_results["fallback_used"],
                "preferred_count": len(search_results["preferred_results"]),
                "fallback_count": len(search_results["fallback_results"]),
                "filters": {
                    "platforms": platforms,
                    "genres": genres
                }
            })
            
        except Exception as e:
            print(f"Error in POST handler: {e}")
            print(traceback.format_exc())
            self.send_error_response(500, f"Internal server error: {str(e)}")
    
    def send_json_response(self, data: dict, status_code: int = 200):
        """Envoie une réponse JSON"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        response_json = json.dumps(data, ensure_ascii=False, indent=2)
        self.wfile.write(response_json.encode('utf-8'))
    
    def send_error_response(self, status_code: int, message: str):
        """Envoie une réponse d'erreur JSON"""
        self.send_json_response({
            "error": True,
            "message": message,
            "status_code": status_code
        }, status_code)
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

# Export pour Vercel
def handler_function(request):
    """Wrapper function for Vercel"""
    import io
    import sys
    from unittest.mock import Mock
    
    # Créer un mock de BaseHTTPRequestHandler pour Vercel
    mock_handler = handler(request, None, None)
    
    if request.method == 'GET':
        return mock_handler.do_GET()
    elif request.method == 'POST':
        return mock_handler.do_POST()
    elif request.method == 'OPTIONS':
        return mock_handler.do_OPTIONS()
    else:
        return mock_handler.send_error_response(405, "Method not allowed")