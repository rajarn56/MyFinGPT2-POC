# MyFinGPT-POC-V2

Production-grade multi-agent financial analysis system.

## Project Structure

```
MyFinGPT2-POC/
├── backend/              # Backend Python code
│   ├── src/
│   ├── tests/
│   └── requirements.txt
├── frontend/             # Frontend React/TypeScript code (to be implemented)
├── docs/                 # Documentation
├── config/               # Configuration files
├── scripts/              # Utility scripts
└── docker-compose.yml    # Docker configuration
```

## Phase 1: Core Infrastructure

This phase implements:
- Chroma vector database connection
- Neo4j graph database connection
- FastAPI application structure
- Session-based authentication
- Structured logging
- Error handling framework

## Setup

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer
- Docker and Docker Compose
- Node.js 18+ (for frontend, Phase 7)

### Installing uv

Install uv using one of the following methods:

```bash
# Using curl (Unix/macOS)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Using pip
pip install uv

# Using homebrew (macOS)
brew install uv
```

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment and install dependencies:
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

Alternatively, you can use uv's sync command (if using pyproject.toml):
```bash
uv sync
```

3. Copy environment file:
```bash
cp ../.env.example ../.env
# Edit .env with your configuration
```

4. Start databases with Docker Compose:
```bash
docker-compose up -d chroma neo4j
```

5. Run the backend:
```bash
python -m src.main
# Or: uvicorn src.main:app --reload
```

The API will be available at `http://localhost:8000`

## Local Development Setup (Without Docker)

For development, you can run components locally on your laptop instead of using Docker.

### Prerequisites for Local Setup

- **Neo4j Desktop** or **Neo4j Community Edition** installed locally
- **LMStudio** installed and running with a model loaded
- **Chroma** (can use Docker or install locally)

### Quick Setup Script

```bash
# Run the setup script
./scripts/setup-local.sh
```

This script will:
- Check prerequisites (Python, uv, Neo4j, LMStudio)
- Create virtual environment
- Install dependencies
- Create `.env` file from template

### Manual Local Setup

1. **Install Neo4j locally:**
   - Download [Neo4j Desktop](https://neo4j.com/download/) or [Neo4j Community Edition](https://neo4j.com/deployment-center/)
   - Start Neo4j and note the connection details (URI, username, password)

2. **Install and start LMStudio:**
   - Download [LMStudio](https://lmstudio.ai/)
   - Start LMStudio and load:
     - **LLM Model**: For agent responses (e.g., llama-2-7b-chat)
     - **Embedding Model**: For vector search (e.g., text-embedding-ada-002 or your embedding model)
   - Start the local server (default port: 1234)
   - Note the API endpoint (default: `http://localhost:1234/v1`)

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env and set:
   # - NEO4J_URI=bolt://localhost:7687 (or your Neo4j URI)
   # - NEO4J_USER=neo4j (or your username)
   # - NEO4J_PASSWORD=your_password
   # - LM_STUDIO_API_BASE=http://localhost:1234/v1
   # - LM_STUDIO_MODEL=your-llm-model-name
   # - EMBEDDING_PROVIDER=lmstudio  # Optional: use different provider for embeddings
   # - EMBEDDING_MODEL=your-embedding-model-name  # Required for LMStudio embeddings
   # - CHROMA_DATA_PATH=./data/chroma  # Local ChromaDB data path (default)
   ```

4. **Start ChromaDB (if using local ChromaDB instead of Docker):**
   ```bash
   # Option A: Use convenience script (recommended)
   # Folder: Project root (MyFinGPT2-POC/)
   ./scripts/start-chroma-local.sh
   
   # Option B: Manual start
   # Folder: Project root (MyFinGPT2-POC/)
   cd backend
   source .venv/bin/activate
   cd ..
   chroma run --path ./data/chroma --port 8001
   ```

5. **Start backend:**
   ```bash
   ./scripts/start-backend-local.sh
   # Or manually:
   cd backend
   source .venv/bin/activate
   python -m src.main
   ```

### Verify Local Services

```bash
# Check all services status
./scripts/check-services.sh

# Or check individually:
# Neo4j
neo4j status  # If using Neo4j Desktop CLI
# Or check connection:
nc -z localhost 7687

# LMStudio
curl http://localhost:1234/v1/models

# Chroma (if running locally or Docker)
curl http://localhost:8001/api/v1/heartbeat

# Backend
curl http://localhost:8000/health/
```

### Local Component Management

**Neo4j (Local):**
```bash
# Start (Neo4j Desktop)
# Use Neo4j Desktop GUI to start database
# (No folder context needed - GUI application)

# Start (Neo4j Community Edition)
# Folder: Any (system command)
neo4j start

# Stop
# Folder: Any (system command)
neo4j stop

# Status
# Folder: Any (system command)
neo4j status
```

**LMStudio:**
```bash
# Start: Use LMStudio GUI application
# Load TWO models in LMStudio:
#   1. LLM Model: For agent responses (set in LM_STUDIO_MODEL)
#   2. Embedding Model: For vector search (set in EMBEDDING_MODEL)
# Start the local server (usually port 1234)
# API will be available at http://localhost:1234/v1
# (No folder context needed - GUI application)

# Verify:
# Folder: Any
curl http://localhost:1234/v1/models
```

**Chroma (Local - Optional):**
```bash
# Option 1: Use Docker (recommended)
# Folder: Project root (MyFinGPT2-POC/)
docker-compose up -d chroma

# Option 2: Install and run locally in virtual environment
# Step 1: Install ChromaDB (if not already installed)
# Folder: Project root (MyFinGPT2-POC/)
cd backend
source .venv/bin/activate
pip install chromadb
cd ..

# Step 2: Start ChromaDB server
# Option A: Use convenience script (recommended)
# Folder: Project root (MyFinGPT2-POC/)
./scripts/start-chroma-local.sh

# Option B: Manual start
# Folder: Project root (MyFinGPT2-POC/)
source backend/.venv/bin/activate
chroma run --path ./data/chroma --port 8001
```

**Chroma Data Folder:**
- **Default location**: `data/chroma/` under project root (MyFinGPT2-POC/data/chroma/)
- This folder is **shared and persistent** across ChromaDB restarts
- The folder will be **created automatically** if it doesn't exist
- To use a different location, set `CHROMA_DATA_PATH` in `.env`:
  ```
  CHROMA_DATA_PATH=./data/chroma
  ```
- The data folder contains all ChromaDB collections and is **safe to backup/share**

**Backend (Local):**
```bash
# Start
# Folder: Project root (MyFinGPT2-POC/)
./scripts/start-backend-local.sh

# Stop
# Folder: Terminal running backend (Press Ctrl+C)

# Restart
# Folder: Project root (MyFinGPT2-POC/)
# Stop then start again
```

### Mixed Setup (Some Docker, Some Local)

You can mix Docker and local components:

```bash
# Folder: Project root (MyFinGPT2-POC/)
# Example: Use Docker for Chroma, local for Neo4j and LMStudio
docker-compose up -d chroma  # Chroma in Docker
# Neo4j and LMStudio running locally
./scripts/start-backend-local.sh  # Backend connects to all
```

## Component Management

### Databases (Chroma & Neo4j)

**Start:**
```bash
# Folder: Project root (MyFinGPT2-POC/)
docker-compose up -d chroma neo4j
# Or start individually:
docker-compose up -d chroma
docker-compose up -d neo4j
```

**Stop:**
```bash
# Folder: Project root (MyFinGPT2-POC/)
docker-compose stop chroma neo4j
# Or stop individually:
docker-compose stop chroma
docker-compose stop neo4j
```

**Restart:**
```bash
# Folder: Project root (MyFinGPT2-POC/)
docker-compose restart chroma neo4j
# Or restart individually:
docker-compose restart chroma
docker-compose restart neo4j
```

**Verify:**
```bash
# Folder: Project root (MyFinGPT2-POC/)
# Check status
docker-compose ps

# Check logs
docker-compose logs chroma
docker-compose logs neo4j

# Test connections
# Folder: Any
curl http://localhost:8001/api/v1/heartbeat  # Chroma
curl http://localhost:7474  # Neo4j browser (HTTP)
```

### Backend (FastAPI)

**Start:**
```bash
# Folder: Project root (MyFinGPT2-POC/)
cd backend
source .venv/bin/activate  # Activate virtual environment
python -m src.main
# Or with auto-reload:
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**Stop:**
```bash
# Folder: Terminal running backend (Press Ctrl+C)
```

**Restart:**
```bash
# Folder: Project root (MyFinGPT2-POC/)
# Stop (Ctrl+C) then start again with the start command above
```

**Verify:**
```bash
# Folder: Any
# Health check
curl http://localhost:8000/health/

# Expected response:
# {"status":"healthy","timestamp":"...","services":{"chroma":"connected","neo4j":"connected"}}
```

### All Components

**Start all:**
```bash
# Folder: Project root (MyFinGPT2-POC/)
# Start databases first
docker-compose up -d chroma neo4j

# Then start backend (in separate terminal)
# Folder: Project root (MyFinGPT2-POC/)
cd backend && source .venv/bin/activate && python -m src.main
```

**Stop all:**
```bash
# Folder: Project root (MyFinGPT2-POC/)
# Stop backend (Ctrl+C)
# Stop databases
docker-compose stop chroma neo4j
```

**Restart all:**
```bash
# Folder: Project root (MyFinGPT2-POC/)
# Restart databases
docker-compose restart chroma neo4j

# Restart backend (stop and start again)
```

**Verify all:**
```bash
# Folder: Project root (MyFinGPT2-POC/)
# Check database containers
docker-compose ps

# Folder: Any
# Check backend health
curl http://localhost:8000/health/

# Check individual services
curl http://localhost:8001/api/v1/heartbeat  # Chroma
curl http://localhost:7474  # Neo4j
```

### API Endpoints

- `GET /health/` - Health check endpoint
- `POST /auth/session` - Create session (requires X-API-Key header)
- `GET /auth/status` - Get session status (requires X-Session-ID header)

### Testing

**Run unit tests:**
```bash
pytest tests/
```

**Test LMStudio connectivity:**
```bash
# Test LLM and embedding models
cd backend
source .venv/bin/activate
python scripts/test_lmstudio.py

# This verifies:
# - LMStudio server is accessible
# - LLM model is loaded and working
# - Embedding model is configured and working
# - Both models are ready for use
```

**Important: Embedding Model Configuration**
- The system requires an **embedding model** for semantic search (Phase 4+)
- For LMStudio, you must load **two separate models**:
  1. **LLM Model**: Set in `LM_STUDIO_MODEL` (for agent responses)
  2. **Embedding Model**: Set in `EMBEDDING_MODEL` (for vector search)
- Both models must be loaded in LMStudio before starting the backend
- Run the test script to verify both models are working correctly

## Documentation

See `docs/` directory for detailed documentation:
- `docs/requirements.md` - System requirements
- `docs/IMPLEMENTATION_PLAN.md` - Phased implementation plan
- `docs/components/` - Component definitions

