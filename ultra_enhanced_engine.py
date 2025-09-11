import json
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Tuple
import pickle
import os
import re

class UltraEnhancedVectorSearchEngine:
    def __init__(self, model_name: str = "all-mpnet-base-v2"):
        """
        Moteur ultra-amélioré avec logique hybride : vectoriel + règles
        """
        print(f"Chargement du moteur ultra-amélioré {model_name}...")
        self.model = SentenceTransformer(model_name)
        self.movies = []
        self.embeddings = None
        self.movie_texts = []
        self.genre_embeddings = {}
        
        # Patterns de moods avec synonymes et variantes
        self.mood_patterns = {
            "comedy": {
                "patterns": ["rire", "rigoler", "marrant", "drôle", "amusant", "comique", "humour", "funny", "hilare", 
                           "rigolo", "délire", "blague", "gag", "comical", "fun", "divertissant", "léger"],
                "boost_genres": ["Comedy"],
                "description": "laugh funny humor comedy entertaining amusing witty hilarious cheerful lighthearted jokes fun"
            },
            "romance": {
                "patterns": ["amour", "romantique", "love", "coeur", "sentiment", "couple", "relation", "passion", 
                           "romantic", "tender", "affection", "sentimental"],
                "boost_genres": ["Romance"],
                "description": "love romance romantic passionate intimate tender beautiful relationship couple chemistry soulmate"
            },
            "action": {
                "patterns": ["action", "combat", "bataille", "fight", "guerre", "intense", "adrenaline", "baston", 
                           "explosif", "dynamique", "energetic"],
                "boost_genres": ["Action", "Adventure"],
                "description": "action thrilling exciting intense adrenaline combat fight battle explosive dynamic"
            },
            "horror": {
                "patterns": ["peur", "effrayant", "horror", "terreur", "angoisse", "scary", "creepy", "épouvante", 
                           "horreur", "flipper", "terrifying", "nightmare"],
                "boost_genres": ["Horror", "Thriller"],
                "description": "scary frightening terrifying horror supernatural creepy dark mysterious eerie haunted"
            },
            "drama": {
                "patterns": ["triste", "émotion", "touching", "profond", "mélancolie", "drama", "dramatique", 
                           "émotionnel", "poignant", "bouleversant"],
                "boost_genres": ["Drama"],
                "description": "emotional touching deep meaningful dramatic powerful moving heartbreaking sad"
            },
            "thriller": {
                "patterns": ["suspense", "mystère", "tension", "thriller", "mystery", "énigme", "intrigue", 
                           "palpitant", "haletant"],
                "boost_genres": ["Thriller", "Mystery"],
                "description": "suspenseful mysterious thrilling tense gripping edge-of-seat puzzle enigmatic"
            },
            "adventure": {
                "patterns": ["aventure", "voyage", "exploration", "découverte", "épique", "heroic", "quest", 
                           "journey", "expedition"],
                "boost_genres": ["Adventure"],
                "description": "adventure journey quest exploration discovery epic heroic brave courage travel"
            },
            "fantasy": {
                "patterns": ["magie", "fantastique", "magic", "fantasy", "merveilleux", "féerique", "enchantement", 
                           "surnaturel", "mystique"],
                "boost_genres": ["Fantasy"],
                "description": "magical fantasy mystical enchanting otherworldly supernatural wonder fairy tale"
            },
            "nostalgic": {
                "patterns": ["nostalgique", "nostalgie", "souvenir", "passé", "enfance", "mémoire", "temps", 
                           "jeunesse", "mélancolie", "bittersweet"],
                "boost_genres": ["Drama", "Romance"],
                "description": "nostalgic memories childhood past bittersweet melancholy sentimental touching emotional"
            }
        }
        
    def detect_mood_category(self, mood_query: str):
        """
        Détecte la catégorie de mood principale dans la requête
        """
        mood_lower = mood_query.lower()
        detected_moods = []
        
        for category, config in self.mood_patterns.items():
            for pattern in config["patterns"]:
                if pattern in mood_lower:
                    detected_moods.append(category)
                    break
        
        # Si pas de mood détecté, essayer des mots composés
        if not detected_moods:
            if any(word in mood_lower for word in ["je veux", "j'ai envie", "je cherche"]):
                if any(word in mood_lower for word in ["rire", "rigoler", "marrer"]):
                    detected_moods.append("comedy")
                elif any(word in mood_lower for word in ["pleurer", "émouvoir", "toucher"]):
                    detected_moods.append("drama")
        
        return detected_moods
    
    def enhance_movie_text_ultra(self, movie: Dict) -> str:
        """
        Version ultra-enrichie des textes de films
        """
        title = movie.get("title", "")
        overview = movie.get("overview", "")
        genres = movie.get("genres", [])
        vote_average = movie.get("vote_average", 0)
        
        # Enrichissement par genre (plus agressif)
        genre_keywords = []
        genre_lower = [g.lower() for g in genres]
        
        # Comédies - enrichissement massif
        if "comedy" in genre_lower:
            genre_keywords.extend([
                "funny", "hilarious", "laugh", "humor", "amusing", "witty", "entertaining", 
                "lighthearted", "cheerful", "uplifting", "fun", "delightful", "comical",
                "satirical", "parody", "jokes", "gags", "comedic", "humorous", "playful",
                "whimsical", "silly", "absurd", "ridiculous", "laugh-out-loud", "giggle"
            ])
        
        # Romance - enrichissement émotionnel  
        if "romance" in genre_lower:
            genre_keywords.extend([
                "romantic", "love", "passion", "intimate", "tender", "heartwarming",
                "soulmate", "chemistry", "affection", "devotion", "wedding", "couple",
                "relationship", "valentine", "kiss", "embrace", "sweetheart", "beloved"
            ])
        
        # Horreur - enrichissement atmosphérique
        if "horror" in genre_lower:
            genre_keywords.extend([
                "scary", "frightening", "terrifying", "creepy", "eerie", "haunted", 
                "supernatural", "ghost", "demon", "monster", "nightmare", "spine-chilling",
                "bone-chilling", "blood-curdling", "sinister", "ominous", "macabre"
            ])
        
        # Action - enrichissement dynamique
        if "action" in genre_lower:
            genre_keywords.extend([
                "thrilling", "exciting", "intense", "adrenaline", "dynamic", "explosive",
                "fast-paced", "high-octane", "spectacular", "powerful", "energetic"
            ])
        
        # Drame - enrichissement émotionnel
        if "drama" in genre_lower:
            genre_keywords.extend([
                "emotional", "touching", "moving", "powerful", "meaningful", "deep",
                "profound", "character-driven", "heartbreaking", "poignant", "compelling"
            ])
        
        # Score boost words
        if vote_average >= 8.0:
            genre_keywords.extend(["masterpiece", "acclaimed", "brilliant", "exceptional", "outstanding"])
        elif vote_average >= 7.5:
            genre_keywords.extend(["excellent", "superb", "remarkable", "impressive"])
        elif vote_average >= 7.0:
            genre_keywords.extend(["great", "good", "quality", "well-made"])
        
        # Construction du texte ultra-enrichi
        mood_atmosphere = " ".join(genre_keywords)
        
        enriched_text = f"""
        Movie Title: {title}
        Genres: {' '.join(genres)}
        Mood Keywords: {mood_atmosphere}
        Emotional Tone: {mood_atmosphere}
        Story Description: {overview}
        Film Atmosphere: {mood_atmosphere}
        """.strip()
        
        return enriched_text
    
    def create_mood_query_ultra(self, mood_query: str) -> str:
        """
        Crée une requête ultra-enrichie basée sur la détection de mood
        """
        detected_moods = self.detect_mood_category(mood_query)
        
        if not detected_moods:
            # Fallback basique
            return f"I want to watch a movie that makes me feel: {mood_query}"
        
        # Construction ultra-enrichie
        enriched_parts = [mood_query]
        
        for mood_cat in detected_moods:
            if mood_cat in self.mood_patterns:
                config = self.mood_patterns[mood_cat]
                enriched_parts.append(config["description"])
                
                # Ajouter des variations contextuelles
                if mood_cat == "comedy":
                    enriched_parts.extend([
                        "I want to laugh and have fun watching this movie",
                        "This should be a funny entertaining comedy that makes me smile",
                        "Looking for humor jokes and amusing situations",
                        "A lighthearted film that brings joy and laughter"
                    ])
                elif mood_cat == "romance":
                    enriched_parts.extend([
                        "I want a romantic love story that touches my heart",
                        "Looking for passion chemistry and romantic moments",
                        "A beautiful love story with emotional connection"
                    ])
                elif mood_cat == "horror":
                    enriched_parts.extend([
                        "I want to be scared and frightened",
                        "Looking for terrifying supernatural horror",
                        "Something creepy that gives me chills"
                    ])
        
        return " ".join(enriched_parts)
    
    def search_by_mood_ultra(self, mood_query: str, top_k: int = 10) -> List[Tuple[Dict, float]]:
        """
        Recherche ultra-améliorée avec boost par genre
        """
        if self.embeddings is None:
            raise ValueError("Embeddings non disponibles.")
        
        # Détecter les moods
        detected_moods = self.detect_mood_category(mood_query)
        
        # Créer la requête enrichie
        enhanced_query = self.create_mood_query_ultra(mood_query)
        
        # Calculer l'embedding de la requête
        query_embedding = self.model.encode([enhanced_query], normalize_embeddings=True)[0]
        
        # Similarité vectorielle de base
        similarities = cosine_similarity([query_embedding], self.embeddings)[0]
        
        # BOOST PAR GENRE (c'est la clé !)
        if detected_moods:
            for i, movie in enumerate(self.movies):
                movie_genres = [g.lower() for g in movie.get("genres", [])]
                
                for mood_cat in detected_moods:
                    if mood_cat in self.mood_patterns:
                        boost_genres = [g.lower() for g in self.mood_patterns[mood_cat]["boost_genres"]]
                        
                        # Boost si le genre correspond
                        for boost_genre in boost_genres:
                            if boost_genre.lower() in movie_genres:
                                # Boost proportionnel à la note du film
                                rating_multiplier = 1.0 + (movie.get("vote_average", 5) / 20)  # 1.0 à 1.5
                                similarities[i] *= (1.3 * rating_multiplier)  # Boost significatif
                                break
        
        # Boost léger pour les films récents et bien notés
        for i, movie in enumerate(self.movies):
            vote_avg = movie.get("vote_average", 0)
            if vote_avg >= 7.5:
                similarities[i] *= 1.05
            
            # Boost films récents
            if movie.get("release_date"):
                try:
                    year = int(movie["release_date"][:4])
                    if year >= 2010:
                        similarities[i] *= 1.02
                except:
                    pass
        
        # Trier et retourner
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            movie = self.movies[idx]
            score = float(similarities[idx])
            results.append((movie, score))
        
        return results
    
    def load_movies(self, json_file: str):
        """Charge et enrichit les films"""
        print(f"Chargement des films depuis {json_file}...")
        with open(json_file, 'r', encoding='utf-8') as f:
            self.movies = json.load(f)
        
        self.movies = [movie for movie in self.movies if movie.get("overview")]
        print(f"Films chargés: {len(self.movies)}")
        
        print("Enrichissement ultra des descriptions...")
        self.movie_texts = [self.enhance_movie_text_ultra(movie) for movie in self.movies]
        
        print(f"Échantillon enrichi:")
        print(self.movie_texts[0][:300] + "...")
    
    def create_embeddings(self):
        """Crée les embeddings ultra-enrichis"""
        if not self.movie_texts:
            raise ValueError("Aucun film chargé.")
        
        print("Création des embeddings ultra-enrichis...")
        self.embeddings = self.model.encode(
            self.movie_texts, 
            show_progress_bar=True,
            batch_size=16,
            normalize_embeddings=True
        )
        print(f"Embeddings créés: {self.embeddings.shape}")
    
    def save_embeddings(self, filepath: str = "ultra_embeddings.pkl"):
        """Sauvegarde"""
        data = {
            'embeddings': self.embeddings,
            'movies': self.movies,
            'movie_texts': self.movie_texts,
            'model_name': str(self.model)
        }
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)
        print(f"Embeddings ultra sauvegardés dans {filepath}")
    
    def load_embeddings(self, filepath: str = "ultra_embeddings.pkl"):
        """Charge les embeddings ultra"""
        if os.path.exists(filepath):
            print(f"Chargement des embeddings ultra depuis {filepath}...")
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
            
            self.embeddings = data['embeddings']
            self.movies = data['movies']
            self.movie_texts = data['movie_texts']
            print(f"Embeddings ultra chargés: {len(self.movies)} films")
            return True
        return False
    
    def get_mood_suggestions(self) -> List[str]:
        """Suggestions optimisées"""
        return [
            "je veux rire",
            "j'ai envie d'une comédie",
            "quelque chose de drôle",
            "je me sens nostalgique", 
            "une belle histoire d'amour",
            "quelque chose de romantique",
            "j'ai envie d'action",
            "quelque chose d'intense",
            "j'ai envie d'avoir peur",
            "quelque chose d'effrayant",
            "je veux pleurer",
            "quelque chose d'émouvant",
            "une aventure épique",
            "de la magie et du fantastique"
        ]

if __name__ == "__main__":
    # Test ultra
    engine = UltraEnhancedVectorSearchEngine()
    
    if not engine.load_embeddings():
        engine.load_movies("movies_1000.json")
        engine.create_embeddings()
        engine.save_embeddings()
    
    # Test critique
    print("\n🎭 TEST ULTRA - JE VEUX RIRE")
    print("=" * 50)
    
    results = engine.search_by_mood_ultra("je veux rire", top_k=10)
    
    for i, (movie, score) in enumerate(results, 1):
        print(f"{i:2d}. {movie['title']} - Score: {score:.1%}")
        print(f"    Genres: {movie['genres']}")
        print(f"    Note: {movie['vote_average']}/10")
        print()