#!/usr/bin/env python3
"""
Migration complète des données vers Supabase Vector
Utilise directement les fonctions MCP pour insérer films et embeddings
"""

import json
import sys
import os
from typing import List, Dict, Any

def read_embeddings_data():
    """Lit les données d'embeddings générées"""
    try:
        with open('embeddings_data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ embeddings_data.json non trouvé. Exécutez d'abord migrate_movies_batch.py")
        return []

def create_embedding_insert_sql(embeddings_batch: List[Dict], movie_ids_mapping: Dict[int, int]):
    """Crée le SQL pour insérer un batch d'embeddings"""
    if not embeddings_batch:
        return ""
    
    sql_parts = ["INSERT INTO movie_embeddings (movie_id, embedding, embedding_text) VALUES"]
    
    values = []
    for emb_data in embeddings_batch:
        tmdb_id = emb_data['tmdb_id']
        if tmdb_id in movie_ids_mapping:
            movie_id = movie_ids_mapping[tmdb_id]
            
            # Convertir l'embedding en format PostgreSQL array
            embedding_array = str(emb_data['embedding']).replace("'", "")
            
            # Échapper les apostrophes dans le texte
            embedding_text = emb_data['embedding_text'].replace("'", "''")
            
            value = f"({movie_id}, ARRAY{embedding_array}, '{embedding_text}')"
            values.append(value)
    
    if not values:
        return ""
    
    sql_parts.append(', '.join(values))
    sql_parts.append("RETURNING id, movie_id;")
    
    return ' '.join(sql_parts)

def main():
    print("🚀 Migration complète vers Supabase Vector")
    print("=" * 50)
    
    # Lire les embeddings
    embeddings_data = read_embeddings_data()
    if not embeddings_data:
        return
    
    print(f"📊 {len(embeddings_data)} embeddings à traiter")
    
    # Mapping des TMDB IDs vers les IDs Supabase (à compléter manuellement)
    # Basé sur les résultats des insertions précédentes
    movie_ids_mapping = {
        755898: 1,   # War of the Worlds (existait déjà)
        986206: 3,   # Night Carnage
        1087192: 4,  # How to Train Your Dragon
        1100988: 5,  # 28 Years Later
        715253: 6,   # Phantom
        552524: 7,   # Lilo & Stitch
        1071585: 8,  # M3GAN 2.0
        1263256: 9,  # Happy Gilmore 2
        1181540: 10, # Guns Up
        1119878: 11  # Ice Road: Vengeance
    }
    
    print("⚠️  ÉTAPES À SUIVRE :")
    print("1. Insérez manuellement les 4 batches restants via MCP")
    print("2. Notez les IDs retournés pour compléter le mapping")
    print("3. Utilisez ce script pour générer les SQL d'embeddings")
    
    # Générer les SQL d'embeddings pour les films déjà insérés
    available_embeddings = [emb for emb in embeddings_data if emb['tmdb_id'] in movie_ids_mapping]
    
    if available_embeddings:
        print(f"\n📝 Génération SQL pour {len(available_embeddings)} embeddings disponibles...")
        
        # Créer par batches de 5 pour éviter les timeouts
        batch_size = 5
        embedding_sqls = []
        
        for i in range(0, len(available_embeddings), batch_size):
            batch = available_embeddings[i:i + batch_size]
            sql = create_embedding_insert_sql(batch, movie_ids_mapping)
            if sql:
                embedding_sqls.append(sql)
        
        # Sauvegarder les SQL d'embeddings
        with open('embeddings_sql.sql', 'w', encoding='utf-8') as f:
            for i, sql in enumerate(embedding_sqls):
                f.write(f"-- Embeddings Batch {i+1}\n")
                f.write(sql)
                f.write("\n\n")
        
        print(f"✅ {len(embedding_sqls)} SQL d'embeddings générés dans embeddings_sql.sql")
    
    # Instruction pour la recherche de test
    print("\n🧪 POUR TESTER LA RECHERCHE :")
    print("1. Exécutez d'abord tous les SQL d'embeddings")
    print("2. Testez avec cette requête :")
    print("""
    SELECT m.title, m.genres, similarity 
    FROM match_movies(
        ARRAY[0.1, 0.2, 0.3, ...]::vector(768),  -- embedding de test
        0.5, 
        5
    ) 
    JOIN movies m ON m.id = movie_id 
    ORDER BY similarity DESC;
    """)

if __name__ == "__main__":
    main()