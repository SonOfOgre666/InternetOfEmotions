#!/bin/bash

# Start All Backend Microservices
# This script starts all services in the background

PROJECT_ROOT="/home/sonofogre/Downloads/InternetOfEmotions-main"
VENV_PATH="$PROJECT_ROOT/.venv"

echo "🚀 Starting Internet of Emotions - Backend Services"
echo "=================================================="

# Function to start a service
start_service() {
    local service_name=$1
    local service_dir=$2
    local port=$3
    
    echo "Starting $service_name on port $port..."
    cd "$PROJECT_ROOT/backend/microservices/$service_dir"
    
    # Use virtual environment Python
    PYTHON="$PROJECT_ROOT/backend/.venv/bin/python3"
    
    nohup $PYTHON app.py > "$PROJECT_ROOT/logs/${service_name}.log" 2>&1 &
    echo $! > "$PROJECT_ROOT/logs/${service_name}.pid"
    echo "✓ $service_name started (PID: $(cat $PROJECT_ROOT/logs/${service_name}.pid))"
}

# Create logs directory
mkdir -p "$PROJECT_ROOT/logs"

# Start all services
start_service "data-fetcher" "data-fetcher" 5001
sleep 2
start_service "content-extractor" "content-extractor" 5007
sleep 2
start_service "event-extractor" "event-extractor" 5004
sleep 2
start_service "ml-analyzer" "ml-analyzer" 5005
sleep 2
start_service "aggregator" "aggregator" 5003
sleep 2
start_service "api-gateway" "api-gateway" 5000

echo ""
echo "=================================================="
echo "✅ All services started!"
echo ""
echo "Service Status:"
echo "  - Data Fetcher:      http://localhost:5001/health"
echo "  - Content Extractor: http://localhost:5007/health"
echo "  - Event Extractor:   http://localhost:5004/health"
echo "  - ML Analyzer:       http://localhost:5005/health"
echo "  - Aggregator:        http://localhost:5003/health"
echo "  - API Gateway:       http://localhost:5000/api/health"
echo ""
echo "Logs are in: $PROJECT_ROOT/logs/"
echo ""
echo "To stop all services, run: ./stop-backend.sh"
echo ""
echo "Next: Start the frontend with:"
echo "  cd $PROJECT_ROOT/frontend"
echo "  npm run dev"
