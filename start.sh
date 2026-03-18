#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WEB_DIR="$SCRIPT_DIR/web-client"
BACKEND_DIR="$SCRIPT_DIR/backend/recommendation"

VITE_PORT=5173
WS_PORT=8765

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

cleanup() {
    log_info "停止服务..."
    [ -n "$VITE_PID" ] && kill "$VITE_PID" 2>/dev/null
    [ -n "$WS_PID" ] && kill "$WS_PID" 2>/dev/null
    exit 0
}

kill_port() {
    local pid=$(lsof -ti:$1 2>/dev/null)
    [ -n "$pid" ] && { kill -9 $pid 2>/dev/null; sleep 1; }
}

main() {
    log_info "AI Trading Web 启动中..."
    
    trap cleanup SIGINT SIGTERM
    
    kill_port $VITE_PORT
    kill_port $WS_PORT
    
    cd "$WEB_DIR" && npm run dev > /dev/null 2>&1 &
    VITE_PID=$!
    
    cd "$BACKEND_DIR" && python -m recommendation.websocket_server > /dev/null 2>&1 &
    WS_PID=$!
    
    log_info "前端: http://localhost:$VITE_PORT"
    log_info "WebSocket: ws://localhost:$WS_PORT"
    log_info "按 Ctrl+C 停止"
    
    wait
}

main
