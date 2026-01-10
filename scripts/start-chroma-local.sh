#!/bin/bash
# Start ChromaDB server locally

set -e

# Navigate to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Check if .env exists
if [ -f ".env" ]; then
    # Load CHROMA_DATA_PATH from .env if set
    CHROMA_DATA_PATH=$(grep "^CHROMA_DATA_PATH=" .env | cut -d '=' -f2 | tr -d '"' || echo "./data/chroma")
    CHROMA_PORT=$(grep "^CHROMA_PORT=" .env | cut -d '=' -f2 | tr -d '"' || echo "8001")
else
    CHROMA_DATA_PATH="./data/chroma"
    CHROMA_PORT="8001"
fi

# Check if chromadb is installed in virtual environment
if [ ! -d "backend/.venv" ]; then
    echo "Error: Virtual environment not found. Run ./scripts/setup-local.sh first."
    exit 1
fi

# Activate virtual environment
source backend/.venv/bin/activate

# Check if chromadb is installed
if ! python -c "import chromadb" 2>/dev/null; then
    echo "Error: chromadb not installed in virtual environment."
    echo "Install with: cd backend && source .venv/bin/activate && pip install chromadb"
    exit 1
fi

# Create data directory if it doesn't exist
mkdir -p "$CHROMA_DATA_PATH"

echo "Starting ChromaDB server..."
echo "  Data path: $CHROMA_DATA_PATH"
echo "  Port: $CHROMA_PORT"
echo "  API will be available at http://localhost:$CHROMA_PORT"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Start ChromaDB server
chroma run --path "$CHROMA_DATA_PATH" --port "$CHROMA_PORT"
