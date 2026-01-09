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

## Component Management

### Databases (Chroma & Neo4j)

**Start:**
```bash
docker-compose up -d chroma neo4j
# Or start individually:
docker-compose up -d chroma
docker-compose up -d neo4j
```

**Stop:**
```bash
docker-compose stop chroma neo4j
# Or stop individually:
docker-compose stop chroma
docker-compose stop neo4j
```

**Restart:**
```bash
docker-compose restart chroma neo4j
# Or restart individually:
docker-compose restart chroma
docker-compose restart neo4j
```

**Verify:**
```bash
# Check status
docker-compose ps

# Check logs
docker-compose logs chroma
docker-compose logs neo4j

# Test connections
curl http://localhost:8001/api/v1/heartbeat  # Chroma
curl http://localhost:7474  # Neo4j browser (HTTP)
```

### Backend (FastAPI)

**Start:**
```bash
cd backend
source .venv/bin/activate  # Activate virtual environment
python -m src.main
# Or with auto-reload:
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**Stop:**
```bash
# Press Ctrl+C in the terminal running the backend
```

**Restart:**
```bash
# Stop (Ctrl+C) then start again with the start command above
```

**Verify:**
```bash
# Health check
curl http://localhost:8000/health/

# Expected response:
# {"status":"healthy","timestamp":"...","services":{"chroma":"connected","neo4j":"connected"}}
```

### All Components

**Start all:**
```bash
# Start databases first
docker-compose up -d chroma neo4j

# Then start backend (in separate terminal)
cd backend && source .venv/bin/activate && python -m src.main
```

**Stop all:**
```bash
# Stop backend (Ctrl+C)
# Stop databases
docker-compose stop chroma neo4j
```

**Restart all:**
```bash
# Restart databases
docker-compose restart chroma neo4j

# Restart backend (stop and start again)
```

**Verify all:**
```bash
# Check database containers
docker-compose ps

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

Run tests:
```bash
pytest tests/
```

## Documentation

See `docs/` directory for detailed documentation:
- `docs/requirements.md` - System requirements
- `docs/IMPLEMENTATION_PLAN.md` - Phased implementation plan
- `docs/components/` - Component definitions

