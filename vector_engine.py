import json
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Tuple
import pickle
import os

class VectorSearchEngine:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Moteur de recherche vectorielle pour les films
        Utilise SentenceTransformers pour créer des embeddings sémantiques
        """
        print(f"Chargement du modèle {model_name}...")
        self.model = SentenceTransformer(model_name)
        self.movies = []
        self.embeddings = None
        self.movie_texts = []
        
    def prepare_movie_text(self, movie: Dict) -> str:
        """
        Prépare le texte d'un film pour l'embedding
        Combine titre, genres et description
        """
        title = movie.get("title", "")
        overview = movie.get("overview", "")
        genres = " ".join(movie.get("genres", []))
        
        # Créer un texte enrichi pour de meilleurs embeddings
        text = f"Title: {title}. Genres: {genres}. Plot: {overview}"
        return text
    
    def load_movies(self, json_file: str):
        """Charge les films depuis un fichier JSON"""
        print(f"Chargement des films depuis {json_file}...")
        with open(json_file, 'r', encoding='utf-8') as f:
            self.movies = json.load(f)
        
        # Filtrer les films sans description
        self.movies = [movie for movie in self.movies if movie.get("overview")]
        print(f"Films chargés: {len(self.movies)}")
        
        # Préparer les textes pour embedding
        self.movie_texts = [self.prepare_movie_text(movie) for movie in self.movies]
    
    def create_embeddings(self):
        """Crée les embeddings pour tous les films"""
        if not self.movie_texts:
            raise ValueError("Aucun film chargé. Utilisez load_movies() d'abord.")
        
        print("Création des embeddings...")
        self.embeddings = self.model.encode(self.movie_texts, show_progress_bar=True)
        print(f"Embeddings créés: {self.embeddings.shape}")
    
    def save_embeddings(self, filepath: str = "embeddings.pkl"):
        """Sauvegarde les embeddings pour éviter de les recalculer"""
        data = {
            'embeddings': self.embeddings,
            'movies': self.movies,
            'movie_texts': self.movie_texts
        }
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)
        print(f"Embeddings sauvegardés dans {filepath}")
    
    def load_embeddings(self, filepath: str = "embeddings.pkl"):
        """Charge les embeddings depuis un fichier"""
        if os.path.exists(filepath):
            print(f"Chargement des embeddings depuis {filepath}...")
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
            
            self.embeddings = data['embeddings']
            self.movies = data['movies']
            self.movie_texts = data['movie_texts']
            print(f"Embeddings chargés: {len(self.movies)} films")
            return True
        return False
    
    def search_by_mood(self, mood_query: str, top_k: int = 10) -> List[Tuple[Dict, float]]:
        """
        Recherche de films basée sur une description de mood
        """
        if self.embeddings is None:
            raise ValueError("Embeddings non disponibles. Créez-les d'abord.")
        
        # Enrichir la requête de mood
        enriched_query = f"I want to watch a movie that makes me feel: {mood_query}. The mood and atmosphere should be: {mood_query}"
        
        # Créer l'embedding de la requête
        query_embedding = self.model.encode([enriched_query])
        
        # Calculer la similarité cosinus
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        
        # Trier par similarité
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        # Retourner les résultats avec leurs scores
        results = []
        for idx in top_indices:
            movie = self.movies[idx]
            score = float(similarities[idx])
            results.append((movie, score))
        
        return results
    
    def search_similar_movies(self, movie_id: int, top_k: int = 5) -> List[Tuple[Dict, float]]:
        """
        Trouve des films similaires à un film donné
        """
        if self.embeddings is None:
            raise ValueError("Embeddings non disponibles.")
        
        # Trouver l'index du film
        movie_idx = None
        for i, movie in enumerate(self.movies):
            if movie['id'] == movie_id:
                movie_idx = i
                break
        
        if movie_idx is None:
            return []
        
        # Calculer la similarité avec tous les autres films
        movie_embedding = self.embeddings[movie_idx:movie_idx+1]
        similarities = cosine_similarity(movie_embedding, self.embeddings)[0]
        
        # Exclure le film lui-même et prendre les top_k
        similarities[movie_idx] = -1  # Score très bas pour s'exclure
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if idx != movie_idx:  # Double vérification
                movie = self.movies[idx]
                score = float(similarities[idx])
                results.append((movie, score))
        
        return results
    
    def get_mood_suggestions(self) -> List[str]:
        """Retourne des suggestions de moods pour aider l'utilisateur"""
        return [
            "je me sens nostalgique",
            "j'ai envie de rire",
            "quelque chose d'intense et dramatique",
            "une histoire d'amour touchante",
            "du suspense et de l'action",
            "quelque chose qui fait peur",
            "un film inspirant et motivant",
            "du divertissement léger",
            "une aventure épique",
            "quelque chose de mystérieux",
            "un film qui fait réfléchir",
            "du fantastique et de la magie"
        ]

if __name__ == "__main__":
    # Test du moteur
    engine = VectorSearchEngine()
    
    # Charger ou créer les embeddings
    if not engine.load_embeddings():
        engine.load_movies("sample_movies.json")
        engine.create_embeddings()
        engine.save_embeddings()
    
    # Test de recherche
    print("\n=== Test de recherche par mood ===")
    mood = "je me sens nostalgique"
    results = engine.search_by_mood(mood, top_k=5)
    
    print(f"Recherche pour: '{mood}'")
    for i, (movie, score) in enumerate(results, 1):
        print(f"{i}. {movie['title']} (Score: {score:.3f})")
        print(f"   Genres: {', '.join(movie['genres'])}")
        print(f"   Synopsis: {movie['overview'][:100]}...")
        print()