import json
import time
from typing import List, Dict
from tmdb_client import TMDBClient
import pandas as pd

class MovieDataCollector:
    def __init__(self):
        self.tmdb = TMDBClient()
        self.collected_movies = []
    
    def collect_popular_movies(self, pages: int = 5) -> List[Dict]:
        """Collect popular movies from multiple pages"""
        movies = []
        
        for page in range(1, pages + 1):
            print(f"Collecting popular movies - Page {page}/{pages}")
            
            try:
                response = self.tmdb.get_popular_movies(page=page)
                page_movies = response.get("results", [])
                
                for movie in page_movies:
                    # Get detailed info for each movie to get genres
                    detailed_movie = self.tmdb.get_movie_details(movie["id"])
                    formatted_movie = self.tmdb.format_movie_data(detailed_movie)
                    movies.append(formatted_movie)
                    
                    # Rate limiting
                    time.sleep(0.1)
                
            except Exception as e:
                print(f"Error collecting page {page}: {e}")
                continue
        
        return movies
    
    def collect_top_rated_movies(self, pages: int = 3) -> List[Dict]:
        """Collect top rated movies"""
        movies = []
        
        for page in range(1, pages + 1):
            print(f"Collecting top rated movies - Page {page}/{pages}")
            
            try:
                response = self.tmdb.get_top_rated_movies(page=page)
                page_movies = response.get("results", [])
                
                for movie in page_movies:
                    detailed_movie = self.tmdb.get_movie_details(movie["id"])
                    formatted_movie = self.tmdb.format_movie_data(detailed_movie)
                    movies.append(formatted_movie)
                    
                    time.sleep(0.1)
                
            except Exception as e:
                print(f"Error collecting page {page}: {e}")
                continue
        
        return movies
    
    def collect_movies_by_genres(self, genre_ids: List[int], pages_per_genre: int = 2) -> List[Dict]:
        """Collect movies by specific genres"""
        movies = []
        
        for genre_id in genre_ids:
            print(f"Collecting movies for genre ID: {genre_id}")
            
            for page in range(1, pages_per_genre + 1):
                try:
                    response = self.tmdb.get_movies_by_genre(genre_id, page=page)
                    page_movies = response.get("results", [])
                    
                    for movie in page_movies:
                        detailed_movie = self.tmdb.get_movie_details(movie["id"])
                        formatted_movie = self.tmdb.format_movie_data(detailed_movie)
                        movies.append(formatted_movie)
                        
                        time.sleep(0.1)
                    
                except Exception as e:
                    print(f"Error collecting genre {genre_id}, page {page}: {e}")
                    continue
        
        return movies
    
    def collect_comprehensive_dataset(self) -> List[Dict]:
        """Collect a comprehensive dataset of movies"""
        all_movies = []
        movie_ids = set()
        
        # Popular movies
        popular_movies = self.collect_popular_movies(pages=5)
        for movie in popular_movies:
            if movie["id"] not in movie_ids:
                all_movies.append(movie)
                movie_ids.add(movie["id"])
        
        # Top rated movies
        top_rated_movies = self.collect_top_rated_movies(pages=3)
        for movie in top_rated_movies:
            if movie["id"] not in movie_ids:
                all_movies.append(movie)
                movie_ids.add(movie["id"])
        
        # Movies by genre (focusing on diverse genres for mood variety)
        genre_ids = [
            28,  # Action
            12,  # Adventure
            16,  # Animation
            35,  # Comedy
            80,  # Crime
            18,  # Drama
            14,  # Fantasy
            27,  # Horror
            10402,  # Music
            9648,  # Mystery
            10749,  # Romance
            878,  # Science Fiction
            53,  # Thriller
            10752,  # War
            37   # Western
        ]
        
        genre_movies = self.collect_movies_by_genres(genre_ids, pages_per_genre=2)
        for movie in genre_movies:
            if movie["id"] not in movie_ids:
                all_movies.append(movie)
                movie_ids.add(movie["id"])
        
        print(f"Collected {len(all_movies)} unique movies")
        return all_movies
    
    def save_to_json(self, movies: List[Dict], filename: str = "movies_dataset.json"):
        """Save movies to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(movies, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(movies)} movies to {filename}")
    
    def save_to_csv(self, movies: List[Dict], filename: str = "movies_dataset.csv"):
        """Save movies to CSV file"""
        df = pd.DataFrame(movies)
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"Saved {len(movies)} movies to {filename}")

if __name__ == "__main__":
    collector = MovieDataCollector()
    
    print("Starting movie data collection...")
    movies = collector.collect_comprehensive_dataset()
    
    # Save in both formats
    collector.save_to_json(movies)
    collector.save_to_csv(movies)
    
    print("Data collection completed!")