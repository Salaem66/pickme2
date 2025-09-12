#!/usr/bin/env python3
"""
Génération des embeddings français optimisés mood pour tous les films
"""

import os
from supabase import create_client
from sentence_transformers import SentenceTransformer
import time

# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://utzflwmghpojlsthyuqf.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV0emZsd21naHBvamxzdGh5dXFmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc1NDQxOTAsImV4cCI6MjA3MzEyMDE5MH0.j5qMspjG6FTN69DPwI0otqjw7Yp5lbbFadflpkjNvYc")

def create_french_mood_embedding_text(movie):
    """Crée le texte d'embedding optimisé pour recherche mood française"""
    
    # Parties du texte d'embedding en français
    parts = []
    
    # 1. Titre et synopsis (base émotionnelle)
    title = movie.get('title', '')
    overview = movie.get('overview', '')
    
    if title:
        parts.append(title)
    if overview:
        parts.append(overview)
    
    # 2. Genres en français (crucial pour mood)
    genres = movie.get('genres', [])
    if genres:
        parts.extend(genres)
        # Ajout de variations mood
        genre_moods = {
            'Action': ['adrénaline', 'excitation', 'rythme soutenu'],
            'Aventure': ['découverte', 'exploration', 'voyage'],
            'Comédie': ['rire', 'divertissement', 'bonne humeur'],
            'Drame': ['émotion', 'réflexion', 'profondeur'],
            'Horreur': ['peur', 'tension', 'frissons'],
            'Romance': ['amour', 'sentiments', 'romantique'],
            'Science-Fiction': ['futuriste', 'technologie', 'innovation'],
            'Thriller': ['suspense', 'mystère', 'intrigue'],
            'Fantastique': ['magie', 'merveilleux', 'imaginaire'],
            'Animation': ['famille', 'enfants', 'divertissement'],
            'Documentaire': ['apprentissage', 'découverte', 'réalité'],
            'Guerre': ['conflit', 'héroïsme', 'histoire'],
            'Western': ['far west', 'aventure', 'cowboys'],
            'Crime': ['policier', 'enquête', 'justice'],
            'Mystère': ['énigme', 'investigation', 'suspense'],
            'Familial': ['famille', 'enfants', 'générations'],
            'Musique': ['rythme', 'mélodies', 'spectacle']
        }
        
        for genre in genres[:3]:  # Top 3 genres
            if genre in genre_moods:
                parts.extend(genre_moods[genre])
    
    # 3. Mots-clés émotionnels (si disponibles)
    keywords = movie.get('keywords', [])[:8]
    if keywords:
        parts.extend(keywords)
    
    # 4. Cast et réalisateur (ambiance du film)
    director = movie.get('director')
    if director:
        parts.append(f"réalisé par {director}")
        
        # Ajout du style du réalisateur connu
        director_styles = {
            'Christopher Nolan': ['complexe', 'mental', 'temporel'],
            'Quentin Tarantino': ['stylé', 'dialogue', 'violence'],
            'Steven Spielberg': ['spectacle', 'emotion', 'aventure'],
            'Tim Burton': ['dark', 'gothique', 'fantaisie'],
            'Wes Anderson': ['esthétique', 'symétrie', 'quirky'],
            'Martin Scorsese': ['intense', 'réalisme', 'crime']
        }
        
        for famous_director, style in director_styles.items():
            if famous_director.lower() in director.lower():
                parts.extend(style)
                break
    
    # 5. Acteurs principaux (pour l'ambiance)
    cast = movie.get('cast_names', [])[:4]
    for actor in cast:
        parts.append(f"avec {actor}")
    
    # 6. Indicateurs mood selon époque
    release_date = movie.get('release_date', '')
    if release_date and len(release_date) >= 4:
        try:
            year = int(release_date[:4])
            if year < 1960:
                parts.extend(['classique', 'vintage', 'ancien', 'noir et blanc'])
            elif year < 1980:
                parts.extend(['rétro', 'années 60-70', 'nostalgie'])
            elif year < 1990:
                parts.extend(['années 80', 'pop culture', 'synthwave'])
            elif year < 2000:
                parts.extend(['années 90', 'génération X', 'grunge'])
            elif year < 2010:
                parts.extend(['années 2000', 'numérique', 'moderne'])
            elif year < 2020:
                parts.extend(['années 2010', 'HD', 'contemporain'])
            else:
                parts.extend(['récent', 'actuel', 'moderne'])
        except:
            pass
    
    # 7. Niveau de qualité/popularité (mood impact)
    vote_avg = movie.get('vote_average', 0)
    popularity = movie.get('popularity', 0)
    
    if vote_avg >= 8.5:
        parts.extend(['chef d\'oeuvre', 'excellence', 'incontournable'])
    elif vote_avg >= 7.5:
        parts.extend(['très bon', 'recommandé', 'qualité'])
    elif vote_avg >= 6.5:
        parts.extend(['correct', 'divertissant'])
    
    if popularity > 100:
        parts.extend(['populaire', 'blockbuster', 'grand public'])
    elif popularity > 50:
        parts.extend(['connu', 'apprécié'])
    
    # 8. Runtime (mood impact)
    runtime = movie.get('runtime')
    if runtime:
        if runtime > 180:
            parts.extend(['épique', 'long métrage', 'immersif'])
        elif runtime < 90:
            parts.extend(['court', 'rapide', 'concis'])
    
    # 9. Tagline française si disponible
    tagline = movie.get('tagline', '')
    if tagline and len(tagline) < 100:
        parts.append(tagline)
    
    # 10. Plateformes streaming (disponibilité mood)
    streaming = movie.get('streaming_platforms', {})
    if isinstance(streaming, dict):
        platforms = streaming.get('streaming', [])
        if platforms:
            parts.append('disponible streaming')
            parts.extend([p.lower() for p in platforms[:3]])
    
    # Assemblage final avec déduplication
    unique_parts = []
    seen = set()
    for part in parts:
        if part and part.lower() not in seen:
            unique_parts.append(part)
            seen.add(part.lower())
    
    embedding_text = ' '.join(unique_parts[:100])  # Limite à 100 éléments
    return embedding_text

def generate_all_embeddings():
    """Génère tous les embeddings pour les films français"""
    
    # Connexion
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Chargement du modèle
    print("🤖 Chargement du modèle sentence-transformers...")
    model = SentenceTransformer('paraphrase-MiniLM-L3-v2')
    
    try:
        # Nettoyer les embeddings existants
        print("🗑️ Nettoyage des embeddings existants...")
        supabase.from_('movie_embeddings').delete().neq('id', 0).execute()
        
        # Récupérer tous les films
        print("📽️ Récupération des films...")
        movies_result = supabase.from_('movies').select('*').execute()
        movies = movies_result.data
        
        print(f"🎬 {len(movies)} films français trouvés")
        
        success_count = 0
        batch_size = 10
        
        for i in range(0, len(movies), batch_size):
            batch = movies[i:i+batch_size]
            
            print(f"\n📦 Batch {i//batch_size + 1}/{(len(movies)-1)//batch_size + 1}")
            
            batch_embeddings = []
            
            for movie in batch:
                try:
                    # Créer le texte d'embedding français optimisé mood
                    embedding_text = create_french_mood_embedding_text(movie)
                    
                    print(f"🎭 {movie.get('title', 'Unknown')}")
                    print(f"   Texte: {embedding_text[:150]}...")
                    
                    # Générer l'embedding
                    embedding = model.encode(embedding_text, normalize_embeddings=True)
                    
                    # Préparer pour insertion
                    embedding_data = {
                        'movie_id': movie['id'],
                        'embedding': embedding.tolist(),
                        'embedding_text': embedding_text
                    }
                    
                    batch_embeddings.append(embedding_data)
                    
                except Exception as e:
                    print(f"❌ Erreur film {movie.get('title', 'Unknown')}: {e}")
                    continue
            
            # Insertion par batch
            if batch_embeddings:
                try:
                    result = supabase.from_('movie_embeddings').insert(batch_embeddings).execute()
                    if result.data:
                        success_count += len(result.data)
                        print(f"✅ Batch sauvé: {len(result.data)} embeddings")
                    else:
                        print("❌ Erreur sauvegarde batch")
                except Exception as e:
                    print(f"❌ Erreur batch: {e}")
            
            # Pause entre les batchs
            time.sleep(1)
        
        print(f"\n🎉 Génération terminée!")
        print(f"📊 {success_count}/{len(movies)} embeddings créés")
        
        # Vérification finale
        final_count = supabase.from_('movie_embeddings').select('id', count='exact').execute()
        print(f"🔍 Vérification: {final_count.count} embeddings en base")
        
        return success_count
        
    except Exception as e:
        print(f"❌ Erreur globale: {e}")
        return 0

if __name__ == "__main__":
    print("🇫🇷 Génération des embeddings français optimisés mood...")
    generated = generate_all_embeddings()
    print(f"✨ Terminé! {generated} films prêts pour la recherche mood française 🎯")