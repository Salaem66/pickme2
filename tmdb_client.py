import requests
import os
from dotenv import load_dotenv
from typing import List, Dict, Optional

load_dotenv()

class TMDBClient:
    def __init__(self):
        self.api_key = os.getenv("TMDB_API_KEY")
        self.base_url = os.getenv("TMDB_BASE_URL")
        
        if not self.api_key:
            raise ValueError("TMDB_API_KEY not found in environment variables")
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make a request to TMDB API"""
        if params is None:
            params = {}
        
        params["api_key"] = self.api_key
        url = f"{self.base_url}/{endpoint}"
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        return response.json()
    
    def get_popular_movies(self, page: int = 1) -> Dict:
        """Get popular movies"""
        return self._make_request("movie/popular", {"page": page})
    
    def get_top_rated_movies(self, page: int = 1) -> Dict:
        """Get top rated movies"""
        return self._make_request("movie/top_rated", {"page": page})
    
    def get_movie_details(self, movie_id: int) -> Dict:
        """Get detailed information about a specific movie"""
        return self._make_request(f"movie/{movie_id}")
    
    def search_movies(self, query: str, page: int = 1) -> Dict:
        """Search movies by query"""
        return self._make_request("search/movie", {"query": query, "page": page})
    
    def get_movies_by_genre(self, genre_id: int, page: int = 1) -> Dict:
        """Get movies by genre"""
        return self._make_request("discover/movie", {
            "with_genres": genre_id,
            "page": page,
            "sort_by": "popularity.desc"
        })
    
    def get_watch_providers(self, movie_id: int) -> Dict:
        """Get watch providers for a specific movie"""
        try:
            return self._make_request(f"movie/{movie_id}/watch/providers")
        except Exception as e:
            print(f"Erreur lors de la récupération des plateformes pour le film {movie_id}: {e}")
            return {}
    
    def get_genres(self) -> Dict:
        """Get all movie genres"""
        return self._make_request("genre/movie/list")
    
    def format_movie_data(self, movie_data: Dict) -> Dict:
        """Format movie data for our application"""
        return {
            "id": movie_data.get("id"),
            "title": movie_data.get("title"),
            "overview": movie_data.get("overview", ""),
            "release_date": movie_data.get("release_date", ""),
            "vote_average": movie_data.get("vote_average", 0),
            "poster_path": f"https://image.tmdb.org/t/p/w500{movie_data.get('poster_path')}" if movie_data.get('poster_path') else None,
            "genres": [genre.get("name") for genre in movie_data.get("genres", [])] if "genres" in movie_data else [],
            "popularity": movie_data.get("popularity", 0)
        }