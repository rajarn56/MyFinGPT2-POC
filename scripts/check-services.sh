#!/bin/bash
# Check status of all services (local and Docker)

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=== Service Status Check ==="
echo ""

# Load .env if exists
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Check Chroma
CHROMA_HOST=${CHROMA_HOST:-localhost}
CHROMA_PORT=${CHROMA_PORT:-8001}
if curl -s "http://$CHROMA_HOST:$CHROMA_PORT/api/v1/heartbeat" >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Chroma: Running at $CHROMA_HOST:$CHROMA_PORT"
else
    echo -e "${RED}✗${NC} Chroma: Not accessible at $CHROMA_HOST:$CHROMA_PORT"
fi

# Check Neo4j
NEO4J_URI=${NEO4J_URI:-bolt://localhost:7687}
NEO4J_HOST=$(echo "$NEO4J_URI" | sed 's|bolt://||' | cut -d ':' -f1)
NEO4J_PORT=$(echo "$NEO4J_URI" | sed 's|bolt://||' | cut -d ':' -f2)
if nc -z "$NEO4J_HOST" "$NEO4J_PORT" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Neo4j: Running at $NEO4J_URI"
else
    echo -e "${RED}✗${NC} Neo4j: Not accessible at $NEO4J_URI"
fi

# Check LMStudio
LM_STUDIO_API_BASE=${LM_STUDIO_API_BASE:-http://localhost:1234/v1}
LM_STUDIO_HOST=$(echo "$LM_STUDIO_API_BASE" | sed 's|http://||' | sed 's|/v1||' | cut -d ':' -f1)
LM_STUDIO_PORT=$(echo "$LM_STUDIO_API_BASE" | sed 's|http://||' | sed 's|/v1||' | cut -d ':' -f2 || echo "1234")
if curl -s "$LM_STUDIO_API_BASE/models" >/dev/null 2>&1; then
    MODEL_COUNT=$(curl -s "$LM_STUDIO_API_BASE/models" | grep -o '"id"' | wc -l || echo "0")
    echo -e "${GREEN}✓${NC} LMStudio: Running at $LM_STUDIO_API_BASE ($MODEL_COUNT models loaded)"
else
    echo -e "${RED}✗${NC} LMStudio: Not accessible at $LM_STUDIO_API_BASE"
fi

# Check Backend
if curl -s "http://localhost:8000/health/" >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Backend: Running at http://localhost:8000"
    # Get health status
    HEALTH=$(curl -s "http://localhost:8000/health/" | grep -o '"status":"[^"]*"' | cut -d'"' -f4 || echo "unknown")
    echo "  Health: $HEALTH"
else
    echo -e "${RED}✗${NC} Backend: Not running at http://localhost:8000"
fi

echo ""
echo "=== Docker Containers ==="
if command -v docker >/dev/null 2>&1; then
    docker-compose ps 2>/dev/null || echo "No docker-compose.yml found or Docker not running"
else
    echo "Docker not installed"
fi

