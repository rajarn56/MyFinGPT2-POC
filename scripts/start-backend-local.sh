#!/bin/bash
# Start backend for local development

set -e

# Navigate to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Error: .env file not found. Run ./scripts/setup-local.sh first."
    exit 1
fi

# Navigate to backend
cd backend || exit 1

# Activate virtual environment
if [ ! -d ".venv" ]; then
    echo "Error: Virtual environment not found. Run ./scripts/setup-local.sh first."
    exit 1
fi

source .venv/bin/activate

# Check if Neo4j is accessible
echo "Checking Neo4j connection..."
NEO4J_URI=$(grep "^NEO4J_URI=" ../.env | cut -d '=' -f2 | tr -d '"' || echo "bolt://localhost:7687")
if [[ "$NEO4J_URI" == bolt://* ]]; then
    NEO4J_HOST=$(echo "$NEO4J_URI" | sed 's|bolt://||' | cut -d ':' -f1)
    NEO4J_PORT=$(echo "$NEO4J_URI" | sed 's|bolt://||' | cut -d ':' -f2)
    if ! nc -z "$NEO4J_HOST" "$NEO4J_PORT" 2>/dev/null; then
        echo "Warning: Cannot connect to Neo4j at $NEO4J_URI"
        echo "Make sure Neo4j is running locally or update NEO4J_URI in .env"
    else
        echo "✓ Neo4j connection OK"
    fi
fi

# Check if LMStudio is accessible
echo "Checking LMStudio connection..."
LM_STUDIO_API_BASE=$(grep "^LM_STUDIO_API_BASE=" ../.env | cut -d '=' -f2 | tr -d '"' || echo "http://localhost:1234/v1")
LM_STUDIO_HOST=$(echo "$LM_STUDIO_API_BASE" | sed 's|http://||' | sed 's|/v1||' | cut -d ':' -f1)
LM_STUDIO_PORT=$(echo "$LM_STUDIO_API_BASE" | sed 's|http://||' | sed 's|/v1||' | cut -d ':' -f2 || echo "1234")
if ! curl -s "http://$LM_STUDIO_HOST:$LM_STUDIO_PORT/v1/models" >/dev/null 2>&1; then
    echo "Warning: Cannot connect to LMStudio at $LM_STUDIO_API_BASE"
    echo "Make sure LMStudio is running and models are loaded"
else
    echo "✓ LMStudio connection OK"
    # Check if embedding model is configured
    EMBEDDING_MODEL=$(grep "^EMBEDDING_MODEL=" ../.env | cut -d '=' -f2 | tr -d '"' || echo "")
    if [ -z "$EMBEDDING_MODEL" ]; then
        echo "⚠️  Warning: EMBEDDING_MODEL not set in .env"
        echo "   Set EMBEDDING_MODEL to your embedding model name for vector search support"
    else
        echo "✓ Embedding model configured: $EMBEDDING_MODEL"
    fi
fi

# Check if Chroma is accessible (if using local Chroma)
CHROMA_HOST=$(grep "^CHROMA_HOST=" ../.env | cut -d '=' -f2 | tr -d '"' || echo "localhost")
CHROMA_PORT=$(grep "^CHROMA_PORT=" ../.env | cut -d '=' -f2 | tr -d '"' || echo "8001")
CHROMA_DATA_PATH=$(grep "^CHROMA_DATA_PATH=" ../.env | cut -d '=' -f2 | tr -d '"' || echo "./data/chroma")
if ! curl -s "http://$CHROMA_HOST:$CHROMA_PORT/api/v1/heartbeat" >/dev/null 2>&1; then
    echo "Warning: Cannot connect to Chroma at $CHROMA_HOST:$CHROMA_PORT"
    echo "Options:"
    echo "  1. Start Chroma with Docker: docker-compose up -d chroma"
    echo "  2. Start local ChromaDB server (recommended):"
    echo "     cd .. && ./scripts/start-chroma-local.sh"
    echo "  3. Manual start:"
    echo "     cd .. && source backend/.venv/bin/activate"
    echo "     chroma run --path $CHROMA_DATA_PATH --port $CHROMA_PORT"
    echo "     (Data will be stored in: $CHROMA_DATA_PATH)"
else
    echo "✓ Chroma connection OK"
fi

echo ""
echo "Starting backend server..."
echo "API will be available at http://localhost:8000"
echo "Press Ctrl+C to stop"
echo ""

# Run the backend
python -m src.main

