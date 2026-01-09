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

## Local Development Setup

For local development, you can run components on your laptop:

1. **Neo4j**: Install Neo4j Desktop or Community Edition locally
2. **LMStudio**: Install LMStudio and load a model
3. **Chroma**: Use Docker (`docker-compose up -d chroma`) or install locally
4. **Backend**: Run locally using the scripts above

See main README.md for detailed setup instructions.

