#!/usr/bin/env python3
"""
Optimisation des embeddings pour la recherche par mood/émotion
Système mood-centric pour VibeFilms
"""

import json
import numpy as np
from sentence_transformers import SentenceTransformer
from supabase import create_client
import os
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

# Configuration Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://utzflwmghpojlsthyuqf.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV0emZsd21naHBvamxzdGh5dXFmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc1NDQxOTAsImV4cCI6MjA3MzEyMDE5MH0.j5qMspjG6FTN69DPwI0otqjw7Yp5lbbFadflpkjNvYc")

class MoodOptimizer:
    def __init__(self):
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.model = SentenceTransformer('paraphrase-MiniLM-L3-v2')
        
        # MOODS CLASSIQUES les plus fréquents
        self.classic_moods = {
            # Émotions de base
            "triste": {
                "synonyms": ["mélancolique", "déprimé", "nostalgique", "cafardeux", "morose"],
                "genres": ["Drame", "Romance"],
                "keywords": ["perte", "séparation", "mort", "mélancolie", "solitude", "chagrin", "larmes"]
            },
            "heureux": {
                "synonyms": ["joyeux", "content", "optimiste", "enjoué", "réjoui"],
                "genres": ["Comédie", "Familial", "Animation"],
                "keywords": ["bonheur", "joie", "sourire", "rire", "fête", "amitié", "amour", "victoire"]
            },
            "peur": {
                "synonyms": ["effrayé", "terrifié", "angoissé", "inquiet", "stressé"],
                "genres": ["Horreur", "Thriller"],
                "keywords": ["peur", "terreur", "angoisse", "suspense", "mystère", "danger", "frisson"]
            },
            "excité": {
                "synonyms": ["énergique", "dynamique", "motivé", "adrénaline", "intense"],
                "genres": ["Action", "Aventure", "Thriller"],
                "keywords": ["action", "adrénaline", "combat", "poursuite", "aventure", "énergie", "rythme"]
            },
            "romantique": {
                "synonyms": ["amoureux", "tendre", "passionné", "sentimental", "câlin"],
                "genres": ["Romance", "Drame"],
                "keywords": ["amour", "passion", "tendresse", "couple", "baiser", "romance", "cœur"]
            },
            "nostalgique": {
                "synonyms": ["mélancolique", "rêveur", "pensif", "contemplatif"],
                "genres": ["Drame", "Familial"],
                "keywords": ["passé", "souvenirs", "enfance", "mémoire", "temps", "rêverie", "mélancolie"]
            },
            "rire": {
                "synonyms": ["drôle", "amusant", "marrant", "hilarant", "comique", "rigolo"],
                "genres": ["Comédie"],
                "keywords": ["rire", "humour", "comédie", "blague", "drôle", "amusant", "gag", "sourire"]
            },
            "détendu": {
                "synonyms": ["calme", "paisible", "tranquille", "serein", "zen"],
                "genres": ["Drame", "Documentaire"],
                "keywords": ["calme", "paix", "sérénité", "détente", "tranquillité", "harmonie"]
            },
            "aventure": {
                "synonyms": ["exploration", "voyage", "découverte", "épique", "héroïque"],
                "genres": ["Aventure", "Action", "Fantastique"],
                "keywords": ["aventure", "voyage", "exploration", "découverte", "héros", "épique", "quête"]
            },
            "mystère": {
                "synonyms": ["énigmatique", "intriguant", "suspense", "complexe"],
                "genres": ["Mystère", "Thriller", "Crime"],
                "keywords": ["mystère", "énigme", "secret", "intrigue", "enquête", "révélation", "suspense"]
            }
        }
    
    def create_mood_text(self, movie):
        """Créer un texte optimisé mood pour l'embedding"""
        
        # Base : titre + synopsis
        mood_text = f"{movie.get('title', '')} {movie.get('overview', '')}"
        
        # Analyser les genres pour déduire les moods
        genres = movie.get('genre_names', [])
        detected_moods = []
        
        for mood, config in self.classic_moods.items():
            # Si genre correspond au mood
            if any(genre in config['genres'] for genre in genres):
                detected_moods.append(mood)
                # Ajouter les synonymes et keywords
                mood_text += f" {mood} " + " ".join(config['synonyms'])
                mood_text += " " + " ".join(config['keywords'])
        
        # Mapping spécial pour certains genres
        genre_mood_mapping = {
            "Science-Fiction": "futur technologie espace exploration découverte",
            "Fantastique": "magie fantasy imagination rêve merveilleux",
            "Guerre": "conflit bataille héroïsme sacrifice courage",
            "Western": "aventure désert cowboys justice frontier",
            "Musique": "émotion rythme mélodie passion artistique",
            "Sport": "compétition effort dépassement victoire équipe",
        }
        
        for genre in genres:
            if genre in genre_mood_mapping:
                mood_text += f" {genre_mood_mapping[genre]}"
        
        # Analyser le synopsis pour des mots-clés émotionnels
        synopsis = movie.get('overview', '').lower()
        
        emotion_keywords = {
            "amour": "romantique tendre passion couple",
            "mort": "triste mélancolique drame perte",
            "guerre": "intense action conflit héroïque",
            "famille": "émotion tendre familial chaleureux",
            "crime": "suspense mystère thriller danger",
            "comédie": "rire amusant drôle humour",
            "enfant": "nostalgique tendre familial innocent"
        }
        
        for keyword, emotions in emotion_keywords.items():
            if keyword in synopsis:
                mood_text += f" {emotions}"
        
        # Nettoyer et optimiser
        mood_text = " ".join(mood_text.split())  # Remove extra spaces
        
        return mood_text
    
    def get_all_movies(self):
        """Récupérer tous les films de Supabase"""
        try:
            response = self.supabase.table('movies').select('*').execute()
            print(f"📊 {len(response.data)} films récupérés de Supabase")
            return response.data
        except Exception as e:
            print(f"❌ Erreur récupération films: {e}")
            return []
    
    def update_movie_embedding(self, movie_id, new_embedding):
        """Mettre à jour l'embedding d'un film"""
        try:
            response = self.supabase.table('movies').update({
                'embedding': new_embedding
            }).eq('id', movie_id).execute()
            return True
        except Exception as e:
            print(f"❌ Erreur update film {movie_id}: {e}")
            return False
    
    def optimize_all_embeddings(self):
        """Optimiser tous les embeddings pour les moods"""
        movies = self.get_all_movies()
        if not movies:
            return
        
        print(f"🎭 Optimisation mood des embeddings pour {len(movies)} films...")
        
        successful_updates = 0
        
        for movie in tqdm(movies, desc="🔄 Optimisation mood"):
            # Créer le texte mood-optimisé
            mood_text = self.create_mood_text(movie)
            
            # Générer le nouvel embedding
            embedding = self.model.encode(mood_text)
            embedding_list = embedding.tolist()
            
            # Mettre à jour en base
            if self.update_movie_embedding(movie['id'], embedding_list):
                successful_updates += 1
            
            # Debug: afficher quelques exemples
            if successful_updates <= 3:
                print(f"\n🎬 {movie.get('title')} ({movie.get('genre_names', [])})")
                print(f"📝 Mood text: {mood_text[:100]}...")
        
        print(f"\n✅ {successful_updates}/{len(movies)} embeddings optimisés pour mood!")
        
        # Test immédiat
        self.test_mood_search()
    
    def test_mood_search(self):
        """Tester les recherches mood"""
        print(f"\n🧪 Test des recherches mood optimisées...")
        
        test_moods = [
            "je me sens triste",
            "j'ai envie de rire", 
            "je veux de la romance",
            "j'ai envie de me faire peur",
            "je me sens nostalgique"
        ]
        
        for mood in test_moods:
            print(f"\n🔍 Test: '{mood}'")
            
            # Générer embedding de la requête
            query_embedding = self.model.encode(mood).tolist()
            
            # Rechercher via Supabase
            try:
                response = self.supabase.rpc('match_movies', {
                    'query_embedding': query_embedding,
                    'match_threshold': 0.1,
                    'match_count': 3
                }).execute()
                
                results = response.data
                print(f"   📊 {len(results)} résultats:")
                
                for result in results[:2]:
                    title = result.get('title', 'Unknown')
                    genres = result.get('genre_names', [])
                    similarity = result.get('similarity', 0)
                    print(f"   • {title} ({', '.join(genres[:2])}) - {similarity:.3f}")
                    
            except Exception as e:
                print(f"   ❌ Erreur: {e}")

def main():
    print("🎭 VibeFilms - Optimisation Mood des Embeddings")
    print("=" * 60)
    
    optimizer = MoodOptimizer()
    optimizer.optimize_all_embeddings()

if __name__ == "__main__":
    main()