#!/usr/bin/env python3
"""
Ajoute des descriptions françaises pour les films populaires.
"""

import json
import re

# Dictionnaire de traductions pour les films populaires
FRENCH_DESCRIPTIONS = {
    "The Conjuring": "Les époux Warren, enquêteurs paranormaux, viennent en aide à une famille terrorisée par une présence maléfique dans leur propriété agricole isolée.",
    "Jurassic Park": "Un parc à thème peuplé de dinosaures créés génétiquement tourne au cauchemar quand les créatures s'échappent et terrorisent les visiteurs.",
    "The Matrix": "Un programmeur découvre que la réalité qu'il connaît n'est qu'une simulation informatique et rejoint une rébellion contre les machines.",
    "Titanic": "L'histoire d'amour tragique entre Jack et Rose à bord du légendaire paquebot lors de son voyage inaugural fatidique en 1912.",
    "Avatar": "Sur la lune Pandora, un marine paraplégique participe au programme Avatar et se retrouve déchiré entre suivre ses ordres et protéger le monde qu'il apprend à connaître.",
    "Inception": "Un voleur spécialisé dans l'extraction de secrets enfouis dans l'inconscient pendant le rêve se voit confier la mission inverse : l'inception.",
    "The Dark Knight": "Batman affronte le Joker, un génie criminel psychopathe qui veut plonger Gotham City dans l'anarchie et met le héros face à ses limites.",
    "Pulp Fiction": "Les vies de deux hommes de main, d'un boxeur et d'un gangster s'entremêlent dans quatre histoires de rédemption et de violence.",
    "Forrest Gump": "L'histoire extraordinaire d'un homme simple d'esprit qui traverse les grands événements de l'histoire américaine contemporaine.",
    "The Lion King": "Le jeune lion Simba fuit son royaume après la mort tragique de son père, mais doit affronter son passé pour reprendre sa place de roi.",
    "Spider-Man": "Après avoir été mordu par une araignée radioactive, Peter Parker développe des super-pouvoirs et devient Spider-Man pour protéger New York.",
    "Iron Man": "Le milliardaire Tony Stark crée une armure high-tech pour s'échapper de ses ravisseurs et devient le super-héros Iron Man.",
    "The Avengers": "Les plus grands super-héros de la Terre s'unissent pour former les Avengers et affronter une menace que nul ne peut combattre seul.",
    "Frozen": "Elsa, la reine des neiges, et sa sœur Anna vivent une aventure extraordinaire pour sauver leur royaume d'un hiver éternel.",
    "Toy Story": "Les jouets de Andy prennent vie quand il n'est pas là, et Woody le cowboy doit accepter l'arrivée de Buzz l'Éclair, le nouveau jouet préféré.",
    "Finding Nemo": "Un poisson-clown surprotecteur parcourt l'océan pour retrouver son fils Nemo, capturé par des plongeurs.",
    "The Incredibles": "Une famille de super-héros en retraite doit reprendre du service pour sauver le monde d'un génie maléfique.",
    "Shrek": "Un ogre solitaire se lance dans une quête pour sauver une princesse et récupérer son marais, accompagné d'un âne bavard.",
    "Pirates of the Caribbean": "Le capitaine Jack Sparrow s'allie avec Will Turner pour sauver Elizabeth des pirates maudits des Caraïbes.",
    "Harry Potter": "Un jeune sorcier découvre ses pouvoirs magiques et entre à Poudlard, l'école de sorcellerie, où il affronte le sombre Voldemort."
}

def add_french_descriptions():
    """Ajoute des descriptions françaises aux films populaires."""
    
    print("🇫🇷 Ajout de descriptions françaises")
    print("=" * 50)
    
    # Charger la base
    with open('production_movies_1500_final.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    movies = data['movies']
    updated = 0
    
    for movie in movies:
        title = movie.get('title', '')
        
        # Chercher une correspondance exacte ou partielle
        french_desc = None
        for key, desc in FRENCH_DESCRIPTIONS.items():
            if key.lower() in title.lower() or title.lower() in key.lower():
                french_desc = desc
                break
        
        if french_desc:
            print(f"✅ {title} -> Description française ajoutée")
            movie['overview'] = french_desc
            updated += 1
    
    # Ajouter quelques descriptions génériques pour les genres
    generic_descriptions = {
        'action': "Film d'action palpitant avec des séquences spectaculaires et des héros intrépides.",
        'comedy': "Comédie divertissante qui vous fera rire aux éclats avec des situations hilarantes.",
        'drama': "Drame émouvant qui explore les relations humaines avec profondeur et sensibilité.",
        'horror': "Film d'horreur terrifiant qui vous tiendra en haleine du début à la fin.",
        'romance': "Histoire d'amour touchante qui célèbre les sentiments et les émotions humaines.",
        'thriller': "Thriller haletant plein de suspense et de rebondissements inattendus.",
        'sci-fi': "Film de science-fiction visionnaire qui explore les possibilités du futur.",
        'fantasy': "Aventure fantastique dans un monde magique plein de merveilles et de créatures extraordinaires."
    }
    
    # Appliquer des descriptions génériques pour les films sans description française
    for movie in movies:
        if not movie.get('overview') or len(movie['overview']) < 20:
            genres = movie.get('genres', [])
            if genres:
                primary_genre = genres[0].lower()
                for genre_key, desc in generic_descriptions.items():
                    if genre_key in primary_genre:
                        movie['overview'] = desc
                        updated += 1
                        break
    
    # Sauvegarder
    with open('production_movies_1500_final.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n🎉 {updated} descriptions mises à jour!")
    print("💾 Base de données sauvegardée")
    
    return updated

if __name__ == "__main__":
    add_french_descriptions()