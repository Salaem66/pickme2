#!/usr/bin/env python3
"""
VibeFilms - Serveur FastAPI pour Railway
Moteur de recherche de films par mood avec Supabase
"""

import os
from fastapi import FastAPI, HTTPException, Query, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
import uvicorn

# Imports pour le moteur de recherche
from supabase import create_client, Client
from sentence_transformers import SentenceTransformer
import numpy as np
import logging

# Import du système d'auth simple
from simple_auth import simple_auth, get_current_user, get_current_user_optional

# Import du système de mapping émotionnel
from emotion_mapper import emotion_mapper

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

# ==================== ENDPOINTS D'AUTHENTIFICATION ====================

@app.post("/api/auth/register")
async def register(request: Request):
    """Inscription utilisateur"""
    try:
        data = await request.json()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        name = data.get('name', '').strip()
        
        if not email or not password or not name:
            raise HTTPException(status_code=400, detail="Email, mot de passe et nom requis")
        
        result = await simple_auth.register_user(email, password, name)
        return JSONResponse(result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur inscription: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de l'inscription")

@app.post("/api/auth/login")
async def login(request: Request):
    """Connexion utilisateur"""
    try:
        data = await request.json()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        
        if not email or not password:
            raise HTTPException(status_code=400, detail="Email et mot de passe requis")
        
        result = await simple_auth.login_user(email, password)
        return JSONResponse(result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur connexion: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la connexion")

@app.get("/api/auth/me")
async def get_user_info(current_user: dict = Depends(get_current_user)):
    """Récupérer les informations de l'utilisateur connecté"""
    return JSONResponse({
        "user": {
            "id": current_user['id'],
            "email": current_user['email'],
            "name": current_user['name'],
            "subscription_type": current_user.get('subscription_type', 'free'),
            "preferences": current_user.get('preferences', {})
        }
    })

# Note: Endpoints de préférences et watchlist à ajouter plus tard

# ==================== EVENTS ET CONFIGURATION ====================

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

# PWA Routes
@app.get("/manifest.json")
async def manifest():
    """PWA Manifest"""
    with open("static/manifest.json", "r", encoding="utf-8") as f:
        import json
        content = json.loads(f.read())
        return JSONResponse(
            content=content,
            headers={"Content-Type": "application/manifest+json"}
        )

@app.get("/sw.js")
async def service_worker():
    """PWA Service Worker"""
    with open("static/sw.js", "r", encoding="utf-8") as f:
        return Response(
            content=f.read(),
            media_type="application/javascript"
        )

@app.get("/pickme_logo.png")
async def app_icon():
    """App Icon for PWA"""
    with open("static/pickme_logo.png", "rb") as f:
        return Response(
            content=f.read(),
            media_type="image/png"
        )

@app.get("/test-auth", response_class=HTMLResponse)
async def test_auth_interface():
    """Page de test Google OAuth"""
    with open("test_google_oauth.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.get("/api/search")
async def search_movies(
    q: str = Query(..., description="Requête de recherche"),
    limit: int = Query(10, ge=1, le=50, description="Nombre de résultats"),
    platforms: Optional[str] = Query(None, description="Plateformes de streaming (séparées par virgule)"),
    genres: Optional[str] = Query(None, description="Genres (séparés par virgule)"),
    threshold: float = Query(0.1, ge=0.0, le=1.0, description="Seuil de similarité"),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Recherche de films par similarité sémantique
    """
    try:
        logger.info(f"🔍 Recherche: '{q}' (limit: {limit})")
        
        # Détection et amélioration émotionnelle
        enhanced_query = emotion_mapper.enhance_query(q)
        genre_boosts = emotion_mapper.get_genre_boosts(q)
        
        if enhanced_query != q:
            logger.info(f"✨ Requête améliorée: '{enhanced_query}'")
        if genre_boosts:
            logger.info(f"🎭 Boost genres: {genre_boosts}")
        
        # Génération de l'embedding avec la requête améliorée
        query_embedding = generate_embedding(enhanced_query)
        
        # Traitement des filtres
        platform_list = [p.strip() for p in platforms.split(',')] if platforms else None
        genre_list = [g.strip() for g in genres.split(',')] if genres else None
        
        # Debug logging
        if platform_list:
            logger.info(f"🎬 Filtrage plateformes: {platform_list}")
        
        # Appel à la fonction Supabase avec filtrage plateforme intégré
        result = supabase.rpc('match_movies', {
            'query_embedding': query_embedding,
            'match_threshold': threshold,
            'match_count': limit,
            'filter_genres': genre_list,
            'filter_platforms': platform_list
        }).execute()

        # AJOUT SPÉCIAL : Si recherche "peur" avec boost Horreur >= 7.0, forcer l'ajout des films d'horreur populaires
        if genre_boosts and 'Horreur' in genre_boosts and genre_boosts['Horreur'] >= 7.0:
            logger.info(f"🔥 RECHERCHE PEUR DÉTECTÉE - Injection FORCÉE des films d'horreur populaires")

            # Requête pour récupérer les films d'horreur populaires (vote_average >= 6.5)
            horror_query = supabase.from_('movies').select('*').contains('genres', ['Horreur']).gte('vote_average', 6.5).order('vote_average', desc=True).limit(15).execute()

            if horror_query.data:
                # TOUJOURS ajouter les films d'horreur - même s'ils existent déjà
                if not result.data:
                    result.data = []

                # Ajouter TOUS les films d'horreur populaires avec boost
                for horror_movie in horror_query.data:
                    horror_movie['similarity'] = 0.9  # Similarité très élevée pour être en tête
                    horror_movie['forced_injection'] = True  # Marquer comme injecté
                    result.data.append(horror_movie)
                    logger.info(f"💉 INJECTION FORCÉE: {horror_movie.get('title')} ({horror_movie.get('vote_average')})")

                logger.info(f"🎬 {len(result.data)} films au total après injection FORCÉE des horreurs populaires")
        
        if not result.data:
            return JSONResponse({
                "query": q,
                "results": [],
                "count": 0,
                "message": "Aucun film trouvé pour cette recherche"
            })
        
        movies = result.data
        
        # Application des boost émotionnels - BOOST AGRESSIF POUR HORREUR
        if genre_boosts and movies:
            for movie in movies:
                movie_genres = movie.get('genre_names', [])
                emotion_boost = 1.0

                # Calculer le boost maximal pour ce film
                for genre in movie_genres:
                    if genre in genre_boosts:
                        emotion_boost = max(emotion_boost, genre_boosts[genre])

                # Appliquer le boost au score de similarité
                if emotion_boost > 1.0:
                    original_similarity = movie.get('similarity', 0)

                    # BOOST SPÉCIAL HORREUR : Si c'est un film d'horreur populaire et recherche "peur"
                    if 'Horreur' in movie_genres and emotion_boost >= 7.0:
                        # Films d'horreur populaires : boost additif massif
                        if movie.get('vote_average', 0) >= 6.5:
                            boosted_similarity = min(1.0, original_similarity + 0.8)  # Boost additif énorme
                            logger.info(f"🔥 BOOST HORREUR POPULAIRE: {movie.get('title')} ({movie.get('vote_average')}) -> {boosted_similarity}")
                        else:
                            boosted_similarity = min(1.0, original_similarity + 0.4)  # Boost additif modéré
                    else:
                        # Boost multiplicatif classique pour les autres genres
                        boosted_similarity = min(1.0, original_similarity * emotion_boost)

                    movie['similarity'] = boosted_similarity
                    movie['emotion_boost'] = emotion_boost

            # Retrier par similarité après boost
            movies.sort(key=lambda x: x.get('similarity', 0), reverse=True)
            logger.info(f"🎭 Boost émotionnel appliqué aux genres")
        
        logger.info(f"✅ Trouvé {len(movies)} films")
        
        # Note: Tracking des recherches à ajouter plus tard avec les tables custom
        
        return JSONResponse({
            "query": q,
            "enhanced_query": enhanced_query if enhanced_query != q else None,
            "detected_emotions": genre_boosts if genre_boosts else None,
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
        platforms = [p.strip() for p in data.get('platforms', [])] if data.get('platforms') else None
        genres = [g.strip() for g in data.get('genres', [])] if data.get('genres') else None
        threshold = data.get('threshold', 0.1)
        
        logger.info(f"🔍 Recherche POST: '{query}'")
        
        # Détection et amélioration émotionnelle
        enhanced_query = emotion_mapper.enhance_query(query)
        genre_boosts = emotion_mapper.get_genre_boosts(query)
        
        if enhanced_query != query:
            logger.info(f"✨ Requête améliorée: '{enhanced_query}'")
        if genre_boosts:
            logger.info(f"🎭 Boost genres: {genre_boosts}")
        
        # Génération de l'embedding avec la requête améliorée
        query_embedding = generate_embedding(enhanced_query)
        
        # Appel à la fonction Supabase avec filtrage plateforme intégré
        result = supabase.rpc('match_movies', {
            'query_embedding': query_embedding,
            'match_threshold': threshold,
            'match_count': limit,
            'filter_genres': genres if genres else None,
            'filter_platforms': platforms if platforms else None
        }).execute()

        # AJOUT SPÉCIAL : Si recherche "peur" avec boost Horreur >= 7.0, forcer l'ajout des films d'horreur populaires
        if genre_boosts and 'Horreur' in genre_boosts and genre_boosts['Horreur'] >= 7.0:
            logger.info(f"🔥 RECHERCHE PEUR DÉTECTÉE (POST) - Injection FORCÉE des films d'horreur populaires")

            # Requête pour récupérer les films d'horreur populaires (vote_average >= 6.5)
            horror_query = supabase.from_('movies').select('*').contains('genres', ['Horreur']).gte('vote_average', 6.5).order('vote_average', desc=True).limit(15).execute()

            if horror_query.data:
                # TOUJOURS ajouter les films d'horreur - même s'ils existent déjà
                if not result.data:
                    result.data = []

                # Ajouter TOUS les films d'horreur populaires avec boost
                for horror_movie in horror_query.data:
                    horror_movie['similarity'] = 0.9  # Similarité très élevée pour être en tête
                    horror_movie['forced_injection'] = True  # Marquer comme injecté
                    result.data.append(horror_movie)
                    logger.info(f"💉 INJECTION FORCÉE: {horror_movie.get('title')} ({horror_movie.get('vote_average')})")

                logger.info(f"🎬 {len(result.data)} films au total après injection FORCÉE des horreurs populaires (POST)")
        
        if not result.data:
            return JSONResponse({
                "query": query,
                "results": [],
                "count": 0
            })
        
        movies = result.data
        
        # Application des boost émotionnels - BOOST AGRESSIF POUR HORREUR
        if genre_boosts and movies:
            for movie in movies:
                movie_genres = movie.get('genre_names', [])
                emotion_boost = 1.0

                # Calculer le boost maximal pour ce film
                for genre in movie_genres:
                    if genre in genre_boosts:
                        emotion_boost = max(emotion_boost, genre_boosts[genre])

                # Appliquer le boost au score de similarité
                if emotion_boost > 1.0:
                    original_similarity = movie.get('similarity', 0)

                    # BOOST SPÉCIAL HORREUR : Si c'est un film d'horreur populaire et recherche "peur"
                    if 'Horreur' in movie_genres and emotion_boost >= 7.0:
                        # Films d'horreur populaires : boost additif massif
                        if movie.get('vote_average', 0) >= 6.5:
                            boosted_similarity = min(1.0, original_similarity + 0.8)  # Boost additif énorme
                            logger.info(f"🔥 BOOST HORREUR POPULAIRE: {movie.get('title')} ({movie.get('vote_average')}) -> {boosted_similarity}")
                        else:
                            boosted_similarity = min(1.0, original_similarity + 0.4)  # Boost additif modéré
                    else:
                        # Boost multiplicatif classique pour les autres genres
                        boosted_similarity = min(1.0, original_similarity * emotion_boost)

                    movie['similarity'] = boosted_similarity
                    movie['emotion_boost'] = emotion_boost

            # Retrier par similarité après boost
            movies.sort(key=lambda x: x.get('similarity', 0), reverse=True)
            logger.info(f"🎭 Boost émotionnel appliqué aux genres (POST)")
        
        return JSONResponse({
            "query": query,
            "enhanced_query": enhanced_query if enhanced_query != query else None,
            "detected_emotions": genre_boosts if genre_boosts else None,
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