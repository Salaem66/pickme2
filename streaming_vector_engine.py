#!/usr/bin/env python3
"""
Moteur vectoriel optimisé pour la base de données des 500 films disponibles en streaming.
"""

import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re

class StreamingVectorEngine:
    def __init__(self, embeddings_file='streaming_500_embeddings.pkl'):
        """Initialise le moteur vectoriel streaming."""
        self.model = None
        self.embeddings = None
        self.movies = None
        self.texts = None
        self.embeddings_file = embeddings_file
        
        # Mapping des moods amélioré avec plus de contexte
        self.mood_mappings = {
            "rire": ["comedy", "comédie", "humour", "drôle", "amusant", "hilarant", "funny", "comic"],
            "peur": ["horror", "horreur", "thriller", "suspense", "angoissant", "effrayant", "scary"],
            "amour": ["romance", "romantic", "romantique", "amour", "passion", "relation", "love"],
            "action": ["action", "adventure", "aventure", "combat", "explosif", "héroïque", "fight"],
            "réflexion": ["drama", "drame", "philosophique", "profond", "introspectif", "pensif"],
            "nostalgie": ["vintage", "classique", "retro", "nostalgique", "ancien", "classic"],
            "évasion": ["fantasy", "fantastique", "science fiction", "sci-fi", "imaginaire", "magique"],
            "motivation": ["inspirant", "motivant", "héroïque", "courage", "dépassement", "inspiring"],
            "intense": ["thriller", "action", "suspense", "intense", "dramatic"],
            "léger": ["comedy", "family", "comédie", "familial", "léger", "light"]
        }
        
        self.load_embeddings()
    
    def load_embeddings(self):
        """Charge les embeddings et les données des films."""
        try:
            print("Chargement du moteur vectoriel streaming...")
            
            with open(self.embeddings_file, 'rb') as f:
                data = pickle.load(f)
                self.embeddings = data['embeddings']
                self.movies = data['movies']
                self.texts = data['texts']
            
            # Charger le modèle
            self.model = SentenceTransformer('all-mpnet-base-v2')
            
            print(f"✅ Moteur vectoriel chargé: {len(self.movies)} films streaming")
            
        except FileNotFoundError:
            print(f"❌ Fichier {self.embeddings_file} non trouvé")
            raise
        except Exception as e:
            print(f"❌ Erreur lors du chargement: {e}")
            raise
    
    def detect_mood_keywords(self, query):
        """Détecte les mots-clés de mood dans la requête avec des patterns plus larges."""
        query_lower = query.lower()
        detected_genres = set()
        
        # Patterns spécifiques pour mieux détecter les moods
        mood_patterns = {
            "rire": ["rire", "rigoler", "marrer", "drôle", "amusant", "comique", "comédie", "humoristique"],
            "peur": ["peur", "effrayant", "terrorisant", "angoissant", "horreur", "épouvante", "faire peur"],
            "amour": ["amour", "romantique", "romance", "relation", "couple", "passion"],
            "action": ["action", "aventure", "combat", "bagarres", "explosions", "adrénaline"],
            "réflexion": ["réfléchir", "pensé", "profond", "drame", "sérieux", "philosophique"],
            "intense": ["intense", "thriller", "suspense", "tension", "haletant"],
            "léger": ["léger", "détente", "facile", "divertissant", "familial"]
        }
        
        for mood, patterns in mood_patterns.items():
            for pattern in patterns:
                if pattern in query_lower:
                    detected_genres.add(mood)
                    break  # Une fois qu'on trouve un pattern, pas besoin de continuer pour ce mood
        
        return detected_genres
    
    def boost_genre_similarity(self, similarities, query, boost_factor=1.8):
        """Booste la similarité pour les films correspondant au mood détecté."""
        detected_moods = self.detect_mood_keywords(query)
        
        if not detected_moods:
            return similarities
        
        boosted_similarities = similarities.copy()
        
        for i, movie in enumerate(self.movies):
            movie_genres = [g.lower() for g in movie.get('genres', [])]
            
            # Calculer le score de correspondance
            boost_multiplier = 1.0
            
            for mood in detected_moods:
                mood_keywords = self.mood_mappings.get(mood, [])
                for keyword in mood_keywords:
                    for genre in movie_genres:
                        # Match exact (ex: "comedy" == "comedy")
                        if keyword == genre:
                            boost_multiplier += 1.5  # +150%
                        # Match partiel (ex: "comedy" in "romantic comedy")  
                        elif keyword in genre or genre in keyword:
                            boost_multiplier += 0.8  # +80%
            
            # Appliquer le boost de manière progressive
            if boost_multiplier > 1.0:
                boosted_similarities[i] *= boost_multiplier
        
        return boosted_similarities
    
    def search_by_mood(self, mood_query, top_k=20, boost_recent=False, platforms=None):
        """
        Recherche des films par mood avec filtrage par plateformes.
        
        Args:
            mood_query: Requête décrivant le mood
            top_k: Nombre de résultats à retourner
            boost_recent: Booster les films récents
            platforms: Liste des plateformes à filtrer (optionnel)
        """
        if not self.model or self.embeddings is None:
            raise ValueError("Moteur non initialisé")
        
        # Créer l'embedding de la requête enrichie
        enriched_query = self.enrich_query(mood_query)
        query_embedding = self.model.encode([enriched_query])
        
        # Calculer les similarités
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        
        # Appliquer le boost par genre/mood
        similarities = self.boost_genre_similarity(similarities, mood_query)
        
        # Filtrer par plateformes si spécifié
        valid_indices = []
        for i, movie in enumerate(self.movies):
            if platforms:
                movie_platforms = []
                watch_providers = movie.get('watch_providers', {})
                for provider_type in ['streaming', 'rent', 'buy']:
                    movie_platforms.extend(watch_providers.get(provider_type, []))
                
                # Vérifier si au moins une plateforme demandée est disponible
                if not any(platform.lower() in [mp.lower() for mp in movie_platforms] for platform in platforms):
                    continue
            
            valid_indices.append(i)
        
        # Filtrer les similarités pour les indices valides
        if valid_indices:
            filtered_similarities = [(similarities[i], i) for i in valid_indices]
        else:
            filtered_similarities = [(similarities[i], i) for i in range(len(similarities))]
        
        # Trier par similarité
        filtered_similarities.sort(key=lambda x: x[0], reverse=True)
        
        # Appliquer le boost pour les films récents si demandé
        if boost_recent:
            current_year = 2025
            boosted_results = []
            
            for sim_score, idx in filtered_similarities[:top_k * 2]:  # Prendre plus pour le tri final
                movie = self.movies[idx]
                release_year = int(movie.get('release_date', '2000')[:4])
                
                # Booster les films récents (moins de 5 ans)
                if current_year - release_year <= 5:
                    sim_score *= 1.2
                
                boosted_results.append((sim_score, idx))
            
            # Re-trier après boost
            boosted_results.sort(key=lambda x: x[0], reverse=True)
            filtered_similarities = boosted_results
        
        # Construire les résultats avec normalisation des scores
        results = []
        max_score = filtered_similarities[0][0] if filtered_similarities else 1.0
        
        for sim_score, idx in filtered_similarities[:top_k]:
            movie = self.movies[idx].copy()
            
            # Normaliser le score entre 0 et 1, puis le convertir en pourcentage plus réaliste
            normalized_score = sim_score / max_score if max_score > 0 else 0
            # Ajuster le score pour qu'il soit plus représentatif (entre 30% et 95% pour les bons matches)
            display_score = max(0.3, min(0.95, normalized_score * 0.7 + 0.25))
            
            movie['similarity_score'] = float(display_score)
            
            # Ajouter les plateformes formatées
            watch_providers = movie.get('watch_providers', {})
            platforms_list = []
            for provider_type in ['streaming', 'rent', 'buy']:
                platforms_list.extend(watch_providers.get(provider_type, []))
            
            movie['available_platforms'] = list(set(platforms_list))
            
            results.append(movie)
        
        return results
    
    def enrich_query(self, mood_query):
        """Enrichit la requête avec des mots-clés relatifs au mood détecté."""
        detected_moods = self.detect_mood_keywords(mood_query)
        enriched_parts = [mood_query]
        
        for mood in detected_moods:
            keywords = self.mood_mappings.get(mood, [])
            # Ajouter les 3 premiers mots-clés les plus pertinents
            enriched_parts.extend(keywords[:3])
        
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
        
        # Compter les genres
        genre_count = {}
        for movie in self.movies:
            for genre in movie.get('genres', []):
                genre_count[genre] = genre_count.get(genre, 0) + 1
        
        # Compter les plateformes
        platform_count = {}
        for movie in self.movies:
            watch_providers = movie.get('watch_providers', {})
            for provider_type in ['streaming', 'rent', 'buy']:
                for platform in watch_providers.get(provider_type, []):
                    platform_count[platform] = platform_count.get(platform, 0) + 1
        
        # Statistiques par année
        year_count = {}
        for movie in self.movies:
            year = movie.get('release_date', '')[:4] if movie.get('release_date') else 'Unknown'
            year_count[year] = year_count.get(year, 0) + 1
        
        return {
            'total_movies': len(self.movies),
            'total_genres': len(genre_count),
            'total_platforms': len(platform_count),
            'top_genres': sorted(genre_count.items(), key=lambda x: x[1], reverse=True)[:10],
            'top_platforms': sorted(platform_count.items(), key=lambda x: x[1], reverse=True)[:10],
            'year_distribution': dict(sorted(year_count.items(), reverse=True)[:10])
        }

if __name__ == "__main__":
    # Test du moteur
    print("🚀 Test du moteur vectoriel streaming")
    
    try:
        engine = StreamingVectorEngine()
        
        # Test de recherche
        print("\n🔍 Test de recherche: 'je veux rire'")
        results = engine.search_by_mood("je veux rire", top_k=5)
        
        for i, movie in enumerate(results, 1):
            print(f"   {i}. {movie['title']} - Score: {movie['similarity_score']:.3f}")
            print(f"      Genres: {', '.join(movie['genres'])}")
            platforms = movie.get('available_platforms', [])
            print(f"      Plateformes: {', '.join(platforms[:3])}{'...' if len(platforms) > 3 else ''}")
        
        # Statistiques
        print(f"\n📊 Statistiques:")
        stats = engine.get_stats()
        print(f"   Total films: {stats['total_movies']}")
        print(f"   Top genres: {', '.join([f'{g} ({c})' for g, c in stats['top_genres'][:5]])}")
        print(f"   Top plateformes: {', '.join([f'{p} ({c})' for p, c in stats['top_platforms'][:5]])}")
        
        print("✅ Test réussi!")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")