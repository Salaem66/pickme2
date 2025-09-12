#!/usr/bin/env python3
"""
Générer les embeddings pour les films existants dans Supabase
"""

import os
from supabase import create_client
from sentence_transformers import SentenceTransformer

# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://utzflwmghpojlsthyuqf.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV0emZsd21naHBvamxzdGh5dXFmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc1NDQxOTAsImV4cCI6MjA3MzEyMDE5MH0.j5qMspjG6FTN69DPwI0otqjw7Yp5lbbFadflpkjNvYc")

def generate_embeddings():
    """Génère les embeddings pour tous les films sans embedding"""
    
    # Connexion
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Chargement du modèle
    print("🤖 Chargement du modèle sentence-transformers...")
    model = SentenceTransformer('paraphrase-MiniLM-L3-v2')
    
    try:
        # Récupérer tous les films
        movies_result = supabase.from_('movies').select('*').execute()
        movies = movies_result.data
        
        print(f"📽️ Trouvé {len(movies)} films")
        
        for movie in movies:
            movie_id = movie['id']
            
            # Vérifier si embedding existe déjà
            existing = supabase.from_('movie_embeddings').select('id').eq('movie_id', movie_id).execute()
            
            if existing.data:
                print(f"⏭️  Film {movie['title']} a déjà un embedding")
                continue
            
            # Créer le texte pour l'embedding
            title = movie.get('title', '')
            overview = movie.get('overview', '')
            genres = movie.get('genres', [])
            director = movie.get('director', '')
            cast = movie.get('cast_names', [])
            keywords = movie.get('keywords', [])
            
            # Construire le texte d'embedding
            embedding_text_parts = [title, overview]
            
            if genres:
                embedding_text_parts.extend(genres)
            
            if director:
                embedding_text_parts.append(f"directed by {director}")
                
            if cast and len(cast) > 0:
                main_cast = cast[:3]  # Top 3 acteurs
                embedding_text_parts.extend([f"starring {actor}" for actor in main_cast])
            
            if keywords and len(keywords) > 0:
                top_keywords = keywords[:5]  # Top 5 mots-clés
                embedding_text_parts.extend(top_keywords)
            
            embedding_text = ' '.join(filter(None, embedding_text_parts))
            
            print(f"🎬 Génération embedding pour: {title}")
            print(f"   Texte: {embedding_text[:100]}...")
            
            # Générer l'embedding
            embedding = model.encode(embedding_text, normalize_embeddings=True)
            
            # Insérer dans movie_embeddings
            embedding_data = {
                'movie_id': movie_id,
                'embedding': embedding.tolist(),
                'embedding_text': embedding_text
            }
            
            result = supabase.from_('movie_embeddings').insert(embedding_data).execute()
            
            if result.data:
                print(f"✅ Embedding créé pour: {title}")
            else:
                print(f"❌ Erreur pour: {title}")
        
        print(f"\n🎉 Embeddings générés avec succès!")
        
        # Vérification finale
        total_embeddings = supabase.from_('movie_embeddings').select('id', count='exact').execute()
        print(f"📊 Total embeddings: {total_embeddings.count}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    generate_embeddings()