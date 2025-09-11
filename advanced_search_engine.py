#!/usr/bin/env python3
"""
Moteur de recherche avancé pour VibeFilms.
Utilise l'analyse sémantique, la détection d'intentions et l'expansion de requêtes.
"""

import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re
from datetime import datetime
from collections import defaultdict

class AdvancedSearchEngine:
    def __init__(self, embeddings_file='streaming_500_embeddings.pkl'):
        """Initialise le moteur de recherche avancé."""
        self.model = None
        self.embeddings = None
        self.movies = None
        self.texts = None
        self.embeddings_file = embeddings_file
        
        # Dictionnaire sémantique étendu avec synonymes et variantes
        self.emotion_semantics = {
            "joie": {
                "patterns": ["rire", "rigoler", "marrer", "drôle", "amusant", "comique", "comédie", "humoristique", 
                           "divertir", "fun", "rigolo", "hilarant", "mourir de rire", "éclater de rire", "sourire",
                           "bonne humeur", "léger", "décontracté", "divertissement", "gai", "enjoué"],
                "semantic_expansions": ["comedy", "humor", "funny", "entertaining", "cheerful", "lighthearted"],
                "genres": ["comedy"],
                "boost": 2.2,
                "mood_score": 0.9
            },
            "tristesse": {
                "patterns": ["triste", "mélancolie", "déprimé", "pleurer", "émouvant", "touchant", "mélancolique",
                           "nostalgie", "nostalgique", "émotionnel", "larmes", "bouleversant", "poignant", 
                           "dramatique", "sombre", "lourd", "grave", "profond"],
                "semantic_expansions": ["sad", "emotional", "dramatic", "melancholy", "touching", "tearjerker"],
                "genres": ["drama"],
                "anti_genres": ["comedy"],
                "boost": 2.0,
                "mood_score": 0.3
            },
            "peur": {
                "patterns": ["peur", "effrayant", "terrifiant", "angoissant", "horreur", "épouvante", "faire peur", 
                           "flipper", "stresser", "tension", "suspense", "anxiété", "flippant", "inquiétant",
                           "sinistre", "macabre", "cauchemar", "frissonner", "sursauter"],
                "semantic_expansions": ["horror", "scary", "frightening", "terrifying", "suspenseful", "thriller"],
                "genres": ["horror", "thriller"],
                "boost": 2.5,
                "mood_score": 0.2
            },
            "amour": {
                "patterns": ["amour", "romantique", "romance", "relation", "couple", "passion", "coeur",
                           "sentimental", "tendresse", "attachement", "séduction", "charme", "attirance",
                           "mariage", "rencontre", "histoire d'amour", "coup de foudre", "émotionnel"],
                "semantic_expansions": ["romantic", "love story", "relationship", "romance", "passionate"],
                "genres": ["romance"],
                "boost": 2.0,
                "mood_score": 0.8
            },
            "excitation": {
                "patterns": ["action", "aventure", "combat", "bagarres", "explosions", "adrénaline", "intense",
                           "dynamique", "rythmé", "spectacle", "épique", "héroïque", "bataille", "guerre",
                           "poursuite", "course-poursuite", "cascades", "énergique", "puissant"],
                "semantic_expansions": ["action", "adventure", "thrilling", "exciting", "epic", "intense"],
                "genres": ["action", "adventure", "thriller"],
                "boost": 2.0,
                "mood_score": 0.9
            },
            "réflexion": {
                "patterns": ["réfléchir", "pensée", "profond", "philosophique", "sens", "signification",
                           "intellectuel", "contemplatif", "méditation", "questionnement", "introspection",
                           "complexe", "subtil", "analyse", "psychologique", "existentiel"],
                "semantic_expansions": ["philosophical", "thought-provoking", "deep", "intellectual", "complex"],
                "genres": ["drama", "documentary"],
                "boost": 1.8,
                "mood_score": 0.6
            },
            "énergie": {
                "patterns": ["énergique", "dynamique", "vivant", "pétillant", "motivant", "stimulant",
                           "entraînant", "rythmé", "musical", "danse", "mouvement", "jeunesse"],
                "semantic_expansions": ["energetic", "upbeat", "lively", "vibrant", "dynamic"],
                "genres": ["music", "musical", "animation"],
                "boost": 1.8,
                "mood_score": 0.8
            },
            "mystère": {
                "patterns": ["mystère", "mystérieux", "énigme", "secret", "intrigue", "enquête",
                           "investigation", "suspense", "indices", "résoudre", "découvrir", "révélation"],
                "semantic_expansions": ["mystery", "detective", "investigation", "puzzle", "crime"],
                "genres": ["mystery", "crime", "thriller"],
                "boost": 2.0,
                "mood_score": 0.7
            }
        }
        
        # Concepts thématiques avancés
        self.thematic_concepts = {
            "famille": {
                "patterns": ["famille", "familial", "enfants", "parents", "fratrie", "génération",
                           "tous âges", "familial", "générationnel", "héritage"],
                "semantic_expansions": ["family", "generational", "parental", "children"],
                "genres": ["family", "animation"],
                "boost": 1.9
            },
            "voyage": {
                "patterns": ["voyage", "voyager", "découverte", "exploration", "aventure", "road trip",
                           "partir", "s'échapper", "évasion", "ailleurs", "monde", "pays"],
                "semantic_expansions": ["travel", "journey", "exploration", "discovery", "adventure"],
                "genres": ["adventure", "drama"],
                "boost": 1.7
            },
            "futur": {
                "patterns": ["futur", "science-fiction", "sci-fi", "technologie", "robot", "espace",
                           "anticipation", "dystopie", "utopie", "virtuel", "intelligence artificielle"],
                "semantic_expansions": ["science fiction", "futuristic", "technology", "space", "dystopian"],
                "genres": ["science fiction"],
                "boost": 2.0
            },
            "passé": {
                "patterns": ["histoire", "historique", "époque", "période", "ancien", "guerre mondiale",
                           "moyen âge", "antiquité", "révolution", "biographie", "basé sur", "vraie histoire"],
                "semantic_expansions": ["historical", "period", "biography", "war", "based on true story"],
                "genres": ["history", "war", "biography"],
                "boost": 1.8
            },
            "nature": {
                "patterns": ["nature", "animaux", "environnement", "forêt", "océan", "montagne",
                           "wilderness", "sauvage", "écologie", "planète", "terre"],
                "semantic_expansions": ["nature", "wildlife", "environmental", "animals", "natural"],
                "genres": ["documentary", "adventure"],
                "boost": 1.6
            }
        }
        
        # Patterns d'intentions utilisateur
        self.intent_patterns = {
            "recommendation": ["recommend", "suggère", "conseil", "que regarder", "quoi regarder"],
            "mood_based": ["je me sens", "j'ai envie", "je veux", "j'aimerais", "mood", "humeur"],
            "genre_preference": ["film de", "du", "genre", "type de film"],
            "quality_focus": ["bon", "meilleur", "excellent", "top", "qualité", "chef d'oeuvre"],
            "recent_focus": ["récent", "nouveau", "sortie", "dernier", "2023", "2024", "actuel"]
        }
        
        self.load_embeddings()
    
    def load_embeddings(self):
        """Charge les embeddings et les données des films."""
        try:
            print("Chargement du moteur de recherche avancé...")
            
            with open(self.embeddings_file, 'rb') as f:
                data = pickle.load(f)
                self.embeddings = data['embeddings']
                self.movies = data['movies']
                self.texts = data['texts']
            
            self.model = SentenceTransformer('all-mpnet-base-v2')
            print(f"✅ Moteur avancé chargé: {len(self.movies)} films")
            
        except Exception as e:
            print(f"❌ Erreur lors du chargement: {e}")
            raise
    
    def analyze_intent(self, query):
        """Détecte l'intention de l'utilisateur dans la requête."""
        query_lower = query.lower()
        detected_intents = []
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if pattern in query_lower:
                    detected_intents.append(intent)
                    break
        
        return detected_intents
    
    def extract_semantic_concepts(self, query):
        """Extrait les concepts sémantiques de la requête."""
        query_lower = query.lower()
        analysis = {
            "emotions": {},
            "themes": {},
            "semantic_boost": 1.0,
            "detected_patterns": [],
            "mood_score": 0.5  # Score neutre par défaut
        }
        
        # Analyser les émotions avec scoring
        emotion_scores = []
        for emotion, config in self.emotion_semantics.items():
            emotion_strength = 0
            matched_patterns = []
            
            for pattern in config["patterns"]:
                if pattern in query_lower:
                    # Plus le pattern est long, plus il est spécifique
                    specificity_bonus = len(pattern.split()) * 0.1
                    emotion_strength += config["boost"] + specificity_bonus
                    matched_patterns.append(pattern)
            
            if emotion_strength > 0:
                analysis["emotions"][emotion] = {
                    "strength": emotion_strength,
                    "config": config,
                    "patterns": matched_patterns
                }
                emotion_scores.append(config.get("mood_score", 0.5))
        
        # Calculer le mood score global
        if emotion_scores:
            analysis["mood_score"] = np.mean(emotion_scores)
        
        # Analyser les thèmes
        for theme, config in self.thematic_concepts.items():
            theme_strength = 0
            matched_patterns = []
            
            for pattern in config["patterns"]:
                if pattern in query_lower:
                    theme_strength += config["boost"]
                    matched_patterns.append(pattern)
            
            if theme_strength > 0:
                analysis["themes"][theme] = {
                    "strength": theme_strength,
                    "config": config,
                    "patterns": matched_patterns
                }
        
        return analysis
    
    def expand_query(self, original_query, semantic_analysis):
        """Expanse la requête avec des termes sémantiquement liés."""
        expanded_terms = [original_query]
        
        # Ajouter les expansions sémantiques
        for emotion_data in semantic_analysis["emotions"].values():
            expanded_terms.extend(emotion_data["config"].get("semantic_expansions", []))
            expanded_terms.extend(emotion_data["config"].get("genres", []))
        
        for theme_data in semantic_analysis["themes"].values():
            expanded_terms.extend(theme_data["config"].get("semantic_expansions", []))
            expanded_terms.extend(theme_data["config"].get("genres", []))
        
        # Limiter la taille de la requête expansée
        unique_terms = list(dict.fromkeys(expanded_terms))[:15]
        return " ".join(unique_terms)
    
    def calculate_advanced_score(self, movie, base_similarity, semantic_analysis, intents):
        """Calcule un score avancé basé sur l'analyse sémantique."""
        final_score = base_similarity
        movie_genres = [g.lower() for g in movie.get('genres', [])]
        movie_year = int(movie.get('release_date', '2000')[:4]) if movie.get('release_date') else 2000
        movie_overview = movie.get('overview', '').lower()
        movie_title = movie.get('title', '').lower()
        
        # Boost émotionnel avancé
        for emotion, data in semantic_analysis["emotions"].items():
            emotion_config = data["config"]
            strength = data["strength"]
            
            # Boost basé sur les genres
            genre_match = any(genre in movie_genres[0] if movie_genres else False 
                            for genre in emotion_config.get("genres", []))
            if genre_match:
                final_score *= (1 + strength * 0.3)
            
            # Boost basé sur les mots-clés dans overview/titre
            for pattern in data["patterns"]:
                if pattern in movie_overview or pattern in movie_title:
                    final_score *= (1 + strength * 0.2)
                    break
        
        # Boost thématique
        for theme, data in semantic_analysis["themes"].items():
            theme_config = data["config"]
            strength = data["strength"]
            
            genre_match = any(genre in movie_genres[0] if movie_genres else False 
                            for genre in theme_config.get("genres", []))
            if genre_match:
                final_score *= (1 + strength * 0.25)
        
        # Boost basé sur l'intention
        if "recent_focus" in intents:
            if movie_year >= 2020:
                final_score *= 1.4
            elif movie_year >= 2015:
                final_score *= 1.2
        
        if "quality_focus" in intents:
            if movie.get('vote_average', 0) >= 7.5:
                final_score *= 1.3
            elif movie.get('vote_average', 0) >= 7.0:
                final_score *= 1.15
        
        # Pénalité pour anti-genres
        for emotion_data in semantic_analysis["emotions"].values():
            anti_genres = emotion_data["config"].get("anti_genres", [])
            for anti_genre in anti_genres:
                if any(anti_genre in genre for genre in movie_genres):
                    final_score *= 0.6
        
        return final_score
    
    def search_by_mood(self, mood_query, top_k=20, platforms=None):
        """Recherche avancée avec analyse sémantique et expansion de requêtes."""
        if not self.model or self.embeddings is None:
            raise ValueError("Moteur non initialisé")
        
        print(f"🔍 Analyse de: '{mood_query}'")
        
        # 1. Analyser l'intention et extraire les concepts sémantiques
        intents = self.analyze_intent(mood_query)
        semantic_analysis = self.extract_semantic_concepts(mood_query)
        
        print(f"Intentions détectées: {intents}")
        print(f"Émotions détectées: {list(semantic_analysis['emotions'].keys())}")
        print(f"Thèmes détectés: {list(semantic_analysis['themes'].keys())}")
        
        # 2. Expanse la requête
        expanded_query = self.expand_query(mood_query, semantic_analysis)
        print(f"Requête expansée: {expanded_query[:100]}...")
        
        # 3. Recherche vectorielle
        query_embedding = self.model.encode([expanded_query])
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        
        # 4. Calcul des scores avancés
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
            
            # Score avancé
            advanced_score = self.calculate_advanced_score(movie, base_score, semantic_analysis, intents)
            enhanced_scores.append((advanced_score, i))
        
        # 5. Trier et normaliser
        enhanced_scores.sort(key=lambda x: x[0], reverse=True)
        
        # 6. Construire les résultats
        results = []
        max_score = enhanced_scores[0][0] if enhanced_scores else 1.0
        
        for advanced_score, idx in enhanced_scores[:top_k]:
            movie = self.movies[idx].copy()
            
            # Score normalisé plus réaliste
            normalized_score = advanced_score / max_score if max_score > 0 else 0
            
            # Ajustement du score d'affichage basé sur la qualité de l'analyse
            confidence_bonus = 0
            if semantic_analysis["emotions"] or semantic_analysis["themes"]:
                confidence_bonus = 0.1  # +10% si on a détecté des patterns
            if len(semantic_analysis["emotions"]) >= 2:
                confidence_bonus += 0.05  # +5% si plusieurs émotions
            
            display_score = max(0.45, min(0.95, normalized_score * 0.65 + 0.3 + confidence_bonus))
            
            movie['similarity_score'] = float(display_score)
            movie['analysis_debug'] = {
                'detected_emotions': list(semantic_analysis["emotions"].keys()),
                'detected_themes': list(semantic_analysis["themes"].keys()),
                'detected_intents': intents,
                'mood_score': semantic_analysis["mood_score"],
                'raw_score': float(advanced_score)
            }
            
            # Ajouter les plateformes
            watch_providers = movie.get('watch_providers', {})
            platforms_list = []
            for provider_type in ['streaming', 'rent', 'buy']:
                platforms_list.extend(watch_providers.get(provider_type, []))
            
            movie['available_platforms'] = list(set(platforms_list))
            results.append(movie)
        
        return results
    
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
            'total_emotions': len(self.emotion_semantics),
            'total_themes': len(self.thematic_concepts),
            'top_genres': sorted(genre_count.items(), key=lambda x: x[1], reverse=True)[:10],
            'top_platforms': sorted(platform_count.items(), key=lambda x: x[1], reverse=True)[:10]
        }

if __name__ == "__main__":
    print("🚀 Test du moteur de recherche avancé")
    
    try:
        engine = AdvancedSearchEngine()
        
        # Tests avec différents types de requêtes
        test_queries = [
            'je me sens un peu mélancolique ce soir',
            'quelque chose de vraiment drôle pour me remonter le moral',
            'un film récent avec beaucoup d\'action et d\'aventure',
            'une histoire profonde qui fait réfléchir sur la vie',
            'un bon thriller psychologique avec du suspense',
            'une comédie française légère pour se détendre'
        ]
        
        for query in test_queries:
            print(f"\n🔍 Test: \"{query}\"")
            results = engine.search_by_mood(query, top_k=3)
            
            for i, movie in enumerate(results, 1):
                score = int(movie['similarity_score'] * 100)
                debug = movie.get('analysis_debug', {})
                print(f"   {i}. {movie['title']} - {score}%")
                print(f"      Genres: {movie['genres']}")
                print(f"      Émotions: {debug.get('detected_emotions', [])}")
                print(f"      Thèmes: {debug.get('detected_themes', [])}")
        
        print("\n✅ Test avancé réussi!")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")