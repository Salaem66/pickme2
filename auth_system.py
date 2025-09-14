#!/usr/bin/env python3
"""
Système d'authentification robuste pour VibeFilms
Gestion des comptes utilisateurs avec Supabase Auth
"""

from fastapi import HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import os
from supabase import create_client
import bcrypt
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://utzflwmghpojlsthyuqf.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV0emZsd21naHBvamxzdGh5dXFmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc1NDQxOTAsImV4cCI6MjA3MzEyMDE5MH0.j5qMspjG6FTN69DPwI0otqjw7Yp5lbbFadflpkjNvYc")
JWT_SECRET = os.getenv("JWT_SECRET", "vibefilms-super-secret-key-2024")

security = HTTPBearer()
logger = logging.getLogger(__name__)

class AuthSystem:
    def __init__(self):
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
    def validate_email(self, email: str) -> bool:
        """Validation email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_password(self, password: str) -> Dict[str, Any]:
        """Validation mot de passe avec critères sécurisés"""
        errors = []
        
        if len(password) < 8:
            errors.append("Le mot de passe doit contenir au moins 8 caractères")
        
        if not re.search(r'[A-Z]', password):
            errors.append("Le mot de passe doit contenir au moins une majuscule")
        
        if not re.search(r'[a-z]', password):
            errors.append("Le mot de passe doit contenir au moins une minuscule")
        
        if not re.search(r'\d', password):
            errors.append("Le mot de passe doit contenir au moins un chiffre")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Le mot de passe doit contenir au moins un caractère spécial")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def hash_password(self, password: str) -> str:
        """Hashage sécurisé du mot de passe"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Vérification du mot de passe"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def generate_jwt_token(self, user_data: dict) -> str:
        """Génération token JWT sécurisé"""
        payload = {
            'user_id': user_data['id'],
            'email': user_data['email'],
            'subscription_type': user_data.get('subscription_type', 'free'),
            'exp': datetime.utcnow() + timedelta(days=7),  # Expire dans 7 jours
            'iat': datetime.utcnow(),
            'iss': 'vibefilms'
        }
        
        token = jwt.encode(payload, JWT_SECRET, algorithm='HS256')
        return token
    
    def decode_jwt_token(self, token: str) -> dict:
        """Décodage et validation token JWT"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expiré"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalide"
            )
    
    async def register_user(self, email: str, password: str, name: str) -> Dict[str, Any]:
        """Inscription utilisateur"""
        
        # Validation email
        if not self.validate_email(email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email invalide"
            )
        
        # Validation password  
        password_validation = self.validate_password(password)
        if not password_validation["valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"errors": password_validation["errors"]}
            )
        
        # Vérifier si l'utilisateur existe déjà
        try:
            existing_user = self.supabase.table('users').select('email').eq('email', email).execute()
            if existing_user.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Un compte existe déjà avec cet email"
                )
        except Exception as e:
            logger.error(f"Erreur vérification utilisateur existant: {e}")
        
        # Hash du mot de passe
        hashed_password = self.hash_password(password)
        
        # Création utilisateur en base
        try:
            user_data = {
                'email': email,
                'password_hash': hashed_password,
                'name': name,
                'subscription_type': 'free',  # Compte gratuit par défaut
                'created_at': datetime.utcnow().isoformat(),
                'is_active': True,
                'preferences': {
                    'favorite_genres': [],
                    'watchlist': [],
                    'mood_history': []
                }
            }
            
            result = self.supabase.table('users').insert(user_data).execute()
            
            if result.data:
                user = result.data[0]
                token = self.generate_jwt_token(user)
                
                return {
                    "message": "Compte créé avec succès",
                    "user": {
                        "id": user['id'],
                        "email": user['email'],
                        "name": user['name'],
                        "subscription_type": user['subscription_type']
                    },
                    "token": token
                }
            
        except Exception as e:
            logger.error(f"Erreur création utilisateur: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erreur lors de la création du compte"
            )
    
    async def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """Connexion utilisateur"""
        
        # Validation email
        if not self.validate_email(email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email invalide"
            )
        
        try:
            # Récupération utilisateur
            result = self.supabase.table('users').select('*').eq('email', email).execute()
            
            if not result.data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Email ou mot de passe incorrect"
                )
            
            user = result.data[0]
            
            # Vérifier si le compte est actif
            if not user.get('is_active', True):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Compte désactivé"
                )
            
            # Vérification mot de passe
            if not self.verify_password(password, user['password_hash']):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Email ou mot de passe incorrect"
                )
            
            # Mise à jour dernière connexion
            self.supabase.table('users').update({
                'last_login': datetime.utcnow().isoformat()
            }).eq('id', user['id']).execute()
            
            # Génération token
            token = self.generate_jwt_token(user)
            
            return {
                "message": "Connexion réussie",
                "user": {
                    "id": user['id'],
                    "email": user['email'],
                    "name": user['name'],
                    "subscription_type": user.get('subscription_type', 'free')
                },
                "token": token
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erreur connexion utilisateur: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erreur lors de la connexion"
            )
    
    async def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
        """Récupération utilisateur courant à partir du token"""
        
        token = credentials.credentials
        payload = self.decode_jwt_token(token)
        
        try:
            # Récupération données utilisateur actualisées
            result = self.supabase.table('users').select('id, email, name, subscription_type, preferences, is_active').eq('id', payload['user_id']).execute()
            
            if not result.data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Utilisateur non trouvé"
                )
            
            user = result.data[0]
            
            if not user.get('is_active', True):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Compte désactivé"
                )
            
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erreur récupération utilisateur: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalide"
            )
    
    async def update_user_preferences(self, user_id: str, preferences: dict) -> Dict[str, Any]:
        """Mise à jour préférences utilisateur"""
        
        try:
            result = self.supabase.table('users').update({
                'preferences': preferences,
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', user_id).execute()
            
            if result.data:
                return {"message": "Préférences mises à jour avec succès"}
            
        except Exception as e:
            logger.error(f"Erreur mise à jour préférences: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erreur lors de la mise à jour des préférences"
            )
    
    async def add_to_watchlist(self, user_id: str, movie_id: int) -> Dict[str, Any]:
        """Ajouter film à la watchlist"""
        
        try:
            # Récupérer préférences actuelles
            result = self.supabase.table('users').select('preferences').eq('id', user_id).execute()
            
            if result.data:
                preferences = result.data[0].get('preferences', {})
                watchlist = preferences.get('watchlist', [])
                
                if movie_id not in watchlist:
                    watchlist.append(movie_id)
                    preferences['watchlist'] = watchlist
                    
                    await self.update_user_preferences(user_id, preferences)
                    
                    return {"message": "Film ajouté à votre watchlist"}
                else:
                    return {"message": "Film déjà dans votre watchlist"}
            
        except Exception as e:
            logger.error(f"Erreur ajout watchlist: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erreur lors de l'ajout à la watchlist"
            )
    
    def check_subscription_limit(self, user: dict, action: str) -> bool:
        """Vérification limites abonnement freemium"""
        
        subscription_type = user.get('subscription_type', 'free')
        
        # Limites pour compte gratuit
        if subscription_type == 'free':
            preferences = user.get('preferences', {})
            
            if action == 'search':
                # Limite à 10 recherches par jour pour les comptes gratuits
                # (à implémenter avec un compteur quotidien)
                return True
            
            elif action == 'watchlist':
                # Limite watchlist à 20 films pour les comptes gratuits
                watchlist = preferences.get('watchlist', [])
                return len(watchlist) < 20
        
        # Comptes premium : pas de limites
        return True

# Instance globale
auth_system = AuthSystem()

# Fonctions pour FastAPI dependency injection
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Dependency pour récupérer l'utilisateur courant"""
    return await auth_system.get_current_user(credentials)

async def get_current_user_optional(request: Request) -> Optional[dict]:
    """Dependency optionnelle pour récupérer l'utilisateur si connecté"""
    try:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer "
            payload = auth_system.decode_jwt_token(token)
            result = auth_system.supabase.table('users').select('*').eq('id', payload['user_id']).execute()
            if result.data:
                return result.data[0]
    except:
        pass
    return None