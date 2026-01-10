# Setup Scripts

Scripts for setting up and managing MyFinGPT-POC-V2 components.

## Scripts

### `setup-local.sh`
Initial setup script for local development (without Docker).

**Usage:**
```bash
./scripts/setup-local.sh
```

**What it does:**
- Checks prerequisites (Python, uv, Neo4j, LMStudio)
- Creates virtual environment
- Installs dependencies
- Creates `.env` file from template

### `start-backend-local.sh`
Start the backend server with local service checks.

**Usage:**
```bash
./scripts/start-backend-local.sh
```

**What it does:**
- Checks Neo4j connection (local or Docker)
- Checks LMStudio connection
- Checks Chroma connection (local or Docker)
- Starts backend server

### `check-services.sh`
Check status of all services (local and Docker).

**Usage:**
```bash
./scripts/check-services.sh
```

**What it checks:**
- Chroma status
- Neo4j status
- LMStudio status (and loaded models)
- Backend status (and health)
- Docker containers status

### `start-chroma-local.sh`
Start ChromaDB server locally using the virtual environment.

**Usage:**
```bash
./scripts/start-chroma-local.sh
```

**What it does:**
- Checks if virtual environment exists
- Checks if chromadb is installed
- Reads `CHROMA_DATA_PATH` from `.env` (default: `./data/chroma`)
- Creates data directory if needed
- Starts ChromaDB server on configured port (default: 8001)

**Data Storage:**
- Data is stored in `data/chroma/` under project root by default
- Configure custom path via `CHROMA_DATA_PATH` in `.env`

## Local Development Setup

For local development, you can run components on your laptop:

1. **Neo4j**: Install Neo4j Desktop or Community Edition locally
2. **LMStudio**: Install LMStudio and load a model
3. **Chroma**: Use Docker (`docker-compose up -d chroma`) or install locally
4. **Backend**: Run locally using the scripts above

See main README.md for detailed setup instructions.

