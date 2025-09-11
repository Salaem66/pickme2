#!/usr/bin/env python3
"""
Moteur de recherche vectorielle utilisant ChromaDB pour VibeFilms.
Remplace le système de fichiers pickle par une vraie base vectorielle.
"""

import chromadb
from chromadb.config import Settings
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional
import os
from collections import defaultdict
import re

class ChromaVectorEngine:
    def __init__(self, 
                 collection_name: str = "vibefilms_movies",
                 persist_directory: str = "./chroma_db",
                 model_name: str = "all-mpnet-base-v2"):
        """
        Initialise le moteur ChromaDB.
        
        Args:
            collection_name: Nom de la collection ChromaDB
            persist_directory: Répertoire de persistance
            model_name: Modèle SentenceTransformers
        """
        self.model_name = model_name
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        
        # Initialiser SentenceTransformers
        print(f"Chargement du modèle {model_name}...")
        self.model = SentenceTransformer(model_name)
        
        # Initialiser ChromaDB
        print(f"Initialisation ChromaDB dans {persist_directory}...")
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                is_persistent=True
            )
        )
        
        # Obtenir ou créer la collection avec notre fonction d'embedding
        try:
            self.collection = self.client.get_collection(name=collection_name)
            print(f"✅ Collection '{collection_name}' trouvée avec {self.collection.count()} films")
        except (ValueError, Exception):
            # Collection n'existe pas, la créer avec notre fonction d'embedding
            self.collection = self.client.create_collection(
                name=collection_name,
                embedding_function=None,  # Utiliser nos propres embeddings
                metadata={"description": "VibeFilms movie database with semantic search"}
            )
            print(f"✅ Collection '{collection_name}' créée")
        
        # Dictionnaire sémantique pour l'amélioration des requêtes
        self.emotion_semantics = {
            "joie": {
                "patterns": ["rire", "rigoler", "marrer", "drôle", "amusant", "comique", "comédie", 
                           "divertir", "fun", "rigolo", "hilarant", "sourire", "bonne humeur", "envie de rire"],
                "semantic_expansions": ["comedy", "humor", "funny", "entertaining", "cheerful", "lighthearted"],
                "boost_genres": ["comedy"],
                "boost_factor": 1.3
            },
            "tristesse": {
                "patterns": ["triste", "mélancolie", "déprimé", "pleurer", "émouvant", "touchant", 
                           "nostalgique", "émotionnel", "dramatique", "sombre"],
                "boost_genres": ["drama"],
                "boost_factor": 1.2
            },
            "peur": {
                "patterns": ["peur", "effrayant", "terrifiant", "horreur", "épouvante", "flipper",
                           "suspense", "anxiété", "sinistre", "macabre", "frissons", "avoir peur",
                           "frayeur", "angoisse", "tension"],
                "boost_genres": ["horror", "thriller"],
                "boost_factor": 2.0  # Boost plus fort pour priorité
            },
            "amour": {
                "patterns": ["amour", "romantique", "relation", "couple", "cœur", "passion",
                           "romance", "sentimental", "émotions"],
                "boost_genres": ["romance"],
                "boost_factor": 1.25
            },
            "action": {
                "patterns": ["action", "aventure", "combat", "guerre", "épique", "héros",
                           "intense", "adrénaline", "bataille"],
                "boost_genres": ["action", "adventure", "war"],
                "boost_factor": 1.3
            }
        }
    
    def load_movies_from_json(self, json_file: str) -> bool:
        """
        Charge les films depuis un fichier JSON dans ChromaDB.
        
        Args:
            json_file: Chemin vers le fichier JSON des films
            
        Returns:
            True si succès, False sinon
        """
        try:
            if not os.path.exists(json_file):
                print(f"❌ Fichier {json_file} introuvable")
                return False
            
            print(f"Chargement des films depuis {json_file}...")
            with open(json_file, 'r', encoding='utf-8') as f:
                movies_data = json.load(f)
            
            if isinstance(movies_data, dict) and 'movies' in movies_data:
                movies = movies_data['movies']
            elif isinstance(movies_data, list):
                movies = movies_data
            else:
                print(f"❌ Format JSON non reconnu dans {json_file}")
                return False
            
            # Vérifier si la collection est déjà peuplée
            existing_count = self.collection.count()
            if existing_count > 0:
                print(f"Collection déjà peuplée avec {existing_count} films")
                return True
            
            print(f"Ajout de {len(movies)} films à ChromaDB...")
            
            # Préparer les données pour ChromaDB
            documents = []
            metadatas = []
            ids = []
            embeddings = []
            
            print("Génération des embeddings avec sentence-transformers...")
            for i, movie in enumerate(movies):
                if i % 100 == 0:
                    print(f"  Traitement film {i+1}/{len(movies)}")
                
                movie_id = str(movie['id'])
                
                # Créer le document textuel pour l'embedding
                doc_text = self._create_movie_document(movie)
                documents.append(doc_text)
                
                # Générer l'embedding avec notre modèle
                embedding = self.model.encode(doc_text)
                embeddings.append(embedding.tolist())
                
                # Métadonnées (ChromaDB stocke automatiquement, pas de None autorisé)
                metadata = {
                    'title': movie.get('title') or '',
                    'overview': movie.get('overview') or '',
                    'release_date': movie.get('release_date') or '',
                    'vote_average': float(movie.get('vote_average') or 0),
                    'popularity': float(movie.get('popularity') or 0),
                    'genres': json.dumps(movie.get('genres') or []),
                    'poster_path': movie.get('poster_path') or '',
                    'runtime': int(movie.get('runtime') or 0),
                    'adult': bool(movie.get('adult', False)),
                    'original_title': movie.get('original_title') or '',
                    'original_language': movie.get('original_language') or '',
                    'vote_count': int(movie.get('vote_count') or 0),
                    'budget': int(movie.get('budget') or 0),
                    'revenue': int(movie.get('revenue') or 0),
                    'imdb_id': movie.get('imdb_id') or ''
                }
                
                # Ajouter les plateformes de streaming si disponibles
                if 'watch_providers' in movie and movie['watch_providers']:
                    wp = movie['watch_providers']
                    metadata['streaming_platforms'] = json.dumps(wp.get('streaming', []))
                    metadata['rent_platforms'] = json.dumps(wp.get('rent', []))
                    metadata['buy_platforms'] = json.dumps(wp.get('buy', []))
                
                metadatas.append(metadata)
                ids.append(movie_id)
            
            # Ajouter à ChromaDB avec nos embeddings précalculés
            print("Ajout des films à ChromaDB avec embeddings customisés...")
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings
            )
            
            print(f"✅ {len(movies)} films ajoutés avec succès à ChromaDB")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors du chargement: {e}")
            return False
    
    def _create_movie_document(self, movie: Dict) -> str:
        """
        Crée un document textuel représentant le film pour l'embedding.
        
        Args:
            movie: Données du film
            
        Returns:
            Document textuel
        """
        parts = []
        
        # Titre
        if movie.get('title'):
            parts.append(f"Titre: {movie['title']}")
        
        # Synopsis
        if movie.get('overview'):
            parts.append(f"Synopsis: {movie['overview']}")
        
        # Genres
        if movie.get('genres'):
            genres_str = ', '.join(movie['genres'])
            parts.append(f"Genres: {genres_str}")
        
        # Année
        if movie.get('release_date'):
            year = movie['release_date'][:4] if len(movie['release_date']) >= 4 else ''
            if year:
                parts.append(f"Année: {year}")
        
        # Note
        if movie.get('vote_average'):
            parts.append(f"Note: {movie['vote_average']}/10")
        
        return ' | '.join(parts)
    
    def search_by_mood(self, 
                      mood: str, 
                      top_k: int = 10,
                      platforms: Optional[List[str]] = None) -> List[Dict]:
        """
        Recherche de films par mood en utilisant ChromaDB.
        
        Args:
            mood: Description de l'humeur/mood
            top_k: Nombre de résultats à retourner
            platforms: Filtres par plateformes (optionnel)
            
        Returns:
            Liste des films correspondants avec scores
        """
        try:
            # Expansion sémantique de la requête
            expanded_mood = self._expand_mood_query(mood)
            
            # Générer l'embedding de la requête avec notre modèle
            query_embedding = self.model.encode(expanded_mood)
            
            # Construction des filtres ChromaDB
            where_filter = None
            if platforms:
                # ChromaDB ne supporte pas les filtres complexes sur JSON
                # On fera le filtrage post-recherche
                pass
            
            # Recherche vectorielle avec ChromaDB en utilisant notre embedding
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=min(top_k * 5, 200),  # Récupérer beaucoup plus pour améliorer la diversité
                where=where_filter
            )
            
            # Traitement des résultats
            movies_results = []
            
            if not results['documents'] or not results['documents'][0]:
                return movies_results
            
            documents = results['documents'][0]
            metadatas = results['metadatas'][0]
            distances = results['distances'][0]
            ids = results['ids'][0]
            
            for i, (doc, metadata, distance, movie_id) in enumerate(zip(
                documents, metadatas, distances, ids
            )):
                # Convertir distance en score de similarité 
                # ChromaDB utilise la distance L2 par défaut, on convertit en similarité
                similarity_score = max(0.0, 1.0 - (distance / 2.0))
                
                # Filtrage par plateformes si demandé
                if platforms:
                    streaming_platforms = json.loads(metadata.get('streaming_platforms', '[]'))
                    if not any(platform in streaming_platforms for platform in platforms):
                        continue
                
                # Reconstruction de l'objet film
                movie_result = {
                    'id': int(movie_id),
                    'title': metadata.get('title', ''),
                    'overview': metadata.get('overview', ''),
                    'release_date': metadata.get('release_date', ''),
                    'vote_average': metadata.get('vote_average', 0),
                    'popularity': metadata.get('popularity', 0),
                    'genres': json.loads(metadata.get('genres', '[]')),
                    'poster_path': metadata.get('poster_path'),
                    'runtime': metadata.get('runtime', 0),
                    'adult': metadata.get('adult', False),
                    'similarity_score': similarity_score
                }
                
                # Ajouter les plateformes de streaming si disponibles
                if metadata.get('streaming_platforms'):
                    movie_result['watch_providers'] = {
                        'streaming': json.loads(metadata.get('streaming_platforms', '[]')),
                        'rent': json.loads(metadata.get('rent_platforms', '[]')),
                        'buy': json.loads(metadata.get('buy_platforms', '[]'))
                    }
                
                movies_results.append(movie_result)
                
                # Arrêter quand on a assez de résultats
                if len(movies_results) >= top_k:
                    break
            
            # Boost sémantique des genres
            movies_results = self._apply_semantic_boost(movies_results, mood)
            
            # Diversification pour éviter les mêmes films/genres
            movies_results = self._diversify_results(movies_results, top_k)
            
            # Trier par score final
            movies_results.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            return movies_results[:top_k]
            
        except Exception as e:
            print(f"❌ Erreur lors de la recherche: {e}")
            return []
    
    def _expand_mood_query(self, mood: str) -> str:
        """
        Étend la requête mood avec des termes sémantiques SIMPLIFIÉS.
        
        Args:
            mood: Requête originale
            
        Returns:
            Requête étendue
        """
        mood_lower = mood.lower()
        
        # Chercher des correspondances sémantiques
        for emotion, data in self.emotion_semantics.items():
            for pattern in data["patterns"]:
                if pattern in mood_lower:
                    # Expansion SIMPLE : juste ajouter les genres principaux
                    genre_terms = " ".join(data["boost_genres"])
                    return f"{mood} {genre_terms}"
        
        # Si aucune émotion trouvée, retourner la requête originale
        return mood
    
    def _apply_semantic_boost(self, movies: List[Dict], mood: str) -> List[Dict]:
        """
        Applique un boost sémantique basé sur les genres et émotions.
        
        Args:
            movies: Liste des films
            mood: Requête mood originale
            
        Returns:
            Films avec scores boostés
        """
        mood_lower = mood.lower()
        
        for movie in movies:
            boost_factor = 1.0
            movie_genres = [g.lower() for g in movie.get('genres', [])]
            
            # Chercher des boosts émotionnels
            for emotion, data in self.emotion_semantics.items():
                for pattern in data["patterns"]:
                    if pattern in mood_lower:
                        # Boost si le genre correspond
                        for boost_genre in data["boost_genres"]:
                            if boost_genre.lower() in movie_genres:
                                boost_factor = max(boost_factor, data["boost_factor"])
                        break
            
            # Appliquer le boost
            movie['similarity_score'] *= boost_factor
        
        return movies
    
    def _diversify_results(self, movies: List[Dict], target_count: int) -> List[Dict]:
        """
        Diversifie les résultats en privilégiant d'abord les genres pertinents.
        
        Args:
            movies: Liste des films
            target_count: Nombre de films souhaités
            
        Returns:
            Films diversifiés
        """
        if len(movies) <= target_count:
            return movies
        
        # Séparer les films par pertinence de genre (si score élevé = genre pertinent)
        priority_films = []
        other_films = []
        
        for movie in movies:
            # Si le score est très élevé (>0.8), c'est probablement un genre pertinent
            if movie.get('similarity_score', 0) > 0.8:
                priority_films.append(movie)
            else:
                other_films.append(movie)
        
        # Diversifier d'abord les films prioritaires, puis les autres
        diversified = []
        seen_titles = set()
        genre_counts = defaultdict(int)
        
        # Traiter d'abord les films prioritaires (genres pertinents)
        for movie in priority_films:
            title = movie.get('title', '').lower()
            if title in seen_titles:
                continue
                
            movie_genres = movie.get('genres', [])
            primary_genre = movie_genres[0] if movie_genres else 'unknown'
            
            # Plus de tolérance pour les genres prioritaires
            if genre_counts[primary_genre] >= max(2, target_count // 2):
                continue
            
            diversified.append(movie)
            seen_titles.add(title)
            genre_counts[primary_genre] += 1
            
        # Puis ajouter des films variés des autres genres
        for movie in other_films:
            if len(diversified) >= target_count * 2:
                break
                
            title = movie.get('title', '').lower()
            if title in seen_titles:
                continue
                
            movie_genres = movie.get('genres', [])
            primary_genre = movie_genres[0] if movie_genres else 'unknown'
            
            # Limiter la répétition pour les autres genres
            if genre_counts[primary_genre] >= max(1, target_count // 4):
                continue
            
            diversified.append(movie)
            seen_titles.add(title)
            genre_counts[primary_genre] += 1
        
        return diversified
    
    def get_available_platforms(self) -> List[str]:
        """
        Retourne toutes les plateformes de streaming disponibles.
        
        Returns:
            Liste des plateformes uniques
        """
        try:
            # Récupérer tous les films pour extraire les plateformes
            all_results = self.collection.get()
            
            platforms = set()
            for metadata in all_results['metadatas']:
                streaming_platforms = json.loads(metadata.get('streaming_platforms', '[]'))
                platforms.update(streaming_platforms)
            
            return sorted(list(platforms))
            
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des plateformes: {e}")
            return []
    
    def get_stats(self) -> Dict:
        """
        Retourne les statistiques de la base vectorielle.
        
        Returns:
            Dictionnaire des statistiques
        """
        try:
            count = self.collection.count()
            
            # Collecter des stats sur les genres
            all_results = self.collection.get()
            genres_count = defaultdict(int)
            platforms_count = defaultdict(int)
            
            for metadata in all_results['metadatas']:
                # Genres
                genres = json.loads(metadata.get('genres', '[]'))
                for genre in genres:
                    genres_count[genre] += 1
                
                # Plateformes
                streaming_platforms = json.loads(metadata.get('streaming_platforms', '[]'))
                for platform in streaming_platforms:
                    platforms_count[platform] += 1
            
            return {
                "total_movies": count,
                "database_type": "ChromaDB Vector Database",
                "model_name": self.model_name,
                "collection_name": self.collection_name,
                "top_genres": dict(sorted(genres_count.items(), key=lambda x: x[1], reverse=True)[:10]),
                "top_platforms": dict(sorted(platforms_count.items(), key=lambda x: x[1], reverse=True)[:10]),
                "persist_directory": self.persist_directory
            }
            
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des stats: {e}")
            return {"total_movies": 0, "error": str(e)}
    
    def reset_database(self) -> bool:
        """
        Supprime et recrée la collection (pour les tests).
        
        Returns:
            True si succès
        """
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "VibeFilms movie database with semantic search"}
            )
            print(f"✅ Collection '{self.collection_name}' réinitialisée")
            return True
        except Exception as e:
            print(f"❌ Erreur lors de la réinitialisation: {e}")
            return False

if __name__ == "__main__":
    # Test rapide
    print("Test du moteur ChromaDB...")
    
    engine = ChromaVectorEngine()
    
    # Tenter de charger les données
    if os.path.exists('streaming_movies_500.json'):
        print("Chargement des films streaming...")
        engine.load_movies_from_json('streaming_movies_500.json')
    elif os.path.exists('sample_movies.json'):
        print("Chargement des films sample...")
        engine.load_movies_from_json('sample_movies.json')
    else:
        print("❌ Aucun fichier de films trouvé")
    
    # Test de recherche
    results = engine.search_by_mood("j'ai envie de rire", top_k=5)
    print(f"\n🎬 Résultats pour 'j'ai envie de rire': {len(results)} films")
    
    for movie in results:
        print(f"  - {movie['title']} (score: {movie['similarity_score']:.3f})")
    
    # Statistiques
    stats = engine.get_stats()
    print(f"\n📊 Stats: {stats['total_movies']} films dans ChromaDB")