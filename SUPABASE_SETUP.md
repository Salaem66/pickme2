# 🚀 Setup Supabase pour PickMe

PickMe est maintenant prêt à être transformé en plateforme collaborative avec comptes utilisateurs et fonctionnalités sociales !

## ✅ Ce qui est déjà fait

- ✅ **Backend complet** : Routes API pour auth + interactions films
- ✅ **Modèles de données** : Tables et relations Supabase
- ✅ **Sécurité** : Authentification JWT + Row Level Security
- ✅ **Filtrage intelligent** : Exclusion automatique des films vus/pas intéressés
- ✅ **Mode développement** : Fonctionne sans Supabase configuré

## 🎯 Fonctionnalités prêtes à activer

### **Actions utilisateur :**
- ❤️ **Wishlist** : "Je veux le voir"
- 👎 **Pas intéressé** : "Ça ne m'intéresse pas" 
- ✅ **Film vu** : "Je l'ai vu" + note 1-5 étoiles
- 🚫 **Filtrage automatique** : Ne plus voir les films exclus

### **Pages utilisateur :**
- 📊 **Statistiques** : Films vus, notes moyennes, genres préférés
- 📝 **Ma liste** : Wishlist + films vus avec notes
- 🎭 **Profil** : Gestion compte utilisateur

## 🛠️ Comment activer Supabase

### Étape 1 : Créer le projet Supabase
1. Allez sur [supabase.com](https://supabase.com)
2. Créez un compte gratuit
3. Créez un nouveau projet
4. Notez l'URL et les clés API

### Étape 2 : Configurer les clés
Modifiez le fichier `.env` :
```bash
# Remplacez par vos vraies valeurs
SUPABASE_URL=https://YOUR_PROJECT_ID.supabase.co
SUPABASE_KEY=your_anon_key_here
SUPABASE_SERVICE_KEY=your_service_role_key_here
```

### Étape 3 : Créer les tables
1. Ouvrez l'éditeur SQL dans Supabase
2. Collez et exécutez ce code :

```sql
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
```

### Étape 4 : Redémarrer PickMe
```bash
# Arrêter le serveur actuel (Ctrl+C)
# Puis redémarrer
python3 main.py
```

Vous devriez voir : `✅ Supabase configuré et connecté`

## 🧪 Tester l'intégration

```bash
# Tester que tout fonctionne
python3 test_supabase_setup.py
```

## 📡 API Endpoints disponibles

### **Authentification :**
- `POST /auth/signup` - Créer un compte
- `POST /auth/signin` - Se connecter  
- `POST /auth/signout` - Se déconnecter
- `GET /auth/user` - Profil utilisateur

### **Interactions films :**
- `POST /user/movie/{id}/interaction` - Ajouter/modifier interaction
- `GET /user/interactions` - Récupérer ses interactions
- `GET /user/stats` - Statistiques personnelles

### **Recherche améliorée :**
- `POST /search` - Recherche avec filtrage automatique des films exclus

## 🎨 Prochaines étapes

1. **Frontend** : Ajouter les boutons d'action sur les cartes films
2. **Pages utilisateur** : Créer les interfaces de gestion
3. **Recommandations** : IA basée sur les goûts utilisateur
4. **Social** : Partage de listes, avis, etc.

## 💡 Architecture technique

```
Frontend (JavaScript)
    ↓ HTTP/JWT
Backend (FastAPI + Supabase)
    ↓ Vector Search  
ChromaDB (1500 films)
    ↓ Metadata
TMDB API
```

**PickMe est maintenant prêt à devenir le Netflix personnalisé de vos rêves ! 🎬✨**