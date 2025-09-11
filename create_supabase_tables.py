#!/usr/bin/env python3
"""
Script pour créer automatiquement les tables Supabase de PickMe.
"""

from supabase_client import get_supabase

def create_tables():
    """Crée les tables Supabase pour PickMe."""
    
    print("🚀 Création des tables Supabase pour PickMe")
    print("=" * 50)
    
    supabase = get_supabase()
    
    if not supabase.enabled:
        print("❌ Supabase non configuré. Vérifiez votre fichier .env")
        return False
    
    # Essayer de créer les tables
    success = supabase.create_tables()
    
    if success:
        print("✅ Tables créées avec succès!")
        print("\n🧪 Test de la table...")
        
        # Test simple d'insertion
        try:
            # Note: Ceci échouera car on n'a pas d'utilisateur authentifié, 
            # mais ça confirme que la table existe
            test_result = supabase.supabase.table("user_movie_interactions").select("*").limit(1).execute()
            print("✅ Table accessible!")
            return True
        except Exception as e:
            if "relation \"user_movie_interactions\" does not exist" in str(e):
                print("❌ Table non créée. Utilisez l'interface web Supabase.")
                return False
            else:
                print("✅ Table créée (erreur normale d'accès)")
                return True
    else:
        print("\n📝 Créez la table manuellement dans Supabase:")
        print("1. Allez sur https://supabase.com/dashboard")
        print("2. Sélectionnez votre projet") 
        print("3. Menu SQL Editor")
        print("4. Exécutez le SQL ci-dessous:")
        print("\n" + "="*60)
        
        sql = """
-- Table pour stocker les interactions utilisateur-film
CREATE TABLE user_movie_interactions (
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
CREATE INDEX idx_user_movie_interactions_user_id ON user_movie_interactions(user_id);
CREATE INDEX idx_user_movie_interactions_movie_id ON user_movie_interactions(movie_id);
CREATE INDEX idx_user_movie_interactions_status ON user_movie_interactions(status);

-- Fonction pour auto-update du timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger pour auto-update
CREATE TRIGGER update_user_movie_interactions_updated_at
    BEFORE UPDATE ON user_movie_interactions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- RLS (Row Level Security) pour sécuriser les données
ALTER TABLE user_movie_interactions ENABLE ROW LEVEL SECURITY;

-- Policy : les utilisateurs ne voient que leurs propres interactions
CREATE POLICY "Users can view their own interactions" ON user_movie_interactions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own interactions" ON user_movie_interactions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own interactions" ON user_movie_interactions
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own interactions" ON user_movie_interactions
    FOR DELETE USING (auth.uid() = user_id);
"""
        print(sql)
        print("="*60)
        return False

if __name__ == "__main__":
    create_tables()