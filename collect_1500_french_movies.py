#!/usr/bin/env python3
"""
Collection de 1500 films populaires avec métadonnées françaises
pour la recherche par mood/humeur
"""

import requests
import time
import json
import os
from datetime import datetime
from supabase import create_client

# Configuration
TMDB_API_KEY = "6ef7318d02f41956a25c992eb066a580"
TMDB_BASE_URL = "https://api.themoviedb.org/3"

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://utzflwmghpojlsthyuqf.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV0emZsd21naHBvamxzdGh5dXFmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc1NDQxOTAsImV4cCI6MjA3MzEyMDE5MH0.j5qMspjG6FTN69DPwI0otqjw7Yp5lbbFadflpkjNvYc")

class FrenchMovieCollector:
    def __init__(self):
        self.session = requests.Session()
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.collected_movies = []
        
    def get_popular_movies(self, pages=75):  # 75 pages × 20 films = 1500 films
        """Récupère les films populaires avec métadonnées françaises"""
        movies = []
        
        for page in range(1, pages + 1):
            print(f"📄 Page {page}/{pages}")
            
            try:
                # Films populaires avec région France
                url = f"{TMDB_BASE_URL}/movie/popular"
                params = {
                    'api_key': TMDB_API_KEY,
                    'language': 'fr-FR',  # Métadonnées en français
                    'region': 'FR',       # Région française
                    'page': page
                }
                
                response = self.session.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                for movie_basic in data['results']:
                    # Récupérer les détails complets + streaming
                    movie_details = self.get_movie_details(movie_basic['id'])
                    if movie_details:
                        movies.append(movie_details)
                        print(f"✅ {movie_details['title']} ({movie_details.get('release_date', 'N/A')})")
                
                # Pause pour éviter rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Erreur page {page}: {e}")
                continue
                
        return movies
    
    def get_movie_details(self, movie_id):
        """Récupère tous les détails d'un film en français"""
        try:
            # Détails complets du film
            details_url = f"{TMDB_BASE_URL}/movie/{movie_id}"
            details_params = {
                'api_key': TMDB_API_KEY,
                'language': 'fr-FR',
                'append_to_response': 'keywords,credits,watch/providers'
            }
            
            response = self.session.get(details_url, params=details_params)
            response.raise_for_status()
            movie = response.json()
            
            # Skip films pour adultes ou sans synopsis français
            if movie.get('adult') or not movie.get('overview'):
                return None
                
            # Extraction des plateformes streaming (France)
            streaming_data = {}
            watch_providers = movie.get('watch/providers', {}).get('results', {}).get('FR', {})
            
            if watch_providers:
                streaming_data = {
                    'streaming': [p['provider_name'] for p in watch_providers.get('flatrate', [])],
                    'rent': [p['provider_name'] for p in watch_providers.get('rent', [])],
                    'buy': [p['provider_name'] for p in watch_providers.get('buy', [])]
                }
            
            # Extraction des mots-clés (pour le mood)
            keywords_fr = []
            if 'keywords' in movie and movie['keywords'].get('keywords'):
                keywords_fr = [kw['name'] for kw in movie['keywords']['keywords'][:10]]
            
            # Cast principal (pour l'ambiance du film)
            main_cast = []
            director = None
            if 'credits' in movie:
                # Acteurs principaux
                cast = movie['credits'].get('cast', [])[:8]
                main_cast = [actor['name'] for actor in cast]
                
                # Réalisateur
                crew = movie['credits'].get('crew', [])
                directors = [person['name'] for person in crew if person['job'] == 'Director']
                director = directors[0] if directors else None
            
            # Construction des données mood-optimisées
            movie_data = {
                'tmdb_id': movie['id'],
                'title': movie.get('title', ''),
                'overview': movie.get('overview', ''),
                'genres': [g['name'] for g in movie.get('genres', [])],
                'release_date': movie.get('release_date'),
                'vote_average': movie.get('vote_average', 0),
                'vote_count': movie.get('vote_count', 0),
                'popularity': movie.get('popularity', 0),
                'poster_path': movie.get('poster_path'),
                'backdrop_path': movie.get('backdrop_path'),
                'original_language': movie.get('original_language'),
                'runtime': movie.get('runtime'),
                'budget': movie.get('budget', 0),
                'revenue': movie.get('revenue', 0),
                'tagline': movie.get('tagline', ''),
                'homepage': movie.get('homepage'),
                'imdb_id': movie.get('imdb_id'),
                'status': movie.get('status'),
                
                # Données mood-spécifiques
                'keywords': keywords_fr,
                'cast_names': main_cast,
                'director': director,
                'streaming_platforms': streaming_data,
                
                # Métadonnées techniques
                'production_countries': [c['name'] for c in movie.get('production_countries', [])],
                'spoken_languages': [l['name'] for l in movie.get('spoken_languages', [])]
            }
            
            return movie_data
            
        except Exception as e:
            print(f"❌ Erreur film {movie_id}: {e}")
            return None
    
    def create_mood_embedding_text(self, movie):
        """Crée le texte optimisé pour les recherches par mood/humeur"""
        
        # Parties du texte d'embedding
        parts = []
        
        # 1. Titre et synopsis (base)
        parts.append(movie.get('title', ''))
        parts.append(movie.get('overview', ''))
        
        # 2. Genres (très important pour mood)
        genres = movie.get('genres', [])
        if genres:
            parts.extend(genres)
            parts.append(f"film de {' et '.join(genres[:2])}")
        
        # 3. Mots-clés (mood/thèmes)
        keywords = movie.get('keywords', [])[:8]  
        if keywords:
            parts.extend(keywords)
        
        # 4. Ambiance selon cast/réalisateur
        director = movie.get('director')
        if director:
            parts.append(f"réalisé par {director}")
            
        cast = movie.get('cast_names', [])[:4]  # Top 4 acteurs
        if cast:
            parts.extend([f"avec {actor}" for actor in cast])
        
        # 5. Indicateurs de mood selon note/popularité
        vote_avg = movie.get('vote_average', 0)
        if vote_avg > 8.0:
            parts.append("film acclamé excellent")
        elif vote_avg > 7.0:
            parts.append("film apprécié qualité")
        
        # 6. Époque/ambiance temporelle
        release_year = movie.get('release_date', '')[:4] if movie.get('release_date') else ''
        if release_year:
            try:
                year = int(release_year)
                if year < 1980:
                    parts.append("film classique vintage rétro")
                elif year < 2000:
                    parts.append("film années 80 90 nostalgie")
                elif year < 2010:
                    parts.append("film années 2000")
                else:
                    parts.append("film récent moderne")
            except:
                pass
        
        # 7. Tagline si pertinente
        tagline = movie.get('tagline', '')
        if tagline and len(tagline) < 100:
            parts.append(tagline)
        
        # Assemblage final
        embedding_text = ' '.join(filter(None, parts))
        return embedding_text
    
    def save_to_supabase(self, movies):
        """Sauvegarde les films dans Supabase"""
        print(f"\n💾 Sauvegarde de {len(movies)} films dans Supabase...")
        
        # Clear existing data
        print("🗑️ Nettoyage des données existantes...")
        self.supabase.from_('movie_embeddings').delete().neq('id', 0).execute()
        self.supabase.from_('movies').delete().neq('id', 0).execute()
        
        success_count = 0
        
        for i, movie in enumerate(movies, 1):
            try:
                # Insérer le film
                movie_result = self.supabase.from_('movies').insert(movie).execute()
                
                if movie_result.data:
                    print(f"✅ {i}/{len(movies)}: {movie['title']}")
                    success_count += 1
                else:
                    print(f"❌ {i}/{len(movies)}: Erreur insertion {movie['title']}")
                    
            except Exception as e:
                print(f"❌ {i}/{len(movies)}: Erreur {movie['title']} - {e}")
                continue
        
        print(f"\n🎉 {success_count}/{len(movies)} films sauvegardés !")
        return success_count

def main():
    collector = FrenchMovieCollector()
    
    print("🎬 Collection de 1500 films français pour recherche par mood...")
    print("🇫🇷 Métadonnées en français + plateformes streaming")
    
    # Collection des films
    movies = collector.get_popular_movies(pages=75)
    
    if not movies:
        print("❌ Aucun film collecté")
        return
    
    print(f"\n📊 {len(movies)} films collectés")
    
    # Sauvegarde dans Supabase
    saved_count = collector.save_to_supabase(movies)
    
    # Sauvegarde locale en backup
    backup_file = f"movies_french_1500_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(movies, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Backup sauvegardé: {backup_file}")
    print(f"🎯 Prêt pour recherche par mood avec {saved_count} films français !")

if __name__ == "__main__":
    main()