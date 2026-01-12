# MyFinGPT-POC-V2

Production-grade multi-agent financial analysis system.

## Project Structure

```
MyFinGPT2-POC/
├── backend/              # Backend Python code
│   ├── src/
│   ├── tests/
│   └── requirements.txt
├── frontend/             # Frontend React/TypeScript code (Phase 7 - Complete)
├── docs/                 # Documentation
├── config/               # Configuration files
├── scripts/              # Utility scripts
└── docker-compose.yml    # Docker configuration
```

## Implementation Status

**Completed Phases:** 0-7 (Foundation through Frontend Implementation)

**Current Phase:** Phase 7 - Frontend Implementation ✅

### Phase Summary

- **Phase 0**: Foundation and Setup
- **Phase 1**: Core Infrastructure (Chroma, Neo4j, FastAPI, Auth, Logging)
- **Phase 2**: Basic Agent System (Research Agent, MCP Integration)
- **Phase 3**: Core Agents and Orchestration (Analyst, Reporting, Parallel Execution)
- **Phase 4**: Knowledge Layer (Vector Search, Ingestion, Neo4j Schema)
- **Phase 5**: EDGAR Integration (Hybrid Search, SEC Filing Processing)
- **Phase 6**: Advanced Agents (Comparison, Trend Analysis, Conditional Routing)
- **Phase 7**: Frontend Implementation (React UI, Chat Interface, Analysis Panel)

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

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. (Optional) Configure environment variables:
```bash
# Create .env file in frontend directory (optional)
# Defaults are used if not specified:
# VITE_API_BASE_URL=http://localhost:8000
# VITE_WS_BASE_URL=ws://localhost:8000
# VITE_API_KEY=key1
```

4. Start the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

**Note:** The frontend requires the backend to be running. Make sure the backend is started before accessing the frontend.

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

### Frontend (React)

**Start:**
```bash
# Folder: Project root (MyFinGPT2-POC/)
cd frontend
npm run dev
```

**Stop:**
```bash
# Folder: Terminal running frontend (Press Ctrl+C)
```

**Build for Production:**
```bash
# Folder: Project root (MyFinGPT2-POC/)
cd frontend
npm run build
```

**Preview Production Build:**
```bash
# Folder: Project root (MyFinGPT2-POC/)
cd frontend
npm run preview
```

**Verify:**
```bash
# Folder: Any
# Frontend should be accessible at:
curl http://localhost:3000
```

### All Components

**Start all:**
```bash
# Folder: Project root (MyFinGPT2-POC/)
# Step 1: Start databases
docker-compose up -d chroma neo4j

# Step 2: Start backend (in separate terminal)
# Folder: Project root (MyFinGPT2-POC/)
cd backend && source .venv/bin/activate && python -m src.main

# Step 3: Start frontend (in another terminal)
# Folder: Project root (MyFinGPT2-POC/)
cd frontend && npm run dev
```

**Stop all:**
```bash
# Folder: Project root (MyFinGPT2-POC/)
# Stop frontend (Ctrl+C in frontend terminal)
# Stop backend (Ctrl+C in backend terminal)
# Stop databases
docker-compose stop chroma neo4j
```

**Restart all:**
```bash
# Folder: Project root (MyFinGPT2-POC/)
# Restart databases
docker-compose restart chroma neo4j

# Restart backend (stop and start again)
# Restart frontend (stop and start again)
```

**Verify all:**
```bash
# Folder: Project root (MyFinGPT2-POC/)
# Check database containers
docker-compose ps

# Folder: Any
# Check backend health
curl http://localhost:8000/health/

# Check frontend
curl http://localhost:3000

# Check individual services
curl http://localhost:8001/api/v1/heartbeat  # Chroma
curl http://localhost:7474  # Neo4j
```

### API Endpoints

**Health & Authentication:**
- `GET /health/` - Health check endpoint
- `POST /auth/session` - Create session (requires X-API-Key header)
- `GET /auth/status` - Get session status (requires X-Session-ID header)

**Agents (Phase 2-6):**
- `POST /api/agents/execute` - Execute agent workflow (requires X-Session-ID header)
  - Request body: `{"query": "string", "symbols": ["AAPL", "MSFT"]}`
  - Returns: Transaction ID, status, and analysis results

**Knowledge Layer (Phase 4):**
- `POST /api/knowledge/ingest/news` - Ingest news article (requires X-Session-ID header)
- `GET /api/knowledge/search/reports` - Search reports by query (requires X-Session-ID header)
- `GET /api/knowledge/collections/stats` - Get collection statistics (requires X-Session-ID header)

**EDGAR (Phase 5):**
- `GET /api/edgar/search` - Hybrid search in EDGAR filings (requires X-Session-ID header)
  - Query parameters: `query`, `limit`, `company_ticker`, `form_type`, `semantic_type`, `use_vector`, `use_graph`

**API Documentation:**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Testing

#### Prerequisites for Testing

Before running tests, ensure:
1. **Backend is running** at `http://localhost:8000`
2. **Databases are running** (Chroma and Neo4j)
3. **LMStudio is running** with both LLM and embedding models loaded (if using LMStudio)
4. **Session is created** (for API testing)

#### Unit Tests

**Run backend unit tests:**
```bash
cd backend
source .venv/bin/activate
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

#### Connectivity Tests

**Test LMStudio connectivity:**
```bash
cd backend
source .venv/bin/activate
python scripts/test_lmstudio.py

# This verifies:
# - LMStudio server is accessible
# - LLM model is loaded and working
# - Embedding model is configured and working
# - Both models are ready for use
```

#### API Testing

**1. Health Check:**
```bash
curl http://localhost:8000/health/
```

**2. Create Session:**
```bash
curl -X POST http://localhost:8000/auth/session \
  -H "X-API-Key: key1" \
  -H "Content-Type: application/json"
```

Save the `session_id` from the response for subsequent requests.

**3. Test Agent Execution (Phase 2-6):**
```bash
# Replace SESSION_ID with the session ID from step 2
# Note: The system intelligently extracts symbols from queries, so you can use various formats:
# - "Analyze AAPL stock performance" (symbols will be extracted automatically)
# - "Tell me about Apple" (company name will be mapped to AAPL)
# - "Compare Apple and Microsoft" (both will be extracted and mapped)

curl -X POST http://localhost:8000/api/agents/execute \
  -H "X-Session-ID: SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Analyze AAPL stock performance",
    "symbols": []
  }'
# Note: Even with empty symbols array, backend will extract "AAPL" from query
```

**4. Test Knowledge Layer Search (Phase 4):**
```bash
# Replace SESSION_ID with your session ID
curl "http://localhost:8000/api/knowledge/search/reports?query=AAPL%20revenue&n_results=5" \
  -H "X-Session-ID: SESSION_ID"
```

**5. Test EDGAR Hybrid Search (Phase 5):**
```bash
# Replace SESSION_ID with your session ID
curl "http://localhost:8000/api/edgar/search?query=revenue%20growth&limit=10&company_ticker=AAPL" \
  -H "X-Session-ID: SESSION_ID"
```

**6. Test Knowledge Layer Ingestion (Phase 4):**
```bash
# Replace SESSION_ID with your session ID
curl -X POST http://localhost:8000/api/knowledge/ingest/news \
  -H "X-Session-ID: SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Apple Reports Record Revenue",
    "content": "Apple Inc. reported record quarterly revenue...",
    "symbol": "AAPL",
    "source": "Financial News",
    "url": "https://example.com/news"
  }'
```

#### Frontend Testing

**1. Start Frontend:**
```bash
cd frontend
npm run dev
```

**2. Access Frontend:**
- Open browser to `http://localhost:3000`
- The frontend should automatically create a session and connect to the backend

**3. Test Frontend Features:**

**Chat Interface:**
- Type a query in the chat input (e.g., "Analyze AAPL stock", "Tell me about Apple", "Compare Apple and Microsoft")
- The system intelligently extracts stock symbols using LLM-based parsing
- Supports various formats:
  - Stock symbols: "AAPL", "MSFT"
  - Company names: "Apple", "Microsoft", "Tesla"
  - Parenthetical notation: "Apple Inc. (AAPL)", "Microsoft (MSFT)"
  - Case variations: "aapl", "AAPL", "Apple"
- Submit the query and wait for analysis results
- If symbols aren't extracted, backend will handle extraction automatically

**Analysis Panel:**
- After submitting a query, the analysis report should appear in the right panel
- The report should include:
  - Research data (Phase 2)
  - Analyst insights (Phase 3)
  - Generated report (Phase 3)
  - EDGAR data (Phase 5, if applicable)
  - Comparison data (Phase 6, if comparison query)
  - Trend analysis (Phase 6, if trend query)
  - Citations and sources

**Session Management:**
- Session is automatically created on first load
- Session persists in localStorage
- Multiple queries in the same session should work

#### End-to-End Testing Workflow

**Complete Test Scenario:**

1. **Start all services:**
   ```bash
   # Terminal 1: Databases
   docker-compose up -d chroma neo4j
   
   # Terminal 2: Backend
   cd backend && source .venv/bin/activate && python -m src.main
   
   # Terminal 3: Frontend
   cd frontend && npm run dev
   ```

2. **Verify services:**
   ```bash
   curl http://localhost:8000/health/
   curl http://localhost:3000
   ```

3. **Test via Frontend:**
   - Open `http://localhost:3000` in browser
   - Enter query: "Compare AAPL and MSFT financial performance"
   - Submit and verify:
     - Chat messages appear
     - Analysis report appears in right panel
     - Report includes comparison data (Phase 6)
     - Citations are displayed

4. **Test via API (Alternative):**
   ```bash
   # Create session
   SESSION_ID=$(curl -s -X POST http://localhost:8000/auth/session \
     -H "X-API-Key: key1" | jq -r '.session_id')
   
   # Execute query
   curl -X POST http://localhost:8000/api/agents/execute \
     -H "X-Session-ID: $SESSION_ID" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "Analyze AAPL stock trends",
       "symbols": ["AAPL"]
     }' | jq .
   ```

#### Testing Different Query Types (Phase 6)

**Comparison Query:**
```bash
curl -X POST http://localhost:8000/api/agents/execute \
  -H "X-Session-ID: SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Compare AAPL and MSFT",
    "symbols": ["AAPL", "MSFT"]
  }'
```

**Trend Query:**
```bash
curl -X POST http://localhost:8000/api/agents/execute \
  -H "X-Session-ID: SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the trends for AAPL stock?",
    "symbols": ["AAPL"]
  }'
```

**Standard Analysis Query:**
```bash
curl -X POST http://localhost:8000/api/agents/execute \
  -H "X-Session-ID: SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Analyze AAPL financial performance",
    "symbols": ["AAPL"]
  }'
```

#### Important Configuration Notes

**Embedding Model Configuration:**
- The system requires an **embedding model** for semantic search (Phase 4+)
- For LMStudio, you must load **two separate models**:
  1. **LLM Model**: Set in `LM_STUDIO_MODEL` (for agent responses)
  2. **Embedding Model**: Set in `EMBEDDING_MODEL` (for vector search)
- Both models must be loaded in LMStudio before starting the backend
- Run the test script to verify both models are working correctly

**API Keys:**
- Default API keys are configured in `.env`: `API_KEYS=key1,key2,key3`
- Use any of these keys when creating sessions
- Frontend uses `key1` by default

**CORS Configuration:**
- Frontend runs on `http://localhost:3000` by default
- Backend CORS is configured to allow this origin
- If using a different port, update `CORS_ORIGINS` in backend `.env`

## Documentation

See `docs/` directory for detailed documentation:
- `docs/requirements.md` - System requirements
- `docs/IMPLEMENTATION_PLAN.md` - Phased implementation plan
- `docs/components/` - Component definitions

