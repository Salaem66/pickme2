# 🎬 VibeFilms - Moteur de Recherche de Films par Mood

VibeFilms est un moteur de recherche de films innovant qui utilise l'intelligence artificielle et les bases vectorielles pour recommander des films basés sur votre humeur et vos émotions.

## 🚀 Fonctionnalités

- **Recherche par mood** : Décrivez votre humeur en langage naturel (ex: "je me sens nostalgique", "j'ai envie de rire")
- **Recherche vectorielle** : Utilise des embeddings sémantiques pour comprendre le sens de vos requêtes
- **Base de données de films** : Intégration avec l'API TMDB pour des données à jour
- **Interface web intuitive** : Interface simple et élégante pour explorer les recommandations
- **API REST** : Endpoints pour intégrer le moteur dans d'autres applications

## 🛠️ Technologies Utilisées

- **Backend** : FastAPI (Python)
- **IA/ML** : SentenceTransformers, Scikit-learn
- **Base de données** : TMDB API
- **Frontend** : HTML/CSS/JavaScript vanilla
- **Recherche vectorielle** : Embeddings sémantiques avec similarité cosinus

## 📦 Installation

1. **Cloner le repository**
```bash
git clone <repository-url>
cd VibeFilms
```

2. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

3. **Configuration**
   - Copiez votre clé API TMDB dans le fichier `.env`
   - La clé est déjà configurée dans le projet

4. **Collecter les données de films**
```bash
python3 collect_sample.py
```

5. **Lancer l'application**
```bash
python3 main.py
```

6. **Accéder à l'interface**
   - Interface web : http://localhost:8000
   - Documentation API : http://localhost:8000/docs

## 🎯 Utilisation

### Interface Web
1. Ouvrez http://localhost:8000
2. Décrivez votre humeur dans la barre de recherche
3. Cliquez sur "Rechercher" ou utilisez les suggestions
4. Explorez les films recommandés avec leurs scores de correspondance

### API REST

**Recherche par mood :**
```bash
curl -X POST "http://localhost:8000/search" \
     -H "Content-Type: application/json" \
     -d '{"mood": "je me sens nostalgique", "limit": 5}'
```

**Obtenir des suggestions de moods :**
```bash
curl "http://localhost:8000/mood-suggestions"
```

**Statistiques :**
```bash
curl "http://localhost:8000/stats"
```

## 🏗️ Architecture

```
VibeFilms/
├── main.py                 # API FastAPI principale
├── vector_engine.py        # Moteur de recherche vectorielle
├── tmdb_client.py         # Client API TMDB
├── data_collector.py      # Collecteur de données de films
├── collect_sample.py      # Script de collecte d'échantillons
├── static/
│   └── index.html         # Interface web
├── .env                   # Configuration (clé API)
├── requirements.txt       # Dépendances Python
├── sample_movies.json     # Base de données locale
└── embeddings.pkl         # Cache des embeddings
```

## 🧠 Comment ça fonctionne

1. **Collecte de données** : Récupération des films via l'API TMDB avec métadonnées (titre, synopsis, genres)

2. **Création d'embeddings** : Transformation des descriptions de films en vecteurs numériques via SentenceTransformers

3. **Recherche sémantique** : 
   - Conversion de votre mood en vecteur
   - Calcul de similarité cosinus avec tous les films
   - Classement par pertinence

4. **Recommandations** : Retour des films les plus similaires à votre mood avec scores de correspondance

## 📊 Exemple de Recherches

- **"je me sens nostalgique"** → Films dramatiques, coming-of-age
- **"j'ai envie de rire"** → Comédies, films légers
- **"quelque chose d'intense"** → Thrillers, films d'action
- **"une histoire d'amour"** → Films romantiques, drames sentimentaux
- **"quelque chose qui fait peur"** → Films d'horreur, suspense

## 🚀 Développement

### Ajouter plus de films
```bash
# Modifier collect_sample.py pour collecter plus de pages
python3 collect_sample.py
```

### Personnaliser le modèle d'embedding
```python
# Dans vector_engine.py, changer le modèle
engine = VectorSearchEngine(model_name="all-mpnet-base-v2")
```

### Étendre l'API
- Ajouter de nouveaux endpoints dans `main.py`
- Implémenter des filtres avancés (genre, année, note)
- Intégrer d'autres sources de données

## 🤝 Contribution

1. Fork le projet
2. Créez votre branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

## 📈 Améliorations Futures

- [ ] Intégration ChromaDB pour base vectorielle persistante
- [ ] Système de filtres avancés (genre, année, acteurs)
- [ ] Historique des recherches utilisateur
- [ ] Recommendations personnalisées
- [ ] Support multilingue
- [ ] Interface mobile responsive
- [ ] Intégration plateformes de streaming

## 📝 License

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 🙏 Remerciements

- [TMDB](https://www.themoviedb.org/) pour l'API de données de films
- [SentenceTransformers](https://www.sbert.net/) pour les modèles d'embedding
- [FastAPI](https://fastapi.tiangolo.com/) pour le framework web

---

**Créé avec ❤️ pour explorer les bases vectorielles et l'IA appliquée au divertissement**