#!/usr/bin/env python3
"""
Mapping émotionnel intelligent pour VibeFilms
Détecte les émotions dans les requêtes et boost les genres correspondants
"""

import re
from typing import Dict, List, Tuple, Optional

class EmotionMapper:
    def __init__(self):
        # Mapping émotions/états -> genres avec coefficients de boost
        self.emotion_mappings = {
            # DÉTENTE / RELAXATION / CHILL
            "detente": {
                "keywords": ["détendre", "chill", "relaxer", "zen", "paisible", "calme", "tranquille", "reposer"],
                "phrases": [],
                "target_genres": {"Drame": 6.0, "Romance": 5.0, "Comédie": 4.0, "Familial": 4.0},
                "boost_keywords": ["paisible", "relaxant", "doux", "contemplatif", "slow", "nature"]
            },

            # RÉCONFORT / BESOIN DE CHALEUR
            "reconfort": {
                "keywords": ["réconfort", "chaleur", "bienveillant", "réconfortant", "doudou", "cocooning"],
                "phrases": [],
                "target_genres": {"Familial": 8.0, "Romance": 6.0, "Animation": 5.0, "Comédie": 4.0},
                "boost_keywords": ["touchant", "bienveillant", "chaleureux", "émotionnel", "feel-good"]
            },

            # STRESS / BESOIN D'ÉVACUER
            "stress": {
                "keywords": ["stressé", "énervé", "tendu", "évacuer", "défouler", "exploser"],
                "phrases": [],
                "target_genres": {"Action": 8.0, "Comédie": 6.0, "Thriller": 4.0},
                "boost_keywords": ["explosif", "défouloir", "cathartique", "intense", "libérateur"]
            },

            # NOSTALGIE / SOUVENIRS
            "nostalgie": {
                "keywords": ["nostalgie", "nostalgique", "souvenirs", "passé", "mélancolie", "enfance"],
                "phrases": [],
                "target_genres": {"Drame": 8.0, "Romance": 6.0, "Familial": 5.0},
                "boost_keywords": ["nostalgique", "émouvant", "touchant", "mélancolique", "souvenir"]
            },

            # RIRE / HUMOUR / COMÉDIE
            "rire": {
                "keywords": ["rire", "marrer", "rigoler", "drôle", "délirer"],
                "phrases": [],
                "target_genres": {"Comédie": 8.0, "Familial": 4.0, "Animation": 3.0},
                "boost_keywords": ["drôle", "amusant", "hilarant", "comique", "rigolo", "marrant", "gag", "humour"]
            },
            
            # PEUR / HORREUR / ANGOISSE
            "peur": {
                "keywords": ["peur"],  # SIMPLE : DÈS QU'IL Y A "PEUR" → BOOST HORREUR
                "phrases": [],  # TOUTES LES PHRASES CONTENANT "PEUR" SONT DÉTECTÉES
                "target_genres": {"Horreur": 10.0},  # BOOST ULTRA-AGRESSIF - HORREUR UNIQUEMENT
                "boost_keywords": ["horreur", "épouvante", "effrayant", "terrifiant", "gore", "cauchemar", "zombie", "fantôme"]
            },
            
            # TRISTESSE / ÉMOTION / DRAME
            "tristesse": {
                "keywords": ["triste"],  # SIMPLE : DÈS QU'IL Y A "TRISTE" → BOOST DRAME
                "phrases": [],
                "target_genres": {"Drame": 8.0, "Romance": 4.0},
                "boost_keywords": ["émouvant", "bouleversant", "touchant", "poignant", "mélancolique", "nostalgique"]
            },
            
            # ROMANCE / AMOUR / TENDRESSE
            "amour": {
                "keywords": ["amour", "romantique", "couple", "tendresse", "passion", "cœur"],
                "phrases": [],
                "target_genres": {"Romance": 8.0, "Drame": 4.0, "Comédie": 3.0},
                "boost_keywords": ["romantique", "passionné", "tendre", "sensuel", "couple", "mariage", "baiser"]
            },

            # SOLITUDE / TRISTESSE
            "solitude": {
                "keywords": ["seul", "isolé", "solitaire", "abandon", "vide", "mélancolie"],
                "phrases": [],
                "target_genres": {"Drame": 8.0, "Romance": 4.0, "Thriller": 3.0},
                "boost_keywords": ["introspectif", "contemplatif", "mélancolique", "profond", "existentiel"]
            },

            # MOTIVATION / INSPIRATION
            "motivation": {
                "keywords": ["motiver", "inspirer", "courage", "détermination", "réussir", "vaincre", "surmonter"],
                "phrases": [],
                "target_genres": {"Drame": 7.0, "Action": 6.0, "Aventure": 5.0, "Familial": 4.0},
                "boost_keywords": ["inspirant", "motivant", "triomphe", "résilience", "espoir", "courage"]
            },

            # ÉVASION / VOYAGER / AVENTURE
            "evasion": {
                "keywords": ["évader", "voyager", "partir", "ailleurs", "découvrir", "explorer", "liberté"],
                "phrases": [],
                "target_genres": {"Aventure": 8.0, "Fantastique": 6.0, "Science-Fiction": 5.0, "Animation": 4.0},
                "boost_keywords": ["évasion", "voyage", "découverte", "exploration", "liberté", "horizon"]
            },
            
            # ACTION / ADRÉNALINE / EXCITATION
            "action": {
                "keywords": ["action"],  # SIMPLE : DÈS QU'IL Y A "ACTION" → BOOST ACTION
                "phrases": [],
                "target_genres": {"Action": 8.0, "Thriller": 4.0, "Aventure": 3.0},
                "boost_keywords": ["intense", "explosif", "rapide", "combat", "poursuite", "bagarre", "spectaculaire"]
            },
            
            # FAMILLE / ENFANTS / INNOCENCE
            "famille": {
                "keywords": ["famille"],  # SIMPLE : DÈS QU'IL Y A "FAMILLE" → BOOST FAMILIAL
                "phrases": [],
                "target_genres": {"Familial": 8.0, "Animation": 6.0, "Comédie": 4.0},
                "boost_keywords": ["familial", "enfant", "mignon", "innocent", "éducatif", "bienveillant"]
            },
            
            # SCIENCE-FICTION / FUTUR / TECHNOLOGIE
            "futur": {
                "keywords": ["futur"],  # SIMPLE : DÈS QU'IL Y A "FUTUR" → BOOST SF
                "phrases": [],
                "target_genres": {"Science-Fiction": 8.0, "Action": 4.0},
                "boost_keywords": ["futuriste", "technologique", "spatial", "alien", "robot", "cyberpunk"]
            },
            
            # MYSTÈRE / SUSPENSE / ENQUÊTE
            "mystere": {
                "keywords": ["mystère"],  # SIMPLE : DÈS QU'IL Y A "MYSTÈRE" → BOOST MYSTÈRE
                "phrases": [],
                "target_genres": {"Mystère": 8.0, "Thriller": 6.0, "Crime": 4.0},
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