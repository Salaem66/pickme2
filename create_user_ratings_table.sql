-- Table pour stocker les évaluations des utilisateurs
CREATE TABLE IF NOT EXISTS user_ratings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    movie_id INTEGER NOT NULL,
    movie_title TEXT NOT NULL,
    liked BOOLEAN NOT NULL, -- true = j'aime, false = j'aime pas
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, movie_id) -- Un utilisateur ne peut noter qu'une seule fois chaque film
);

-- Index pour optimiser les recherches
CREATE INDEX IF NOT EXISTS user_ratings_user_id_idx ON user_ratings(user_id);
CREATE INDEX IF NOT EXISTS user_ratings_movie_id_idx ON user_ratings(movie_id);

-- RLS (Row Level Security) pour que chaque utilisateur ne voit que ses notations
ALTER TABLE user_ratings ENABLE ROW LEVEL SECURITY;

-- Politique pour que les utilisateurs authentifiés puissent voir/modifier leurs propres notations
CREATE POLICY "Users can view their own ratings" ON user_ratings
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own ratings" ON user_ratings
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own ratings" ON user_ratings
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own ratings" ON user_ratings
    FOR DELETE USING (auth.uid() = user_id);