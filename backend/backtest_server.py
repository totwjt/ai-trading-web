"""
AI Trading Server - 策略与回测服务

FastAPI 主入口
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import asyncio
import logging

from backend.backtest.src.routers import strategy_router, backtest_router, preview_router
from backend.websocket_manager import websocket_handler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Trading Server - 策略与回测",
    description="AI 交易平台后端服务 - 策略管理 + 回测引擎",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "service": "backtest",
        "timestamp": datetime.now().isoformat()
    }


app.include_router(strategy_router, prefix="/api")
app.include_router(backtest_router, prefix="/api")
app.include_router(preview_router, prefix="/api")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 端点"""
    await websocket_handler(websocket)


async def main():
    import uvicorn
    
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=8766,
        log_level="info"
    )
    server = uvicorn.Server(config)
    
    logger.info("HTTP API 服务启动: http://0.0.0.0:8766")
    logger.info("WebSocket 服务启动: ws://0.0.0.0:8766/ws")
    
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
