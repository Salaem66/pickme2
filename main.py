#!/usr/bin/env python3
"""
VibeFilms - Serveur FastAPI pour Railway
Moteur de recherche de films par mood avec Supabase
"""

import os
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from typing import List, Optional
import uvicorn

# Imports pour le moteur de recherche
from supabase import create_client, Client
from sentence_transformers import SentenceTransformer
import numpy as np
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration - Variables d'environnement
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://utzflwmghpojlsthyuqf.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV0emZsd21naHBvamxzdGh5dXFmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc1NDQxOTAsImV4cCI6MjA3MzEyMDE5MH0.j5qMspjG6FTN69DPwI0otqjw7Yp5lbbFadflpkjNvYc")

# Variables globales - chargées au démarrage du serveur
supabase: Client = None
model: SentenceTransformer = None

# Initialisation FastAPI
app = FastAPI(
    title="VibeFilms API",
    description="Moteur de recherche de films par mood",
    version="2.0.0"
)

# Servir les fichiers statiques
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def startup_event():
    """Initialisation au démarrage du serveur - une seule fois"""
    global supabase, model
    
    try:
        logger.info("🚀 Initialisation VibeFilms...")
        
        # Connexion Supabase
        logger.info("📡 Connexion à Supabase...")
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Chargement du modèle ML (une seule fois!)
        logger.info("🤖 Chargement du modèle sentence-transformers (384D)...")
        model = SentenceTransformer('paraphrase-MiniLM-L3-v2')  # 384 dimensions, optimisé
        
        logger.info("✅ VibeFilms prêt!")
        
    except Exception as e:
        logger.error(f"❌ Erreur d'initialisation: {e}")
        raise

def generate_embedding(text: str) -> List[float]:
    """Génère un embedding avec le modèle chargé en mémoire"""
    try:
        embedding = model.encode(text, normalize_embeddings=True)
        return embedding.tolist()
    except Exception as e:
        logger.error(f"Erreur génération embedding: {e}")
        # Embedding par défaut si erreur
        return [0.0] * 384

@app.get("/", response_class=HTMLResponse)
async def root():
    """Page d'accueil - interface tech"""
    with open("static/tech.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.get("/modern", response_class=HTMLResponse)
async def modern_interface():
    """Interface moderne"""
    with open("static/modern.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.get("/classic", response_class=HTMLResponse)
async def classic_interface():
    """Interface classique"""
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.get("/tinder", response_class=HTMLResponse)
async def tinder_interface():
    """Interface style Tinder"""
    with open("static/tinder.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.get("/api/search")
async def search_movies(
    q: str = Query(..., description="Requête de recherche"),
    limit: int = Query(10, ge=1, le=50, description="Nombre de résultats"),
    platforms: Optional[str] = Query(None, description="Plateformes de streaming (séparées par virgule)"),
    genres: Optional[str] = Query(None, description="Genres (séparés par virgule)"),
    threshold: float = Query(0.6, ge=0.0, le=1.0, description="Seuil de similarité")
):
    """
    Recherche de films par similarité sémantique
    """
    try:
        logger.info(f"🔍 Recherche: '{q}' (limit: {limit})")
        
        # Génération de l'embedding
        query_embedding = generate_embedding(q)
        
        # Traitement des filtres
        platform_list = platforms.split(',') if platforms else None
        genre_list = genres.split(',') if genres else None
        
        # Appel à la fonction Supabase
        result = supabase.rpc('match_movies', {
            'query_embedding': query_embedding,
            'match_threshold': threshold,
            'match_count': limit,
            'filter_genres': genre_list
        }).execute()
        
        if not result.data:
            return JSONResponse({
                "query": q,
                "results": [],
                "count": 0,
                "message": "Aucun film trouvé pour cette recherche"
            })
        
        movies = result.data
        
        # Filtrage par plateforme si demandé
        if platform_list:
            filtered_movies = []
            for movie in movies:
                streaming_platforms = movie.get('streaming_platforms', {})
                if isinstance(streaming_platforms, dict):
                    available_platforms = streaming_platforms.get('streaming', [])
                    if any(platform.lower().strip() in [p.lower() for p in available_platforms] 
                          for platform in platform_list):
                        filtered_movies.append(movie)
            movies = filtered_movies
        
        logger.info(f"✅ Trouvé {len(movies)} films")
        
        return JSONResponse({
            "query": q,
            "results": movies[:limit],
            "count": len(movies),
            "filters": {
                "platforms": platform_list,
                "genres": genre_list,
                "threshold": threshold
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Erreur recherche: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")

@app.post("/api/search")
async def search_movies_post(request: Request):
    """
    Recherche de films (POST) - pour requêtes complexes
    """
    try:
        data = await request.json()
        
        query = data.get('query', '').strip()
        if not query:
            raise HTTPException(status_code=400, detail="Champ 'query' requis")
        
        limit = data.get('limit', 10)
        platforms = data.get('platforms', [])
        genres = data.get('genres', [])
        threshold = data.get('threshold', 0.6)
        
        logger.info(f"🔍 Recherche POST: '{query}'")
        
        # Génération de l'embedding
        query_embedding = generate_embedding(query)
        
        # Appel à la fonction Supabase
        result = supabase.rpc('match_movies', {
            'query_embedding': query_embedding,
            'match_threshold': threshold,
            'match_count': limit,
            'filter_genres': genres if genres else None
        }).execute()
        
        if not result.data:
            return JSONResponse({
                "query": query,
                "results": [],
                "count": 0
            })
        
        movies = result.data
        
        # Filtrage par plateforme si demandé
        if platforms:
            filtered_movies = []
            for movie in movies:
                streaming_platforms = movie.get('streaming_platforms', {})
                if isinstance(streaming_platforms, dict):
                    available_platforms = streaming_platforms.get('streaming', [])
                    if any(platform.lower() in [p.lower() for p in available_platforms] 
                          for platform in platforms):
                        filtered_movies.append(movie)
            movies = filtered_movies
        
        return JSONResponse({
            "query": query,
            "results": movies[:limit],
            "count": len(movies),
            "filters": {
                "platforms": platforms,
                "genres": genres,
                "threshold": threshold
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Erreur recherche POST: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")

@app.get("/api/health")
async def health_check():
    """Vérification de santé du service"""
    try:
        # Test de la connexion Supabase
        result = supabase.from_('movies').select('id').limit(1).execute()
        
        return JSONResponse({
            "status": "healthy",
            "database": "connected",
            "model": "loaded" if model else "error",
            "message": "VibeFilms API opérationnelle"
        })
    except Exception as e:
        return JSONResponse({
            "status": "unhealthy",
            "error": str(e)
        }, status_code=503)

if __name__ == "__main__":
    # Configuration pour Railway
    port = int(os.environ.get("PORT", 8000))
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Pas de reload en production
        log_level="info"
    )