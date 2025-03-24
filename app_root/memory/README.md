# Memory System for KDE AI Interface

This directory contains the memory integration components for the KDE AI Interface, providing both short-term and long-term memory capabilities for a more contextually aware AI assistant.

## Components

- **memory_integration.py**: Main integration interface for the memory system
- **structured_storage.py**: PostgreSQL and Redis integration for structured data storage
- **embeddings.py**: Vector embeddings provider for semantic search
- **memory_manager.py**: (Located in `../rag/`) Manages both short and long-term memory

## Features

### Short-Term Memory
- Maintains the current conversation context
- Enhances assistant responses with relevant context
- Persists across individual chat sessions

### Long-Term Memory
- Stores and retrieves semantic information using vector embeddings
- Supports multiple vector database backends:
  - Qdrant (recommended for production)
  - ChromaDB (simpler alternative)
  - JSON (fallback for development)
- Enables the assistant to recall information from past conversations

### Structured Storage
- PostgreSQL for persistent structured data
- Redis for caching and real-time data
- JSON fallback for development environments

## Setup Instructions

### Vector Database Setup

#### Option 1: Qdrant (Recommended)

1. Install Qdrant using Docker:
```bash
docker run -p 6333:6333 -p 6334:6334 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant
```

2. Or install from PyPI for local development:
```bash
pip install qdrant-client
```

#### Option 2: ChromaDB (Simpler Alternative)

```bash
pip install chromadb
```

### PostgreSQL Setup

1. Install PostgreSQL:
```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib

# Fedora/RHEL
sudo dnf install postgresql-server postgresql-contrib
```

2. Create a database for the KDE AI Interface:
```bash
sudo -u postgres createdb kde_ai_interface
sudo -u postgres createuser -P <username>
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE kde_ai_interface TO <username>;"
```

### Redis Setup (Optional)

1. Install Redis:
```bash
# Ubuntu/Debian
sudo apt install redis-server

# Fedora/RHEL
sudo dnf install redis
```

2. Start Redis service:
```bash
sudo systemctl start redis
```

## Configuration

Configuration can be done through the unified_ai_gui.py interface in the Settings dialog, under the "Memory" tab.

### Environment Variables

You can also set the following environment variables:

```bash
# Vector Database
export VECTOR_DB_TYPE=qdrant  # Options: qdrant, chromadb, json
export VECTOR_DB_URL=http://localhost:6333  # For Qdrant
export VECTOR_DB_CLOUD=false  # For cloud-hosted instances

# PostgreSQL
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=kde_ai_interface
export POSTGRES_USER=youruser
export POSTGRES_PASSWORD=yourpassword

# Redis
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_DB=0
export REDIS_PASSWORD=''  # Leave empty if no password
```

## Integration with External Tools

The memory system is designed to integrate with:

1. **MCP Servers**: For desktop context and tool capabilities
2. **AMD Ryzen AI**: For optimized embedding generation
3. **Quark Server**: For quantized model inference

## Development

To extend the memory system:

1. Add new vector database support in `../rag/indexer.py`
2. Add new structured storage backend in `structured_storage.py`
3. Add new embedding models in `../rag/embeddings.py`

## Debugging

Enable debug logs by setting the environment variable:

```bash
export LOG_LEVEL=DEBUG
```

Memory logs are stored in:
```
~/.local/share/kde-ai-interface/logs/
```