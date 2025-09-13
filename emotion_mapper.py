#!/usr/bin/env python3
"""
Mapping émotionnel intelligent pour VibeFilms
Détecte les émotions dans les requêtes et boost les genres correspondants
"""

import re
from typing import Dict, List, Tuple, Optional

class EmotionMapper:
    def __init__(self):
        # Mapping émotions -> genres avec coefficients de boost
        self.emotion_mappings = {
            # RIRE / HUMOUR / COMÉDIE
            "rire": {
                "keywords": ["rire", "rigoler", "marrer", "éclater", "pouffer", "se bidonner"],
                "phrases": ["j'ai envie de rire", "envie de rigoler", "besoin de rire", "faire rire"],
                "target_genres": {"Comédie": 2.0, "Familial": 1.5, "Animation": 1.3},
                "boost_keywords": ["drôle", "amusant", "hilarant", "comique", "rigolo", "marrant", "gag", "humour"]
            },
            
            # PEUR / HORREUR / ANGOISSE
            "peur": {
                "keywords": ["peur", "effrayer", "terrifier", "angoisser", "flipper", "trembler"],
                "phrases": ["j'ai peur", "j'ai envie de me faire peur", "envie d'avoir peur", "me faire flipper", "avoir la trouille", "faire peur"],
                "target_genres": {"Horreur": 10.0},  # BOOST ULTRA-AGRESSIF - HORREUR UNIQUEMENT
                "boost_keywords": ["effrayant", "terrifiant", "angoissant", "flippant", "gore", "suspense", "frisson", "horreur", "épouvante", "cauchemar", "zombie", "fantôme", "diable", "démon", "massacre", "sanglant"]
            },
            
            # TRISTESSE / ÉMOTION / DRAME
            "tristesse": {
                "keywords": ["triste", "pleurer", "émouvoir", "bouleverser", "mélancolie", "cafard"],
                "phrases": ["je me sens triste", "envie de pleurer", "me faire pleurer", "être ému"],
                "target_genres": {"Drame": 2.0, "Romance": 1.5, "Familial": 1.3},
                "boost_keywords": ["émouvant", "bouleversant", "touchant", "poignant", "mélancolique", "nostalgique"]
            },
            
            # ROMANCE / AMOUR / TENDRESSE
            "amour": {
                "keywords": ["amour", "romance", "romantique", "tendresse", "passion", "cœur"],
                "phrases": ["je veux de la romance", "envie d'amour", "histoire d'amour", "film romantique"],
                "target_genres": {"Romance": 2.5, "Drame": 1.5, "Comédie": 1.2},
                "boost_keywords": ["romantique", "passionné", "tendre", "sensuel", "couple", "mariage", "baiser"]
            },
            
            # ACTION / ADRÉNALINE / EXCITATION
            "action": {
                "keywords": ["action", "adrénaline", "excitation", "intensité", "bagarre", "combat"],
                "phrases": ["action et adrénaline", "quelque chose d'intense", "du mouvement", "de l'action"],
                "target_genres": {"Action": 2.5, "Thriller": 2.0, "Aventure": 1.8, "Crime": 1.5},
                "boost_keywords": ["intense", "explosif", "rapide", "combat", "poursuite", "bagarre", "spectaculaire"]
            },
            
            # FAMILLE / ENFANTS / INNOCENCE
            "famille": {
                "keywords": ["famille", "enfant", "familial", "innocent", "mignon", "ensemble"],
                "phrases": ["film pour famille", "avec les enfants", "film familial", "tout public"],
                "target_genres": {"Familial": 2.5, "Animation": 2.0, "Comédie": 1.5, "Aventure": 1.3},
                "boost_keywords": ["familial", "enfant", "mignon", "innocent", "éducatif", "bienveillant"]
            },
            
            # SCIENCE-FICTION / FUTUR / TECHNOLOGIE
            "futur": {
                "keywords": ["futur", "science-fiction", "technologie", "espace", "alien", "robot"],
                "phrases": ["science-fiction et futur", "dans le futur", "technologie avancée", "espace"],
                "target_genres": {"Science-Fiction": 2.5, "Action": 1.5, "Thriller": 1.3},
                "boost_keywords": ["futuriste", "technologique", "spatial", "alien", "robot", "cyberpunk"]
            },
            
            # MYSTÈRE / SUSPENSE / ENQUÊTE
            "mystere": {
                "keywords": ["mystère", "suspense", "enquête", "secret", "énigme", "investigation"],
                "phrases": ["mystère et suspense", "une enquête", "plein de mystères", "découvrir un secret"],
                "target_genres": {"Mystère": 2.5, "Thriller": 2.0, "Crime": 1.8, "Drame": 1.3},
                "boost_keywords": ["mystérieux", "énigmatique", "secret", "investigation", "détective", "révélation"]
            }
        }
    
    def detect_emotions(self, query: str) -> List[Tuple[str, float]]:
        """Détecte les émotions dans une requête et retourne les genres à booster"""
        query_lower = query.lower()
        detected_emotions = []
        
        for emotion, config in self.emotion_mappings.items():
            emotion_score = 0.0
            
            # Vérifier les phrases exactes (score max)
            for phrase in config["phrases"]:
                if phrase.lower() in query_lower:
                    emotion_score = max(emotion_score, 1.0)
                    break
            
            # Vérifier les mots-clés (score modéré)
            if emotion_score < 1.0:
                for keyword in config["keywords"]:
                    if keyword.lower() in query_lower:
                        emotion_score = max(emotion_score, 0.7)
            
            # Vérifier les mots de boost (score faible)
            if emotion_score < 0.7:
                for boost_word in config["boost_keywords"]:
                    if boost_word.lower() in query_lower:
                        emotion_score = max(emotion_score, 0.4)
            
            if emotion_score > 0:
                detected_emotions.append((emotion, emotion_score))
        
        # Trier par score décroissant
        detected_emotions.sort(key=lambda x: x[1], reverse=True)
        return detected_emotions
    
    def enhance_query(self, query: str) -> str:
        """Améliore la requête en ajoutant des mots-clés contextuels"""
        detected_emotions = self.detect_emotions(query)
        
        if not detected_emotions:
            return query
        
        # Prendre l'émotion la plus forte
        top_emotion, score = detected_emotions[0]
        config = self.emotion_mappings[top_emotion]
        
        # Ajouter des mots-clés de boost selon le score
        enhanced_query = query
        
        if score >= 0.7:  # Émotion forte détectée
            # Ajouter les mots-clés de genre principaux
            top_genres = sorted(config["target_genres"].items(), key=lambda x: x[1], reverse=True)[:2]
            for genre, _ in top_genres:
                enhanced_query += f" {genre.lower()}"
            
            # Ajouter quelques mots-clés de boost
            boost_words = config["boost_keywords"][:3]
            for word in boost_words:
                enhanced_query += f" {word}"
        
        return enhanced_query
    
    def get_genre_boosts(self, query: str) -> Dict[str, float]:
        """Retourne les coefficients de boost par genre pour une requête"""
        detected_emotions = self.detect_emotions(query)
        genre_boosts = {}
        
        for emotion, emotion_score in detected_emotions:
            config = self.emotion_mappings[emotion]
            
            for genre, base_boost in config["target_genres"].items():
                # Ajuster le boost selon la force de détection de l'émotion
                adjusted_boost = base_boost * emotion_score
                
                # Cumuler les boosts si plusieurs émotions ciblent le même genre
                if genre in genre_boosts:
                    genre_boosts[genre] = max(genre_boosts[genre], adjusted_boost)
                else:
                    genre_boosts[genre] = adjusted_boost
        
        return genre_boosts
    
    def explain_detection(self, query: str) -> str:
        """Explique la détection d'émotion pour debug"""
        detected_emotions = self.detect_emotions(query)
        genre_boosts = self.get_genre_boosts(query)
        enhanced_query = self.enhance_query(query)
        
        explanation = f"🔍 Analyse de: '{query}'\n"
        
        if detected_emotions:
            explanation += f"📊 Émotions détectées:\n"
            for emotion, score in detected_emotions:
                explanation += f"  • {emotion}: {score:.2f}\n"
            
            explanation += f"🎬 Boost de genres:\n"
            for genre, boost in sorted(genre_boosts.items(), key=lambda x: x[1], reverse=True):
                explanation += f"  • {genre}: x{boost:.1f}\n"
            
            explanation += f"✨ Requête améliorée: '{enhanced_query}'\n"
        else:
            explanation += "❌ Aucune émotion détectée\n"
        
        return explanation

# Instance globale
emotion_mapper = EmotionMapper()

def test_emotion_mapping():
    """Test du système de mapping émotionnel"""
    test_queries = [
        "j'ai envie de rire",
        "j'ai envie d'avoir peur", 
        "je me sens triste",
        "je veux de la romance",
        "action et adrénaline",
        "film pour famille",
        "science-fiction et futur",
        "mystère et suspense"
    ]
    
    print("🎭 Test du mapping émotionnel")
    print("=" * 50)
    
    for query in test_queries:
        print(emotion_mapper.explain_detection(query))
        print("-" * 30)

if __name__ == "__main__":
    test_emotion_mapping()