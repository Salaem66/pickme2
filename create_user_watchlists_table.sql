-- Table pour stocker les watchlists des utilisateurs
CREATE TABLE IF NOT EXISTS user_watchlists (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    movie_data JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)
);

-- Index pour optimiser les recherches par user_id
CREATE INDEX IF NOT EXISTS user_watchlists_user_id_idx ON user_watchlists(user_id);

-- RLS (Row Level Security) pour que chaque utilisateur ne voit que sa watchlist
ALTER TABLE user_watchlists ENABLE ROW LEVEL SECURITY;

-- Politique pour que les utilisateurs authentifiés puissent voir/modifier leur propre watchlist
CREATE POLICY "Users can view their own watchlist" ON user_watchlists
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own watchlist" ON user_watchlists
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own watchlist" ON user_watchlists
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own watchlist" ON user_watchlists
    FOR DELETE USING (auth.uid() = user_id);