#!/bin/bash
# Setup script for local development (without Docker)

set -e

echo "=== MyFinGPT-POC-V2 Local Setup ==="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo "Checking prerequisites..."
command -v python3 >/dev/null 2>&1 || { echo "Error: python3 is required but not installed."; exit 1; }
command -v uv >/dev/null 2>&1 || { echo "Error: uv is required but not installed. Install from https://github.com/astral-sh/uv"; exit 1; }

# Check if Neo4j is running locally (optional)
if command -v neo4j >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Neo4j command found"
else
    echo -e "${YELLOW}⚠${NC} Neo4j command not found. Install Neo4j Desktop or use Docker."
fi

# Check if LMStudio is accessible
if curl -s http://localhost:1234/v1/models >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} LMStudio is running on localhost:1234"
    MODEL_COUNT=$(curl -s http://localhost:1234/v1/models 2>/dev/null | grep -o '"id"' | wc -l || echo "0")
    echo -e "  ${YELLOW}ℹ${NC}  Loaded models: $MODEL_COUNT"
    echo -e "  ${YELLOW}ℹ${NC}  Remember to load both LLM model and embedding model in LMStudio"
else
    echo -e "${YELLOW}⚠${NC} LMStudio not detected on localhost:1234. Make sure LMStudio is running."
fi

echo ""
echo "Setting up backend..."

# Navigate to backend directory
cd "$(dirname "$0")/../backend" || exit 1

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
uv pip install -r requirements.txt

# Create .env file if it doesn't exist
cd ..
if [ ! -f ".env" ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo -e "${YELLOW}⚠${NC} Please edit .env file with your local configuration:"
    echo "   - Set NEO4J_URI if using local Neo4j (default: bolt://localhost:7687)"
    echo "   - Set LM_STUDIO_API_BASE if LMStudio is on different port (default: http://localhost:1234/v1)"
    echo "   - Set LM_STUDIO_MODEL to your LLM model name"
    echo "   - Set EMBEDDING_MODEL to your embedding model name (REQUIRED for vector search)"
    echo "   - Set EMBEDDING_PROVIDER=lmstudio if using LMStudio for embeddings"
else
    echo -e "${GREEN}✓${NC} .env file already exists"
fi

echo ""
echo -e "${GREEN}Setup complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your local configuration"
echo "2. Start Neo4j locally (if not using Docker): neo4j start"
echo "3. Start LMStudio and load a model"
echo "4. Run: ./scripts/start-backend-local.sh"

