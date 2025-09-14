-- Création table users pour VibeFilms
-- Système d'authentification avec préférences utilisateur

CREATE TABLE IF NOT EXISTS users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name VARCHAR(100) NOT NULL,
    subscription_type VARCHAR(20) DEFAULT 'free' CHECK (subscription_type IN ('free', 'premium')),
    is_active BOOLEAN DEFAULT true,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE
);

-- Index pour performances
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_subscription ON users(subscription_type);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);

-- RLS (Row Level Security) pour sécurité
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Politique : les utilisateurs ne peuvent voir que leurs propres données
CREATE POLICY users_policy ON users FOR ALL USING (auth.uid()::text = id::text);

-- Table pour tracking des recherches (limites freemium)
CREATE TABLE IF NOT EXISTS user_search_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    search_query TEXT,
    search_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index pour comptage quotidien
CREATE INDEX IF NOT EXISTS idx_search_logs_user_date ON user_search_logs(user_id, search_date);

-- Fonction pour compter recherches quotidiennes
CREATE OR REPLACE FUNCTION count_daily_searches(p_user_id UUID, p_date DATE DEFAULT CURRENT_DATE)
RETURNS INTEGER AS $$
BEGIN
    RETURN (
        SELECT COUNT(*)
        FROM user_search_logs
        WHERE user_id = p_user_id
        AND search_date = p_date
    );
END;
$$ LANGUAGE plpgsql;

-- Fonction pour enregistrer une recherche
CREATE OR REPLACE FUNCTION log_user_search(p_user_id UUID, p_query TEXT)
RETURNS VOID AS $$
BEGIN
    INSERT INTO user_search_logs (user_id, search_query)
    VALUES (p_user_id, p_query);
END;
$$ LANGUAGE plpgsql;

-- Trigger pour mise à jour automatique updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Insertion d'un utilisateur test (mot de passe: TestPass123!)
-- Hash généré avec bcrypt pour 'TestPass123!'
INSERT INTO users (email, password_hash, name, subscription_type) VALUES 
('test@vibefilms.com', '$2b$12$LQv3c1yqBWVHxkd0LRN2Qufwq5kAhOFzFe.lQE5HKCmPKYqFJY5gC', 'Utilisateur Test', 'free')
ON CONFLICT (email) DO NOTHING;