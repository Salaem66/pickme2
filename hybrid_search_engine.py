#!/usr/bin/env python3
"""
Moteur de recherche hybride pour VibeFilms.
Combine embeddings vectoriels avec règles sémantiques et contextuelles.
"""

import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re
from datetime import datetime

class HybridSearchEngine:
    def __init__(self, embeddings_file='streaming_500_embeddings.pkl'):
        """Initialise le moteur de recherche hybride."""
        self.model = None
        self.embeddings = None
        self.movies = None
        self.texts = None
        self.embeddings_file = embeddings_file
        
        # Dictionnaire émotionnel étendu
        self.emotion_mappings = {
            "joie": {
                "patterns": ["rire", "rigoler", "marrer", "drôle", "amusant", "comique", "comédie", "humoristique", "divertir", "fun"],
                "genres": ["comedy"],
                "boost": 2.0
            },
            "tristesse": {
                "patterns": ["triste", "mélancolie", "déprimé", "pleurer", "émouvant", "touchant"],
                "genres": ["drama"],
                "anti_genres": ["comedy"],
                "boost": 1.8
            },
            "peur": {
                "patterns": ["peur", "effrayant", "terrifiant", "angoissant", "horreur", "épouvante", "faire peur", "flipper"],
                "genres": ["horror", "thriller"],
                "boost": 2.5
            },
            "amour": {
                "patterns": ["amour", "romantique", "romance", "relation", "couple", "passion", "coeur"],
                "genres": ["romance"],
                "boost": 2.0
            },
            "excitation": {
                "patterns": ["action", "aventure", "combat", "bagarres", "explosions", "adrénaline", "intense"],
                "genres": ["action", "adventure", "thriller"],
                "boost": 1.8
            },
            "réflexion": {
                "patterns": ["réfléchir", "pensée", "profond", "philosophique", "sens", "signification"],
                "genres": ["drama"],
                "boost": 1.5
            },
            "détente": {
                "patterns": ["léger", "détente", "facile", "relaxant", "paisible", "calme"],
                "genres": ["family", "comedy", "animation"],
                "anti_genres": ["horror", "thriller"],
                "boost": 1.8
            },
            "inspiration": {
                "patterns": ["inspiré", "motivant", "courage", "espoir", "triomphe", "dépassement"],
                "genres": ["drama", "biography"],
                "boost": 1.8
            }
        }
        
        # Concepts spécialisés
        self.concept_mappings = {
            "visuel": {
                "patterns": ["belles images", "visuellement", "graphisme", "animation", "effets", "spectacle"],
                "genres": ["animation", "fantasy", "science fiction"],
                "boost": 1.5
            },
            "intelligent": {
                "patterns": ["intelligent", "réfléchi", "complexe", "subtil", "sophistiqué"],
                "genres": ["drama", "thriller", "mystery"],
                "boost": 1.6
            },
            "nostalgie": {
                "patterns": ["nostalgie", "ancien", "vintage", "classique", "rétro", "enfance"],
                "year_preference": "old",
                "boost": 1.4
            },
            "moderne": {
                "patterns": ["récent", "moderne", "nouveau", "contemporain", "actuel"],
                "year_preference": "recent", 
                "boost": 1.3
            },
            "famille": {
                "patterns": ["famille", "familial", "enfants", "tous âges"],
                "genres": ["family", "animation"],
                "boost": 1.8
            },
            "réalité": {
                "patterns": ["vraie histoire", "basé sur", "biographie", "documentaire", "réel"],
                "keywords": ["based on", "true story", "biography"],
                "boost": 1.7
            }
        }
        
        # Spécificités culturelles et linguistiques
        self.cultural_mappings = {
            "français": {
                "patterns": ["français", "france", "francophone"],
                "language": "fr",
                "boost": 1.5
            },
            "américain": {
                "patterns": ["américain", "hollywood", "usa"],
                "language": "en", 
                "boost": 1.2
            },
            "asiatique": {
                "patterns": ["asiatique", "japonais", "coréen", "chinois", "anime"],
                "languages": ["ja", "ko", "zh"],
                "boost": 1.4
            }
        }
        
        self.load_embeddings()
    
    def load_embeddings(self):
        """Charge les embeddings et les données des films."""
        try:
            print("Chargement du moteur hybride...")
            
            with open(self.embeddings_file, 'rb') as f:
                data = pickle.load(f)
                self.embeddings = data['embeddings']
                self.movies = data['movies']
                self.texts = data['texts']
            
            self.model = SentenceTransformer('all-mpnet-base-v2')
            print(f"✅ Moteur hybride chargé: {len(self.movies)} films")
            
        except Exception as e:
            print(f"❌ Erreur lors du chargement: {e}")
            raise
    
    def analyze_query(self, query):
        """Analyse complète de la requête utilisateur."""
        query_lower = query.lower()
        analysis = {
            "emotions": set(),
            "concepts": set(), 
            "cultural": set(),
            "boosts": {},
            "anti_genres": set(),
            "year_preference": None,
            "language_preference": None
        }
        
        # Analyser les émotions
        for emotion, config in self.emotion_mappings.items():
            for pattern in config["patterns"]:
                if pattern in query_lower:
                    analysis["emotions"].add(emotion)
                    analysis["boosts"][emotion] = config["boost"]
                    if "anti_genres" in config:
                        analysis["anti_genres"].update(config["anti_genres"])
                    break
        
        # Analyser les concepts
        for concept, config in self.concept_mappings.items():
            for pattern in config["patterns"]:
                if pattern in query_lower:
                    analysis["concepts"].add(concept)
                    analysis["boosts"][concept] = config["boost"]
                    if "year_preference" in config:
                        analysis["year_preference"] = config["year_preference"]
                    break
        
        # Analyser la culture/langue
        for culture, config in self.cultural_mappings.items():
            for pattern in config["patterns"]:
                if pattern in query_lower:
                    analysis["cultural"].add(culture)
                    analysis["boosts"][culture] = config["boost"]
                    if "language" in config:
                        analysis["language_preference"] = config["language"]
                    break
        
        return analysis
    
    def calculate_movie_score(self, movie, similarity_score, analysis):
        """Calcule le score final d'un film basé sur l'analyse de la requête."""
        final_score = similarity_score
        movie_genres = [g.lower() for g in movie.get('genres', [])]
        movie_year = int(movie.get('release_date', '2000')[:4]) if movie.get('release_date') else 2000
        movie_language = movie.get('original_language', '')
        movie_overview = movie.get('overview', '').lower()
        
        # Boost basé sur les émotions détectées
        for emotion in analysis["emotions"]:
            emotion_config = self.emotion_mappings[emotion]
            
            # Boost si genre correspondant
            for target_genre in emotion_config.get("genres", []):
                if any(target_genre in genre for genre in movie_genres):
                    final_score *= analysis["boosts"][emotion]
                    break
        
        # Boost basé sur les concepts
        for concept in analysis["concepts"]:
            concept_config = self.concept_mappings[concept]
            
            # Boost genre
            for target_genre in concept_config.get("genres", []):
                if any(target_genre in genre for genre in movie_genres):
                    final_score *= analysis["boosts"][concept]
                    break
            
            # Boost mots-clés dans overview
            for keyword in concept_config.get("keywords", []):
                if keyword in movie_overview:
                    final_score *= analysis["boosts"][concept] * 0.8
                    break
        
        # Pénalité pour anti-genres
        for anti_genre in analysis["anti_genres"]:
            if any(anti_genre in genre for genre in movie_genres):
                final_score *= 0.5  # Pénalité de 50%
        
        # Boost/pénalité basée sur l'année
        if analysis["year_preference"] == "recent":
            if movie_year >= 2020:
                final_score *= 1.5
            elif movie_year >= 2015:
                final_score *= 1.2
        elif analysis["year_preference"] == "old":
            if movie_year <= 2000:
                final_score *= 1.4
            elif movie_year <= 2010:
                final_score *= 1.2
        
        # Boost basé sur la langue
        if analysis["language_preference"]:
            if movie_language == analysis["language_preference"]:
                final_score *= 2.0  # Boost important pour la langue
        
        return final_score
    
    def search_by_mood(self, mood_query, top_k=20, boost_recent=False, platforms=None):
        """Recherche hybride combinant embeddings et règles sémantiques."""
        if not self.model or self.embeddings is None:
            raise ValueError("Moteur non initialisé")
        
        # 1. Analyser la requête
        analysis = self.analyze_query(mood_query)
        
        # 2. Enrichir la requête avec le contexte détecté
        enriched_query = self.enrich_query_with_analysis(mood_query, analysis)
        
        # 3. Recherche vectorielle
        query_embedding = self.model.encode([enriched_query])
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        
        # 4. Appliquer les règles hybrides
        enhanced_scores = []
        for i, base_score in enumerate(similarities):
            movie = self.movies[i]
            
            # Filtrage par plateformes
            if platforms:
                movie_platforms = []
                watch_providers = movie.get('watch_providers', {})
                for provider_type in ['streaming', 'rent', 'buy']:
                    movie_platforms.extend(watch_providers.get(provider_type, []))
                
                if not any(platform.lower() in [mp.lower() for mp in movie_platforms] for platform in platforms):
                    continue
            
            # Calcul du score hybride
            hybrid_score = self.calculate_movie_score(movie, base_score, analysis)
            enhanced_scores.append((hybrid_score, i))
        
        # 5. Trier par score hybride
        enhanced_scores.sort(key=lambda x: x[0], reverse=True)
        
        # 6. Normaliser et construire les résultats
        results = []
        max_score = enhanced_scores[0][0] if enhanced_scores else 1.0
        
        for hybrid_score, idx in enhanced_scores[:top_k]:
            movie = self.movies[idx].copy()
            
            # Score normalisé et réaliste
            normalized_score = hybrid_score / max_score if max_score > 0 else 0
            display_score = max(0.4, min(0.98, normalized_score * 0.6 + 0.35))
            
            movie['similarity_score'] = float(display_score)
            movie['analysis_debug'] = {
                'detected_emotions': list(analysis["emotions"]),
                'detected_concepts': list(analysis["concepts"]),
                'raw_score': float(hybrid_score)
            }
            
            # Ajouter les plateformes formatées
            watch_providers = movie.get('watch_providers', {})
            platforms_list = []
            for provider_type in ['streaming', 'rent', 'buy']:
                platforms_list.extend(watch_providers.get(provider_type, []))
            
            movie['available_platforms'] = list(set(platforms_list))
            results.append(movie)
        
        return results
    
    def enrich_query_with_analysis(self, original_query, analysis):
        """Enrichit la requête avec les concepts détectés."""
        enriched_parts = [original_query]
        
        # Ajouter les mots-clés émotionnels
        for emotion in analysis["emotions"]:
            emotion_config = self.emotion_mappings[emotion]
            enriched_parts.extend(emotion_config["genres"][:2])
        
        # Ajouter les mots-clés conceptuels  
        for concept in analysis["concepts"]:
            concept_config = self.concept_mappings[concept]
            enriched_parts.extend(concept_config.get("genres", [])[:2])
        
        return ' '.join(enriched_parts)
    
    def get_available_platforms(self):
        """Retourne la liste de toutes les plateformes disponibles."""
        platforms = set()
        for movie in self.movies:
            watch_providers = movie.get('watch_providers', {})
            for provider_type in ['streaming', 'rent', 'buy']:
                platforms.update(watch_providers.get(provider_type, []))
        return sorted(list(platforms))
    
    def get_stats(self):
        """Retourne les statistiques de la base de données."""
        if not self.movies:
            return {}
        
        genre_count = {}
        for movie in self.movies:
            for genre in movie.get('genres', []):
                genre_count[genre] = genre_count.get(genre, 0) + 1
        
        platform_count = {}
        for movie in self.movies:
            watch_providers = movie.get('watch_providers', {})
            for provider_type in ['streaming', 'rent', 'buy']:
                for platform in watch_providers.get(provider_type, []):
                    platform_count[platform] = platform_count.get(platform, 0) + 1
        
        return {
            'total_movies': len(self.movies),
            'total_genres': len(genre_count),
            'total_platforms': len(platform_count),
            'top_genres': sorted(genre_count.items(), key=lambda x: x[1], reverse=True)[:10],
            'top_platforms': sorted(platform_count.items(), key=lambda x: x[1], reverse=True)[:10]
        }

if __name__ == "__main__":
    print("🚀 Test du moteur hybride")
    
    try:
        engine = HybridSearchEngine()
        
        # Tests
        test_queries = [
            'je me sens triste',
            'je veux être inspiré', 
            'comédie française',
            'film récent avec de l\'aventure'
        ]
        
        for query in test_queries:
            print(f"\n🔍 Test: \"{query}\"")
            results = engine.search_by_mood(query, top_k=3)
            
            for i, movie in enumerate(results, 1):
                score = int(movie['similarity_score'] * 100)
                debug = movie.get('analysis_debug', {})
                print(f"   {i}. {movie['title']} - {score}%")
                print(f"      Genres: {movie['genres']}")
                print(f"      Détecté: {debug.get('detected_emotions', [])} + {debug.get('detected_concepts', [])}")
        
        print("\n✅ Test hybride réussi!")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")