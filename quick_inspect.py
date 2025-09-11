#!/usr/bin/env python3
"""
Script rapide pour inspecter les données actuelles
"""

import pickle
from collections import Counter

def quick_inspect():
    print("📂 Inspection rapide des données...")
    
    with open('streaming_500_embeddings.pkl', 'rb') as f:
        data = pickle.load(f)
    
    movies = data['movies']
    print(f"✅ {len(movies)} films chargés")
    
    # Inspecter quelques descriptions
    print("\n📝 Exemples de descriptions:")
    for i, movie in enumerate(movies[:3]):
        overview = movie.get('overview', 'Pas de description')[:100]
        print(f"  {movie.get('title', 'Unknown')}: {overview}...")
    
    # Inspecter les plateformes
    print("\n🏷️  Analyse des plateformes:")
    all_platforms = Counter()
    for movie in movies:
        watch_providers = movie.get('watch_providers', {})
        for provider_type in ['streaming', 'rent', 'buy']:
            platforms = watch_providers.get(provider_type, [])
            all_platforms.update(platforms)
    
    print(f"📊 {len(all_platforms)} plateformes uniques")
    print("Les 15 plus courantes:")
    for platform, count in all_platforms.most_common(15):
        print(f"  {platform}: {count} films")
    
    # Chercher des doublons évidents
    print("\n🔍 Doublons potentiels:")
    platform_names = list(all_platforms.keys())
    potential_duplicates = []
    
    for name in platform_names:
        name_lower = name.lower()
        if 'netflix' in name_lower and 'netflix' != name_lower:
            potential_duplicates.append(name)
        elif 'amazon' in name_lower or 'prime' in name_lower:
            potential_duplicates.append(name)
        elif 'disney' in name_lower:
            potential_duplicates.append(name)
        elif 'apple' in name_lower:
            potential_duplicates.append(name)
    
    for dup in potential_duplicates[:10]:
        count = all_platforms[dup]
        print(f"  {dup}: {count} films")

if __name__ == "__main__":
    quick_inspect()