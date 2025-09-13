#!/usr/bin/env python3
"""
Système d'auth simple utilisant Supabase Auth builtin
"""

from fastapi import HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
from supabase import create_client
import logging
from typing import Optional, Dict, Any

# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://utzflwmghpojlsthyuqf.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV0emZsd21naHBvamxzdGh5dXFmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc1NDQxOTAsImV4cCI6MjA3MzEyMDE5MH0.j5qMspjG6FTN69DPwI0otqjw7Yp5lbbFadflpkjNvYc")

# Mode développement pour bypass confirmation email
DEV_MODE = os.getenv("DEV_MODE", "true").lower() == "true"

security = HTTPBearer()
logger = logging.getLogger(__name__)

class SimpleAuthSystem:
    def __init__(self):
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    async def register_user(self, email: str, password: str, name: str) -> Dict[str, Any]:
        """Inscription avec Supabase Auth"""
        try:
            # Créer utilisateur avec Supabase Auth
            auth_response = self.supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "name": name,
                        "subscription_type": "free"
                    }
                }
            })
            
            if auth_response.user:
                # Si pas de session (email non confirmé), essayer de connecter immédiatement
                session_token = None
                if auth_response.session:
                    session_token = auth_response.session.access_token
                else:
                    logger.info(f"Pas de session immédiate pour {email}, tentative de connexion...")
                    try:
                        # Tenter une connexion immédiate (certaines configurations Supabase permettent cela)
                        login_response = self.supabase.auth.sign_in_with_password({
                            "email": email,
                            "password": password
                        })
                        if login_response.session:
                            session_token = login_response.session.access_token
                            logger.info(f"Connexion automatique réussie pour {email}")
                    except Exception as e:
                        logger.info(f"Connexion automatique échouée pour {email}: {e}")
                        # Pas grave, l'utilisateur devra se connecter manuellement
                
                return {
                    "message": "Compte créé avec succès" + (" et connecté automatiquement" if session_token else ""),
                    "user": {
                        "id": auth_response.user.id,
                        "email": auth_response.user.email,
                        "name": name
                    },
                    "token": session_token,
                    "needs_confirmation": session_token is None
                }
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Erreur lors de la création du compte"
                )
                
        except Exception as e:
            logger.error(f"Erreur inscription: {e}")
            raise HTTPException(
                status_code=400,
                detail=str(e)
            )
    
    async def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """Connexion avec Supabase Auth"""
        try:
            auth_response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if auth_response.user and auth_response.session:
                return {
                    "message": "Connexion réussie",
                    "user": {
                        "id": auth_response.user.id,
                        "email": auth_response.user.email,
                        "name": auth_response.user.user_metadata.get("name", "Utilisateur")
                    },
                    "token": auth_response.session.access_token
                }
            else:
                raise HTTPException(
                    status_code=401,
                    detail="Email ou mot de passe incorrect"
                )
                
        except Exception as e:
            logger.error(f"Erreur connexion: {e}")
            raise HTTPException(
                status_code=401,
                detail="Email ou mot de passe incorrect"
            )
    
    async def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
        """Récupérer utilisateur à partir du token"""
        try:
            token = credentials.credentials
            
            # Vérifier le token avec Supabase
            user_response = self.supabase.auth.get_user(token)
            
            if user_response.user:
                return {
                    "id": user_response.user.id,
                    "email": user_response.user.email,
                    "name": user_response.user.user_metadata.get("name", "Utilisateur"),
                    "subscription_type": user_response.user.user_metadata.get("subscription_type", "free")
                }
            else:
                raise HTTPException(
                    status_code=401,
                    detail="Token invalide"
                )
                
        except Exception as e:
            logger.error(f"Erreur auth: {e}")
            raise HTTPException(
                status_code=401,
                detail="Token invalide"
            )

# Instance globale
simple_auth = SimpleAuthSystem()

# Dependencies pour FastAPI
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Dependency pour récupérer l'utilisateur courant"""
    return await simple_auth.get_current_user(credentials)

async def get_current_user_optional(request: Request) -> Optional[dict]:
    """Dependency optionnelle pour récupérer l'utilisateur si connecté"""
    try:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer "
            user_response = simple_auth.supabase.auth.get_user(token)
            if user_response.user:
                return {
                    "id": user_response.user.id,
                    "email": user_response.user.email,
                    "name": user_response.user.user_metadata.get("name", "Utilisateur"),
                    "subscription_type": user_response.user.user_metadata.get("subscription_type", "free")
                }
    except:
        pass
    return None