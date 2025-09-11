# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Server
```bash
# Run main FastAPI server (port 8002)
python3 main.py

# Access interfaces:
# - Default (tech): http://localhost:8002/
# - Modern: http://localhost:8002/modern  
# - Classic: http://localhost:8002/classic
# - Tinder-style: http://localhost:8002/tinder
# - API docs: http://localhost:8002/docs
```

### ChromaDB Setup (Production)
```bash
# Production setup: collect 500 enhanced movies and migrate to ChromaDB
python3 collect_500_enhanced.py
python3 migrate_enhanced_to_chromadb.py

# Test collection before full setup
python3 test_collection.py

# Legacy: use existing migration script for 500 basic movies
python3 reset_chromadb.py

# Debug search quality
python3 debug_search.py
```

### Data Collection & Setup
```bash
# Basic setup
pip install -r requirements.txt

# Collect sample movie data (requires TMDB API key in .env)
python3 collect_sample.py

# For streaming-focused database (500 movies)
python3 filter_streaming_movies.py
python3 build_streaming_embeddings.py

# For larger popular movies database (1000 movies)
python3 collect_1000_movies.py
python3 collect_top_1000_popular.py
```

### Data Management
```bash
# Inspect and clean data
python3 inspect_and_clean_data.py
python3 clean_data_fast.py
python3 clean_platforms_only.py

# Update embeddings
python3 update_embeddings.py
```

## Architecture

### Core Components

- **main.py**: FastAPI server with multiple UI interfaces and comprehensive movie search API
- **advanced_search_engine.py**: Semantic search engine with mood detection, emotion semantics, and platform filtering
- **tmdb_client.py**: TMDB API client for movie data collection
- **data_collector.py**: Movie data collection utilities

### Search Engine Evolution
The project contains multiple search engine versions representing architectural evolution:
- **vector_engine.py**: Basic vector search
- **enhanced_vector_engine.py**: Enhanced with better embeddings 
- **streaming_vector_engine.py**: Focused on streaming availability
- **hybrid_search_engine.py**: Hybrid semantic + metadata search
- **advanced_search_engine.py**: Full semantic analysis with emotion detection (current)

### Data Pipeline
1. **Collection**: TMDB API → JSON files (sample_movies.json, streaming_movies_500.json, etc.)
2. **Processing**: Movie metadata + embeddings generation using sentence-transformers
3. **Storage**: Pickled embeddings files (.pkl) for fast loading
4. **Search**: Semantic similarity search using cosine similarity on embeddings

### Key Features
- **ChromaDB Vector Database**: Persistent, scalable vector storage with automatic indexing
- **Mood-based search**: Natural language mood queries ("je me sens nostalgique") 
- **Multi-language support**: French UI with semantic mood mapping
- **Platform filtering**: Filter by streaming platforms (Netflix, Disney+, etc.)
- **Multiple interfaces**: 4 different UI styles (tech, modern, classic, tinder)
- **Advanced semantics**: Emotion detection, query expansion, genre boosting

### Environment Setup
- **ChromaDB Production**: Vector database stored in `./chroma_db_production/` directory
- **TMDB API**: Requires TMDB_API_KEY in .env file (already configured)
- **Model**: Uses sentence-transformers "all-mpnet-base-v2" for embeddings
- **Dependencies**: FastAPI, ChromaDB, sentence-transformers, pandas
- **Database Size**: 492 unique movies with complete metadata

### Current Architecture (Production)
- **chroma_vector_engine.py**: Main vector search engine using ChromaDB
- **collect_500_enhanced.py**: Production data collection with full metadata (streaming, cast, ratings)
- **migrate_enhanced_to_chromadb.py**: Production migration script with deduplication
- **main.py**: Configured for production database (`vibefilms_production`)
- **Legacy scripts**: Various collection and migration scripts for reference

### Production Features
- **Real TMDB Data**: 492 popular movies with verified information
- **Streaming Integration**: Netflix, Disney+, Amazon Prime, HBO Max availability
- **Enhanced Metadata**: Cast, directors, ratings, budgets, countries
- **Quality Search**: Semantic search with 0.6-0.8 similarity scores
- **Genre Coverage**: Action (180), Drama (164), Comedy (113), Horror (77), etc.

### File Patterns
- `*_embeddings.pkl`: Cached embeddings for different movie datasets
- `*.json`: Movie datasets from TMDB
- `collect_*.py`: Data collection scripts
- `static/*.html`: Frontend interfaces
- `*_engine.py`: Search engine implementations