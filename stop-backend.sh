#!/bin/bash

# Stop All Backend Microservices

PROJECT_ROOT="/home/sonofogre/Downloads/InternetOfEmotions-main"
LOGS_DIR="$PROJECT_ROOT/logs"

echo "🛑 Stopping Internet of Emotions - Backend Services"
echo "=================================================="

# Function to stop a service
stop_service() {
    local service_name=$1
    local pid_file="$LOGS_DIR/${service_name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            echo "Stopping $service_name (PID: $pid)..."
            kill $pid
            rm "$pid_file"
            echo "✓ $service_name stopped"
        else
            echo "⚠ $service_name not running (PID: $pid)"
            rm "$pid_file"
        fi
    else
        echo "⚠ $service_name PID file not found"
    fi
}

# Stop all services
stop_service "api-gateway"
stop_service "aggregator"
stop_service "ml-analyzer"
stop_service "event-extractor"
stop_service "content-extractor"
stop_service "data-fetcher"

echo ""
echo "=================================================="
echo "✅ All services stopped!"
echo ""
echo "Logs preserved in: $LOGS_DIR/"
