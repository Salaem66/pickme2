# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Server
```bash
# Development server with fallback mode
python3 run_production.py

# Direct access to static interfaces (Vercel deployment):
# - Default (tech): http://localhost/
# - Modern: http://localhost/modern  
# - Classic: http://localhost/classic
# - Tinder-style: http://localhost/tinder
# - API search: /api/search.py (serverless function)
```

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Install Vercel-optimized dependencies (lighter)
pip install -r requirements-vercel.txt
```

### Database Setup

#### Supabase (Production - Current)
```bash
# Create Supabase tables (run once)
python3 create_supabase_tables.py

# Check database status via MCP (requires .mcp.json configuration)
# Supabase project: utzflwmghpojlsthyuqf
```

#### ChromaDB (Legacy)
```bash
# Legacy setup: collect 500 enhanced movies and migrate to ChromaDB
python3 collect_500_enhanced.py
python3 migrate_enhanced_to_chromadb.py

# Test collection before full setup
python3 test_collection.py

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

### Deployment Architecture
VibeFilms is designed for serverless deployment on Vercel with Supabase as the backend:
- **Static files**: HTML interfaces served directly via Vercel rewrites (`vercel.json`)
- **Serverless API**: `/api/search.py` handles movie search requests 
- **Vector database**: Supabase with pgvector extension for semantic search
- **Fallback mode**: Local development support without Supabase

### Core Components

- **api/search.py**: Serverless function for movie search with Supabase vector engine
- **run_production.py**: Production server launcher with database validation
- **supabase_client.py**: Supabase client with vector search capabilities  
- **tmdb_client.py**: TMDB API client for movie data collection
- **data_collector.py**: Movie data collection utilities
- **static/*.html**: Frontend interfaces (tech, modern, classic, tinder styles)

### Search Engine Evolution
The project contains multiple search engine versions representing architectural evolution:
- **SupabaseVectorEngine** (current): Serverless vector search with Supabase pgvector
- **chroma_vector_engine.py**: ChromaDB-based vector search (legacy)
- **ultra_enhanced_engine.py**: Advanced semantic analysis with emotion detection
- **advanced_search_engine.py**: Full semantic analysis with mood detection
- **hybrid_search_engine.py**: Hybrid semantic + metadata search
- **streaming_vector_engine.py**: Focused on streaming availability
- **enhanced_vector_engine.py**: Enhanced with better embeddings 
- **vector_engine.py**: Basic vector search (original)

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
- **Supabase**: Vector database with pgvector extension (project: utzflwmghpojlsthyuqf)
- **MCP Integration**: Supabase MCP server configured in `.mcp.json` for database operations
- **TMDB API**: Requires TMDB_API_KEY in .env file (already configured)
- **Models**: 
  - Production: `all-MiniLM-L6-v2` (lightweight for Vercel)
  - Legacy: `all-mpnet-base-v2` (higher quality, larger)
- **Dependencies**: 
  - Vercel: `requirements-vercel.txt` (optimized for serverless)
  - Local: `requirements.txt` (full dependencies)
- **Database**: Supabase with vector embeddings for ~500 movies

### Current Architecture (Production)
- **api/search.py**: Serverless search function with SupabaseVectorEngine
- **supabase_client.py**: Supabase client with vector search and user features
- **create_supabase_tables.py**: Database schema setup for movies and user interactions
- **Enhanced user features**: Wishlist, ratings, "not interested" filtering
- **Vercel deployment**: Static interfaces with serverless API backend
- **Legacy ChromaDB**: Various collection and migration scripts for reference

### Production Features
- **Real TMDB Data**: ~500 popular movies with verified information
- **Streaming Integration**: Netflix, Disney+, Amazon Prime, HBO Max availability  
- **Enhanced Metadata**: Cast, directors, ratings, budgets, countries
- **Semantic Search**: Vector similarity with configurable thresholds
- **User Features**: Authentication, watchlist, ratings, personalized filtering
- **Serverless Architecture**: Optimized for Vercel deployment with cold start mitigation

### File Patterns
- `*.json`: Movie datasets from TMDB (enhanced_movies_*.json, etc.)
- `collect_*.py`: Data collection scripts
- `static/*.html`: Frontend interfaces (tech, modern, classic, tinder)
- `*_engine.py`: Search engine implementations (legacy and current)
- `requirements*.txt`: Dependencies (standard vs Vercel-optimized)
- `*_client.py`: API clients (TMDB, Supabase)

### Development Notes
- **MCP Integration**: Use Supabase MCP commands for database operations
- **Vercel Deployment**: Configured via `vercel.json` with static file rewrites
- **Fallback Mode**: Local development works without Supabase (limited functionality)
- **User System**: Complete authentication and user interaction tracking ready
- **Performance**: Optimized for serverless with lazy model loading and lightweight dependencies