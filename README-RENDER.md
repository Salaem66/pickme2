# 🚀 VibeFilms sur Render.com

## Render vs Railway - Plus fiable pour ML !

### Pourquoi Render pour VibeFilms ?
- **🛠️ Infrastructure plus stable** - Moins de timeouts
- **📊 Meilleure gestion des gros builds** - PyTorch + Transformers
- **💰 Pricing clair** - $7/mois Starter Plan
- **🔧 Support ML natif** - Optimisé pour les apps IA

## Déploiement Render - 3 étapes

### 1. Connexion Render
1. Va sur [render.com](https://render.com)
2. **Sign up** avec GitHub
3. **New** → **Web Service**
4. **Connect Repository** → `Salaem66/pickme2`

### 2. Configuration automatique
Render détecte automatiquement :
- ✅ **Python** via `requirements.txt`
- ✅ **Build command** : `pip install -r requirements.txt`
- ✅ **Start command** : `python main.py`
- ✅ **Port** : 10000 (via `render.yaml`)

### 3. Paramètres
- **Plan** : Starter ($7/mois)
- **Region** : Oregon (US-West) 
- **Auto Deploy** : Activé sur push GitHub

## Avantages Render vs Railway

```
RENDER                      RAILWAY
✅ Build stable ML          ❌ Timeout fréquents  
✅ $7/mois fixe            ✅ $5/mois  
✅ Support PyTorch natif    ❌ Docker issues
✅ 24/7 uptime garanti     ❌ Infrastructure instable
✅ Free SSL automatique    ✅ Free SSL
```

## URLs une fois déployé
- **App** : `https://vibefilms.onrender.com`
- **API** : `https://vibefilms.onrender.com/api/search?q=action`
- **Health** : `https://vibefilms.onrender.com/api/health`

## Performance attendue
- **Premier démarrage** : ~30-60s (normal pour ML)
- **Requêtes** : ~200-500ms (modèle en mémoire)
- **Uptime** : 99.9% garanti

## Alternative rapide
Si Railway continue à planter, Render est une **excellente alternative** plus stable pour les apps ML ! 🎯