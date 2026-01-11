# Backend - MyFinGPT-POC-V2

Backend implementation for the multi-agent financial analysis system.

## Structure

```
backend/
├── src/                    # Source code
│   ├── api/               # API routes and middleware
│   ├── agents/           # Agent implementations (Phase 2+)
│   ├── config.py         # Configuration management
│   ├── exceptions.py     # Custom exceptions
│   ├── graph_db/         # Neo4j client
│   ├── main.py           # FastAPI application entry point
│   ├── models/           # Data models
│   ├── mcp/              # MCP client (Phase 2+)
│   ├── orchestrator/     # LangGraph orchestration (Phase 2+)
│   ├── services/         # Business logic services
│   ├── utils/            # Utility functions
│   └── vector_db/        # Chroma client
├── tests/                 # Test files
├── scripts/              # Utility scripts
├── requirements.txt       # Production dependencies
├── requirements-dev.txt  # Development dependencies
├── pyproject.toml        # Python project configuration
└── Dockerfile            # Docker image definition
```

## Setup

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- Docker and Docker Compose (for databases)

### Installation

1. **Create virtual environment:**
   ```bash
   # Using uv (recommended)
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   
   # Or using standard Python
   python3.12 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   # Using uv
   uv pip install -r requirements.txt
   uv pip install -r requirements-dev.txt
   
   # Or using pip
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

3. **Configure environment:**
   ```bash
   cp ../.env.example ../.env
   # Edit ../.env with your configuration
   ```

4. **Start databases:**
   ```bash
   # From project root
   docker-compose up -d chroma neo4j
   ```

## Running

### Development Server

```bash
# From backend directory
python -m src.main

# Or with uvicorn directly
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_specific.py -v
```

## Code Quality

### Linting and Formatting

```bash
# Format code with Black
black src/ tests/

# Lint with Ruff
ruff check src/ tests/

# Type checking with mypy
mypy src/
```

### Pre-commit Hooks

Install pre-commit hooks:
```bash
pip install pre-commit
pre-commit install
```

This will automatically run Black, Ruff, and other checks before commits.

## Development

### Adding New Dependencies

1. **Production dependencies:** Add to `requirements.txt`
2. **Development dependencies:** Add to `requirements-dev.txt`

### Project Configuration

- **Code formatting:** Configured in `pyproject.toml` (Black, Ruff, mypy)
- **Environment variables:** See `.env.example` in project root
- **Application settings:** See `src/config.py`

## Phase Status

- ✅ **Phase 0**: Foundation and Setup
- ✅ **Phase 1**: Core Infrastructure
- ⏳ **Phase 2**: Basic Agent System (Next)
- ⏳ **Phase 3+**: Future phases

## API Endpoints

### Health Check
- `GET /health/` - Health check endpoint

### Authentication
- `POST /auth/session` - Create session (requires `X-API-Key` header)
- `GET /auth/status` - Get session status (requires `X-Session-ID` header)

## Database Connections

- **Chroma**: Vector database for semantic search (Phase 4+)
- **Neo4j**: Graph database for knowledge graph (Phase 4+)

Both databases are configured via environment variables and can run in Docker or locally.

## Troubleshooting

### Database Connection Issues

1. Verify databases are running:
   ```bash
   docker-compose ps
   ```

2. Check database health:
   ```bash
   curl http://localhost:8001/api/v1/heartbeat  # Chroma
   curl http://localhost:7474  # Neo4j browser
   ```

3. Verify environment variables in `.env` file

### Import Errors

Ensure you're running from the backend directory or have the project root in your Python path:
```bash
export PYTHONPATH="${PYTHONPATH}:/path/to/MyFinGPT2-POC/backend"
```
