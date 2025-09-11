#!/usr/bin/env python3
"""
Script de lancement de VibeFilms en mode production avec 1500 films.
"""

import os
import sys

def check_database():
    """Vérifie que la base de production est prête."""
    if not os.path.exists("./chroma_db_1500"):
        print("❌ Base de production non trouvée!")
        print("Lancez: python3 migrate_1500_to_chromadb.py")
        return False
    
    if not os.path.exists("movies_popular_1500_complete.json"):
        print("❌ Données source non trouvées!")
        print("Lancez: python3 collect_1500_popular.py")
        return False
    
    return True

def main():
    print("🚀 Lancement VibeFilms Production (1500 films)")
    
    if not check_database():
        sys.exit(1)
    
    print("✅ Base de production détectée")
    print("🌐 Démarrage du serveur sur http://localhost:8002")
    
    # Import et lancement de l'app
    import main
    
if __name__ == "__main__":
    main()
