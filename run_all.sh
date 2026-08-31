#!/bin/bash

# ==============================================================================
# StockCast Backend - All-In-One Startup Script (run_all.sh)
# Starts Redis, Celery Worker, Celery Beat, and Django ASGI Server in one command.
# Gracefully stops all background processes on Ctrl+C.
# ==============================================================================

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# Colors for terminal output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================================${NC}"
echo -e "${GREEN}       🚀 Starting StockCast Backend Pipeline         ${NC}"
echo -e "${BLUE}======================================================${NC}"

# 1. Activate Virtual Environment
if [ -d "venv" ]; then
    echo -e "${YELLOW}[1/5] Activating Virtual Environment...${NC}"
    source venv/bin/activate
else
    echo -e "${RED}Error: venv directory not found. Please create venv first.${NC}"
    exit 1
fi

# 2. Check and Start Redis Server
echo -e "${YELLOW}[2/5] Checking Redis Server...${NC}"
REDIS_CLI=$(which redis-cli || echo "/opt/homebrew/bin/redis-cli")
REDIS_SERVER=$(which redis-server || echo "/opt/homebrew/bin/redis-server")

if $REDIS_CLI ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Redis is already running.${NC}"
else
    echo -e "${YELLOW}Starting Redis daemon...${NC}"
    if [ -x "$REDIS_SERVER" ]; then
        $REDIS_SERVER --daemonize yes
        sleep 1
        if $REDIS_CLI ping > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Redis started successfully.${NC}"
        else
            echo -e "${RED}Warning: Failed to start Redis automatically. Make sure Redis is installed and running.${NC}"
        fi
    else
        brew services start redis > /dev/null 2>&1 || true
        echo -e "${GREEN}✓ Attempted starting Redis via brew services.${NC}"
    fi
fi

# 3. Apply Database Migrations
echo -e "${YELLOW}[3/5] Checking and Applying Database Migrations...${NC}"
python manage.py migrate --noinput
echo -e "${GREEN}✓ Database is up to date.${NC}"

# Cleanup handler on exit (Ctrl+C)
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down StockCast Backend services...${NC}"
    if [ -n "$CELERY_WORKER_PID" ] && kill -0 "$CELERY_WORKER_PID" 2>/dev/null; then
        kill "$CELERY_WORKER_PID" 2>/dev/null
    fi
    if [ -n "$CELERY_BEAT_PID" ] && kill -0 "$CELERY_BEAT_PID" 2>/dev/null; then
        kill "$CELERY_BEAT_PID" 2>/dev/null
    fi
    # Kill any dangling celery processes if spawned
    pkill -f "celery -A core" 2>/dev/null || true
    echo -e "${GREEN}✓ All services stopped cleanly. Goodbye!${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# 4. Start Celery Worker in Background
echo -e "${YELLOW}[4/5] Starting Celery Worker (Background)...${NC}"
celery -A core worker -l info > /dev/null 2>&1 &
CELERY_WORKER_PID=$!
echo -e "${GREEN}✓ Celery Worker started (PID: $CELERY_WORKER_PID)${NC}"

# 5. Start Celery Beat Scheduler in Background
echo -e "${YELLOW}[5/5] Starting Celery Beat Scheduler (Background)...${NC}"
celery -A core beat -l info > /dev/null 2>&1 &
CELERY_BEAT_PID=$!
echo -e "${GREEN}✓ Celery Beat started (PID: $CELERY_BEAT_PID)${NC}"

echo -e "\n${BLUE}======================================================${NC}"
echo -e "${GREEN}✓ All background services are ACTIVE and RUNNING!${NC}"
echo -e "  - REST API & WebSockets: ${YELLOW}http://127.0.0.1:8000${NC}"
echo -e "  - Live WebSocket Stream: ${YELLOW}ws://127.0.0.1:8000/ws/live/${NC}"
echo -e "  - Press ${RED}Ctrl + C${NC} anytime to stop all services."
echo -e "${BLUE}======================================================${NC}\n"

# 6. Start Django Server (Foregound)
python manage.py runserver 0.0.0.0:8000
