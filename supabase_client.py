#!/usr/bin/env python3
"""
Client Supabase pour PickMe - Gestion des utilisateurs et interactions films.
"""

import os
from typing import List, Dict, Optional
from supabase import create_client, Client
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

class SupabaseManager:
    def __init__(self):
        """Initialise le client Supabase."""
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")
        self.service_key = os.getenv("SUPABASE_SERVICE_KEY")
        
        # Mode développement : permettre de démarrer sans Supabase configuré
        self.enabled = False
        self.supabase = None
        self.admin_client = None
        
        if not self.url or not self.key or "your-project" in self.url:
            print("⚠️  Supabase non configuré - mode développement activé")
            print("📝 Complétez le fichier .env avec vos vraies clés Supabase")
            return
        
        try:
            # Client pour les opérations publiques (avec anon key)
            self.supabase: Client = create_client(self.url, self.key)
            
            # Client pour les opérations admin (avec service key)
            if self.service_key:
                self.admin_client: Client = create_client(self.url, self.service_key)
            else:
                self.admin_client = self.supabase
            
            self.enabled = True
            print("✅ Supabase configuré et connecté")
        except Exception as e:
            print(f"❌ Erreur connexion Supabase: {e}")
            print("📝 Vérifiez vos clés dans le fichier .env")
    
    def create_tables(self):
        """Crée les tables nécessaires dans Supabase."""
        
        # SQL pour créer la table user_movie_interactions
        create_table_sql = """
        -- Table pour stocker les interactions utilisateur-film
        CREATE TABLE IF NOT EXISTS user_movie_interactions (
            id BIGSERIAL PRIMARY KEY,
            user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
            movie_id INTEGER NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('wishlist', 'not_interested', 'seen')),
            rating INTEGER CHECK (rating >= 1 AND rating <= 5),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            
            -- Contrainte unique : un utilisateur ne peut avoir qu'une interaction par film
            UNIQUE(user_id, movie_id)
        );
        
        -- Index pour les requêtes fréquentes
        CREATE INDEX IF NOT EXISTS idx_user_movie_interactions_user_id ON user_movie_interactions(user_id);
        CREATE INDEX IF NOT EXISTS idx_user_movie_interactions_movie_id ON user_movie_interactions(movie_id);
        CREATE INDEX IF NOT EXISTS idx_user_movie_interactions_status ON user_movie_interactions(status);
        
        -- Fonction pour auto-update du timestamp
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        
        -- Trigger pour auto-update
        DROP TRIGGER IF EXISTS update_user_movie_interactions_updated_at ON user_movie_interactions;
        CREATE TRIGGER update_user_movie_interactions_updated_at
            BEFORE UPDATE ON user_movie_interactions
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        
        -- RLS (Row Level Security) pour sécuriser les données
        ALTER TABLE user_movie_interactions ENABLE ROW LEVEL SECURITY;
        
        -- Policy : les utilisateurs ne voient que leurs propres interactions
        DROP POLICY IF EXISTS "Users can view their own interactions" ON user_movie_interactions;
        CREATE POLICY "Users can view their own interactions" ON user_movie_interactions
            FOR SELECT USING (auth.uid() = user_id);
        
        DROP POLICY IF EXISTS "Users can insert their own interactions" ON user_movie_interactions;
        CREATE POLICY "Users can insert their own interactions" ON user_movie_interactions
            FOR INSERT WITH CHECK (auth.uid() = user_id);
        
        DROP POLICY IF EXISTS "Users can update their own interactions" ON user_movie_interactions;
        CREATE POLICY "Users can update their own interactions" ON user_movie_interactions
            FOR UPDATE USING (auth.uid() = user_id);
        
        DROP POLICY IF EXISTS "Users can delete their own interactions" ON user_movie_interactions;
        CREATE POLICY "Users can delete their own interactions" ON user_movie_interactions
            FOR DELETE USING (auth.uid() = user_id);
        """
        
        try:
            # Exécuter le SQL avec le client admin
            result = self.admin_client.rpc('exec_sql', {'sql': create_table_sql})
            print("✅ Tables Supabase créées avec succès")
            return True
        except Exception as e:
            print(f"❌ Erreur création tables: {e}")
            # Fallback : essayer de créer la table via l'interface web
            print("📝 Créez cette table manuellement dans Supabase SQL Editor:")
            print(create_table_sql)
            return False
    
    # === GESTION DES INTERACTIONS FILMS ===
    
    def add_movie_interaction(self, user_id: str, movie_id: int, status: str, rating: Optional[int] = None) -> bool:
        """Ajoute ou met à jour une interaction film."""
        if not self.enabled:
            print("⚠️  Supabase non configuré - interaction ignorée")
            return False
            
        try:
            data = {
                "user_id": user_id,
                "movie_id": movie_id,
                "status": status
            }
            
            if rating is not None and status == "seen":
                data["rating"] = rating
            
            # Upsert : insert ou update si existe déjà
            result = self.supabase.table("user_movie_interactions").upsert(
                data,
                on_conflict="user_id,movie_id"
            ).execute()
            
            return True
        except Exception as e:
            print(f"❌ Erreur interaction film: {e}")
            return False
    
    def get_user_interactions(self, user_id: str, status: Optional[str] = None) -> List[Dict]:
        """Récupère les interactions d'un utilisateur."""
        if not self.enabled:
            return []
            
        try:
            query = self.supabase.table("user_movie_interactions").select("*").eq("user_id", user_id)
            
            if status:
                query = query.eq("status", status)
            
            result = query.execute()
            return result.data
        except Exception as e:
            print(f"❌ Erreur récupération interactions: {e}")
            return []
    
    def get_excluded_movies(self, user_id: str) -> List[int]:
        """Récupère les IDs des films à exclure des recommandations."""
        if not self.enabled:
            return []
            
        try:
            result = self.supabase.table("user_movie_interactions").select("movie_id").eq("user_id", user_id).in_("status", ["seen", "not_interested"]).execute()
            
            return [item["movie_id"] for item in result.data]
        except Exception as e:
            print(f"❌ Erreur récupération films exclus: {e}")
            return []
    
    def get_user_stats(self, user_id: str) -> Dict:
        """Récupère les statistiques d'un utilisateur."""
        try:
            interactions = self.get_user_interactions(user_id)
            
            stats = {
                "total_interactions": len(interactions),
                "wishlist_count": len([i for i in interactions if i["status"] == "wishlist"]),
                "seen_count": len([i for i in interactions if i["status"] == "seen"]),
                "not_interested_count": len([i for i in interactions if i["status"] == "not_interested"]),
                "average_rating": 0
            }
            
            # Calculer la note moyenne
            ratings = [i["rating"] for i in interactions if i["rating"] is not None]
            if ratings:
                stats["average_rating"] = sum(ratings) / len(ratings)
            
            return stats
        except Exception as e:
            print(f"❌ Erreur statistiques utilisateur: {e}")
            return {}
    
    # === GESTION AUTHENTIFICATION ===
    
    def create_user(self, email: str, password: str) -> Dict:
        """Crée un nouvel utilisateur."""
        if not self.enabled:
            return {"success": False, "error": "Supabase non configuré"}
            
        try:
            result = self.supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            return {"success": True, "user": result.user}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def sign_in(self, email: str, password: str) -> Dict:
        """Connecte un utilisateur."""
        if not self.enabled:
            return {"success": False, "error": "Supabase non configuré"}
            
        try:
            result = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            return {"success": True, "user": result.user, "session": result.session}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def sign_out(self) -> bool:
        """Déconnecte l'utilisateur."""
        try:
            self.supabase.auth.sign_out()
            return True
        except Exception as e:
            print(f"❌ Erreur déconnexion: {e}")
            return False
    
    def get_current_user(self) -> Optional[Dict]:
        """Récupère l'utilisateur actuel."""
        try:
            user = self.supabase.auth.get_user()
            return user.user if user else None
        except Exception as e:
            print(f"❌ Erreur utilisateur actuel: {e}")
            return None

# Instance globale
supabase_manager = SupabaseManager()

def get_supabase():
    """Récupère l'instance Supabase."""
    return supabase_manager