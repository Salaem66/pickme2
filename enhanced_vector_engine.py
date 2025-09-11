import json
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Tuple
import pickle
import os
import re

class EnhancedVectorSearchEngine:
    def __init__(self, model_name: str = "all-mpnet-base-v2"):
        """
        Moteur de recherche vectorielle amélioré
        Utilise un modèle plus performant et des techniques d'enrichissement
        """
        print(f"Chargement du modèle amélioré {model_name}...")
        self.model = SentenceTransformer(model_name)
        self.movies = []
        self.embeddings = None
        self.movie_texts = []
        self.mood_embeddings = {}
        
        # Mapping des moods vers des descriptions enrichies
        self.mood_mappings = {
            "nostalgique": [
                "memories childhood past bittersweet melancholy sentimental touching emotional coming-of-age growing up reminiscence",
                "family relationships loss time passage youth innocence fading beautiful sadness wistful reflection"
            ],
            "rire": [
                "funny hilarious comedy humor laughs entertaining amusing witty clever jokes fun lighthearted",
                "silly absurd parody satire romantic comedy adventure comedy feel-good uplifting cheerful"
            ],
            "intense": [
                "thrilling suspenseful action-packed dramatic powerful overwhelming gripping heart-pounding adrenaline",
                "psychological tension high-stakes conflict confrontation battle fight survival dangerous exciting"
            ],
            "amour": [
                "romantic love passionate intimate heartwarming tender beautiful relationship couple chemistry",
                "soulmate romance wedding marriage devotion affection emotional connection true love destiny"
            ],
            "peur": [
                "scary frightening terrifying horror supernatural ghost monster creepy dark mysterious eerie",
                "psychological thriller jump scares haunted possession demon evil nightmare disturbing shocking"
            ],
            "triste": [
                "sad melancholy depressing tragic heartbreaking grief loss death sorrow emotional devastating",
                "drama tears crying mourning separation tragedy misfortune suffering pain lonely"
            ],
            "aventure": [
                "adventure journey quest exploration discovery treasure hunting epic heroic brave courage",
                "travel unknown lands pirates fantasy magical kingdoms ancient civilizations exotic places"
            ],
            "mystérieux": [
                "mystery puzzling enigmatic secretive hidden conspiracy investigation detective solving crimes",
                "unknown truth revelation suspense noir detective thriller cold case missing person"
            ],
            "inspirant": [
                "inspiring uplifting motivational triumphant overcoming obstacles success achievement dreams",
                "hope perseverance determination courage strength resilience against all odds victory"
            ]
        }
        
    def enhance_movie_text(self, movie: Dict) -> str:
        """
        Crée un texte enrichi pour de meilleurs embeddings
        """
        title = movie.get("title", "")
        overview = movie.get("overview", "")
        genres = movie.get("genres", [])
        vote_average = movie.get("vote_average", 0)
        release_year = ""
        
        if movie.get("release_date"):
            try:
                release_year = movie["release_date"][:4]
            except:
                pass
        
        # Enrichissement basé sur les genres
        genre_moods = []
        genre_lower = [g.lower() for g in genres]
        
        if "comedy" in genre_lower:
            genre_moods.extend(["funny", "humorous", "entertaining", "lighthearted", "amusing"])
        if "drama" in genre_lower:
            genre_moods.extend(["emotional", "touching", "deep", "meaningful", "character-driven"])
        if "horror" in genre_lower:
            genre_moods.extend(["scary", "frightening", "creepy", "dark", "terrifying"])
        if "romance" in genre_lower:
            genre_moods.extend(["romantic", "love", "passionate", "heartwarming", "intimate"])
        if "action" in genre_lower:
            genre_moods.extend(["exciting", "thrilling", "intense", "adrenaline", "dynamic"])
        if "thriller" in genre_lower:
            genre_moods.extend(["suspenseful", "tense", "gripping", "mysterious", "edge-of-seat"])
        if "adventure" in genre_lower:
            genre_moods.extend(["adventurous", "journey", "exploration", "heroic", "epic"])
        if "animation" in genre_lower:
            genre_moods.extend(["colorful", "imaginative", "creative", "family-friendly", "magical"])
        if "fantasy" in genre_lower:
            genre_moods.extend(["magical", "otherworldly", "enchanting", "mystical", "wonder"])
        if "science fiction" in genre_lower or "sci-fi" in genre_lower:
            genre_moods.extend(["futuristic", "technological", "innovative", "mind-bending", "visionary"])
        
        # Enrichissement basé sur la note
        if vote_average >= 8.0:
            genre_moods.extend(["masterpiece", "acclaimed", "exceptional", "brilliant"])
        elif vote_average >= 7.0:
            genre_moods.extend(["well-made", "quality", "recommended"])
        
        # Construction du texte enrichi
        mood_text = " ".join(genre_moods)
        
        enriched_text = f"""
        Title: {title}
        Genres: {' '.join(genres)}
        Mood and Atmosphere: {mood_text}
        Story: {overview}
        Year: {release_year}
        Quality: {'High-rated' if vote_average >= 7.0 else 'Standard'}
        """.strip()
        
        return enriched_text
    
    def enhance_mood_query(self, mood_query: str) -> str:
        """
        Enrichit la requête de mood avec des synonymes et contexte
        """
        mood_lower = mood_query.lower()
        
        # Détection des mots-clés de mood
        enhanced_parts = [mood_query]
        
        for mood_key, descriptions in self.mood_mappings.items():
            if mood_key in mood_lower or any(word in mood_lower for word in mood_key.split()):
                enhanced_parts.extend(descriptions)
        
        # Phrases d'enrichissement contextuelles
        context_phrases = [
            f"I want to watch a movie that makes me feel: {mood_query}",
            f"The perfect film for when I'm feeling: {mood_query}",
            f"A movie that captures the mood of: {mood_query}"
        ]
        
        enhanced_parts.extend(context_phrases)
        
        return " ".join(enhanced_parts)
    
    def load_movies(self, json_file: str):
        """Charge les films et prépare les textes enrichis"""
        print(f"Chargement des films depuis {json_file}...")
        with open(json_file, 'r', encoding='utf-8') as f:
            self.movies = json.load(f)
        
        # Filtrer les films sans description
        self.movies = [movie for movie in self.movies if movie.get("overview")]
        print(f"Films chargés: {len(self.movies)}")
        
        # Préparer les textes enrichis
        print("Enrichissement des descriptions de films...")
        self.movie_texts = [self.enhance_movie_text(movie) for movie in self.movies]
        
        # Échantillon pour vérification
        print(f"\nÉchantillon de texte enrichi:")
        print(self.movie_texts[0][:200] + "...")
    
    def create_embeddings(self):
        """Crée les embeddings avec le modèle amélioré"""
        if not self.movie_texts:
            raise ValueError("Aucun film chargé.")
        
        print("Création des embeddings améliorés...")
        self.embeddings = self.model.encode(
            self.movie_texts, 
            show_progress_bar=True,
            batch_size=16,  # Optimisation
            normalize_embeddings=True  # Normalisation pour de meilleures similarités
        )
        print(f"Embeddings créés: {self.embeddings.shape}")
        
        # Pré-calculer les embeddings des moods courants
        print("Pré-calcul des embeddings de moods...")
        common_moods = [
            "je me sens nostalgique",
            "j'ai envie de rire", 
            "quelque chose d'intense",
            "une histoire d'amour",
            "quelque chose qui fait peur",
            "je me sens triste",
            "une aventure épique",
            "quelque chose de mystérieux",
            "quelque chose d'inspirant"
        ]
        
        for mood in common_moods:
            enhanced_mood = self.enhance_mood_query(mood)
            self.mood_embeddings[mood] = self.model.encode([enhanced_mood], normalize_embeddings=True)[0]
    
    def detect_mood_intent(self, mood_query: str):
        """Détecte l'intention de mood dans la requête"""
        mood_lower = mood_query.lower()
        
        # Patterns de détection
        comedy_patterns = ["rire", "rigoler", "marrant", "drôle", "amusant", "comique", "humour", "funny", "comédie", "rigolo"]
        romance_patterns = ["amour", "romantique", "love", "romantic", "sentiment", "coeur", "passion"]
        horror_patterns = ["peur", "effrayant", "horror", "terreur", "scary", "creepy", "épouvante", "horreur", "flip"]
        action_patterns = ["action", "combat", "intense", "adrenaline", "baston", "explosif"]
        drama_patterns = ["triste", "émotion", "touching", "profond", "dramatique", "émotionnel", "pleurer"]
        
        detected = []
        if any(pattern in mood_lower for pattern in comedy_patterns):
            detected.append("Comedy")
        if any(pattern in mood_lower for pattern in romance_patterns):
            detected.append("Romance")
        if any(pattern in mood_lower for pattern in horror_patterns):
            detected.append("Horror")
        if any(pattern in mood_lower for pattern in action_patterns):
            detected.append("Action")
        if any(pattern in mood_lower for pattern in drama_patterns):
            detected.append("Drama")
            
        return detected

    def search_by_mood(self, mood_query: str, top_k: int = 10, boost_recent: bool = True, platforms: List[str] = None) -> List[Tuple[Dict, float]]:
        """
        Recherche améliorée par mood avec boost par genre
        """
        if self.embeddings is None:
            raise ValueError("Embeddings non disponibles.")
        
        # Détecter l'intention de mood
        intended_genres = self.detect_mood_intent(mood_query)
        
        # Utiliser l'embedding pré-calculé si disponible
        if mood_query in self.mood_embeddings:
            query_embedding = self.mood_embeddings[mood_query]
        else:
            enhanced_query = self.enhance_mood_query(mood_query)
            query_embedding = self.model.encode([enhanced_query], normalize_embeddings=True)[0]
        
        # Calculer la similarité
        similarities = cosine_similarity([query_embedding], self.embeddings)[0]
        
        # BOOST CRUCIAL PAR GENRE
        if intended_genres:
            print(f"🎯 Genres détectés: {intended_genres}")
            for i, movie in enumerate(self.movies):
                movie_genres = movie.get("genres", [])
                
                # Boost fort si genre correspondant
                for intended_genre in intended_genres:
                    if intended_genre in movie_genres:
                        # Boost proportionnel à la note
                        rating_boost = 1.0 + (movie.get("vote_average", 5) / 15)  # 1.0 à 1.67
                        similarities[i] *= (1.5 * rating_boost)  # Boost très significatif !
                        break
        
        # Boost optionnel pour les films récents et bien notés
        if boost_recent:
            for i, movie in enumerate(self.movies):
                vote_avg = movie.get("vote_average", 0)
                if vote_avg >= 8.0:
                    similarities[i] *= 1.1
                elif vote_avg >= 7.0:
                    similarities[i] *= 1.05
                    
                if movie.get("release_date"):
                    try:
                        year = int(movie["release_date"][:4])
                        if year >= 2000:
                            similarities[i] *= 1.02
                    except:
                        pass
        
        # Trier par similarité
        sorted_indices = np.argsort(similarities)[::-1]
        
        # Filtrer par plateformes si spécifié
        results = []
        for idx in sorted_indices:
            movie = self.movies[idx]
            score = float(similarities[idx])
            
            # Filtrage par plateformes
            if platforms:
                movie_platforms = movie.get("watch_providers", {})
                available_platforms = (
                    movie_platforms.get("streaming", []) + 
                    movie_platforms.get("rent", []) + 
                    movie_platforms.get("buy", [])
                )
                
                # Vérifier si au moins une plateforme demandée est disponible
                if not any(platform in available_platforms for platform in platforms):
                    continue
            
            results.append((movie, score))
            
            # Arrêter quand on a assez de résultats
            if len(results) >= top_k:
                break
        
        return results
    
    def save_embeddings(self, filepath: str = "enhanced_embeddings.pkl"):
        """Sauvegarde les embeddings améliorés"""
        data = {
            'embeddings': self.embeddings,
            'movies': self.movies,
            'movie_texts': self.movie_texts,
            'mood_embeddings': self.mood_embeddings,
            'model_name': str(self.model)
        }
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)
        print(f"Embeddings améliorés sauvegardés dans {filepath}")
    
    def load_embeddings(self, filepath: str = "enhanced_embeddings.pkl"):
        """Charge les embeddings améliorés"""
        if os.path.exists(filepath):
            print(f"Chargement des embeddings améliorés depuis {filepath}...")
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
            
            self.embeddings = data['embeddings']
            self.movies = data['movies']
            self.movie_texts = data['movie_texts']
            self.mood_embeddings = data.get('mood_embeddings', {})
            print(f"Embeddings améliorés chargés: {len(self.movies)} films")
            return True
        return False
    
    def get_mood_suggestions(self) -> List[str]:
        """Retourne des suggestions de moods optimisées"""
        return [
            "je me sens nostalgique",
            "j'ai envie de rire",
            "quelque chose d'intense et dramatique", 
            "une belle histoire d'amour",
            "du suspense et de l'action",
            "quelque chose qui fait peur",
            "un film inspirant et motivant",
            "du divertissement léger",
            "une aventure épique",
            "quelque chose de mystérieux",
            "un film qui fait réfléchir",
            "de la magie et du fantastique",
            "je me sens triste",
            "quelque chose d'émouvant"
        ]

if __name__ == "__main__":
    # Test du moteur amélioré
    engine = EnhancedVectorSearchEngine()
    
    if not engine.load_embeddings():
        engine.load_movies("movies_1000.json")
        engine.create_embeddings()
        engine.save_embeddings()
    
    # Tests comparatifs
    print("\n🧪 TESTS DU MOTEUR AMÉLIORÉ")
    print("=" * 50)
    
    test_moods = [
        "je me sens nostalgique",
        "j'ai envie de rire",
        "quelque chose d'intense",
        "une histoire d'amour",
        "quelque chose qui fait peur"
    ]
    
    for mood in test_moods:
        print(f"\n🎭 Mood: \"{mood}\"")
        results = engine.search_by_mood(mood, top_k=5)
        
        scores = [score for _, score in results]
        print(f"   Scores améliorés: {[f'{s:.3f}' for s in scores]}")
        
        titles = [movie["title"] for movie, _ in results]
        genres_list = [f"({', '.join(movie['genres'])})" for movie, _ in results]
        
        for i, (title, genre) in enumerate(zip(titles, genres_list)):
            print(f"   {i+1}. {title} {genre}")