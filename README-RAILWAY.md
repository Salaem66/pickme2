# 🚀 VibeFilms sur Railway

## Déploiement Railway - Guide Rapide

### 1. Connexion Railway
1. Va sur [railway.app](https://railway.app)
2. Connecte ton compte GitHub
3. Clique "New Project" → "Deploy from GitHub repo"
4. Sélectionne `Salaem66/pickme2`

### 2. Configuration automatique
Railway détectera automatiquement :
- ✅ **Python** via `requirements.txt`
- ✅ **Start command** via `Procfile` ou `railway.json`
- ✅ **Port dynamique** via variable `$PORT`

### 3. Variables d'environnement (optionnel)
Si tu veux customiser :
```
PORT=8000                    # Port par défaut
PYTHONUNBUFFERED=1          # Logs en temps réel
```

### 4. Premier déploiement
- Railway va build et déployer automatiquement
- URL générée automatiquement (ex: `pickme2-production.up.railway.app`)
- Déploiement continu sur chaque push GitHub

### 5. Interfaces disponibles
- **Tech**: `https://ton-url.railway.app/`
- **Moderne**: `https://ton-url.railway.app/modern`
- **Classique**: `https://ton-url.railway.app/classic`
- **Tinder**: `https://ton-url.railway.app/tinder`
- **API**: `https://ton-url.railway.app/api/search?q=action`

## Avantages Railway vs Vercel

### ✅ **Performance**
- **Serveur persistant** - Pas de cold start
- **Modèle ML en mémoire** - Réponses ultra-rapides
- **Pas de timeout** - Requêtes complexes OK

### ✅ **Simplicité**
- **Auto-deploy GitHub** - Comme Vercel
- **Configuration minimale** - Juste `requirements.txt` + `main.py`
- **Logs en temps réel** - Debug facile

### ✅ **Coût**
- **$5/mois fixe** - Pas de surprise
- **Sleep après inactivité** - Économies automatiques
- **Plus prévisible** - Pas de facturation par requête

## Test local avant déploiement

```bash
# Installer les dépendances
pip install -r requirements.txt

# Lancer le serveur
python main.py

# Test de l'API
curl "http://localhost:8000/api/search?q=action"
```

## Architecture Railway vs Vercel

```
RAILWAY (Recommandé)          VERCEL (Actuel)
├── Serveur persistant        ├── Functions serverless 
├── Modèle chargé une fois    ├── Modèle rechargé à chaque call
├── Pas de cold start         ├── Cold start ~3s
├── Timeout illimité          ├── Timeout 30s max
├── $5/mois                   ├── Pay per request
└── Debug facile              └── Logs fragmentés
```

Railway est **parfait** pour une API ML comme VibeFilms ! 🎯