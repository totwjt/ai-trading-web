#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WEB_DIR="$SCRIPT_DIR/web-client"
BACKEND_DIR="$SCRIPT_DIR/backend"

VITE_PORT=3000
BACKEND_PORT=8766
BACKEND_LOG="$SCRIPT_DIR/logs/backend.log"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

check_port() {
    local port=$1
    if lsof -ti:$port >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

kill_port() {
    local port=$1
    local pid=$(lsof -ti:$port 2>/dev/null)
    if [ -n "$pid" ]; then
        log_warn "端口 $port 被占用 (PID: $pid)，正在释放..."
        kill -9 $pid 2>/dev/null
        sleep 1
        if lsof -ti:$port >/dev/null 2>&1; then
            log_error "无法释放端口 $port"
            return 1
        fi
        log_info "端口 $port 已释放"
    fi
    return 0
}

start_backend() {
    log_info "启动后端服务 (端口 $BACKEND_PORT)..."
    
    mkdir -p "$SCRIPT_DIR/logs"
    
    cd "$BACKEND_DIR"
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
    fi
    
    nohup python server.py > "$BACKEND_LOG" 2>&1 &
    BACKEND_PID=$!
    
    sleep 3
    
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        log_info "后端服务已启动 (PID: $BACKEND_PID)"
    else
        log_error "后端服务启动失败"
        if [ -f "$BACKEND_LOG" ]; then
            log_error "查看日志: tail -50 $BACKEND_LOG"
        fi
        return 1
    fi
}

start_frontend() {
    log_info "启动前端服务 (端口 $VITE_PORT)..."
    
    cd "$WEB_DIR"
    nohup npm run dev -- --host > /dev/null 2>&1 &
    VITE_PID=$!
    
    sleep 3
    
    if ps -p $VITE_PID > /dev/null 2>&1; then
        log_info "前端服务已启动 (PID: $VITE_PID)"
    else
        log_error "前端服务启动失败"
        return 1
    fi
}

cleanup() {
    log_info "停止所有服务..."
    [ -n "$VITE_PID" ] && kill "$VITE_PID" 2>/dev/null
    [ -n "$BACKEND_PID" ] && kill "$BACKEND_PID" 2>/dev/null
    log_info "服务已停止"
    exit 0
}

main() {
    echo ""
    log_info "========================================"
    log_info "       AI Trading Web 启动脚本"
    log_info "========================================"
    echo ""
    
    trap cleanup SIGINT SIGTERM
    
    log_info "检查端口占用情况..."
    
    if check_port $VITE_PORT; then
        kill_port $VITE_PORT
    fi
    
    if check_port $BACKEND_PORT; then
        kill_port $BACKEND_PORT
    fi
    
    start_backend
    start_frontend
    
    echo ""
    log_info "========================================"
    log_info "所有服务已启动:"
    log_info "  前端: http://localhost:$VITE_PORT"
    log_info "  后端: http://localhost:$BACKEND_PORT"
    log_info "  API:  http://localhost:$BACKEND_PORT/api"
    log_info "========================================"
    echo ""
    log_info "按 Ctrl+C 停止所有服务"
    echo ""
    
    wait
}

main
