"""
AI Trading Server

整合服务:
- 资讯分析 API
- 策略管理 API
- 回测管理 API
- WebSocket 实时推送 (复用 recommendation 服务)
"""

from fastapi import FastAPI, HTTPException, Query, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import asyncio
import json
import logging
import websockets
from websockets import WebSocketServerProtocol

from recommendation.db import get_latest_news, get_news_by_id
from recommendation.models import WSMessage, MessageType
from backtest.src.routers import strategy_router, backtest_router, preview_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

connected_websockets: set = set()
ws_client_info: dict = {}

app = FastAPI(
    title="AI Trading Server",
    description="AI 交易平台后端服务 - 资讯分析 + 策略回测 + 实时推送",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(strategy_router, prefix="/api")
app.include_router(backtest_router, prefix="/api")
app.include_router(preview_router, prefix="/api")


class StockItem(BaseModel):
    name: str
    code: Optional[str] = None
    score: Optional[int] = None


class NewsItem(BaseModel):
    id: int
    title: str
    source: str
    publish_time: Optional[str] = None
    analysis: str
    sectors: List[str] = []
    stocks: List[StockItem] = []


class ApiResponse(BaseModel):
    code: int = 0
    message: str = "success"
    data: Optional[List[NewsItem]] = None
    timestamp: str = ""


async def handle_ws_message(websocket: WebSocketServerProtocol, message: str):
    try:
        ws_msg = WSMessage.from_json(message)
        logger.info(f"收到WebSocket消息: type={ws_msg.type}")
        
        if ws_msg.type == MessageType.HEARTBEAT:
            response = WSMessage(
                type=MessageType.HEARTBEAT,
                payload={"status": "pong", "server_time": datetime.now().isoformat()}
            )
            await websocket.send(response.to_json())
            
        elif ws_msg.type == MessageType.SUBSCRIBE:
            ws_client_info[websocket].update({
                "client_type": ws_msg.payload.get("client_type", "web"),
                "client_id": ws_msg.payload.get("client_id", ""),
                "action": ws_msg.payload.get("action", "default")
            })
            response = WSMessage(
                type=MessageType.SYSTEM,
                payload={"status": "subscribed", "topics": ws_msg.payload.get("topics", [])}
            )
            await websocket.send(response.to_json())
            
        elif ws_msg.type == MessageType.CONNECT:
            ws_client_info[websocket].update({
                "client_type": ws_msg.payload.get("client_type", "web"),
                "client_id": ws_msg.payload.get("client_id", ""),
                "action": ws_msg.payload.get("action", "default")
            })
            response = WSMessage(
                type=MessageType.SYSTEM,
                payload={
                    "status": "connected",
                    "client_id": ws_msg.payload.get("client_id", ""),
                    "client_type": ws_msg.payload.get("client_type", "web"),
                    "server_time": datetime.now().isoformat()
                }
            )
            await websocket.send(response.to_json())
            
        elif ws_msg.type == MessageType.PUSH:
            data = ws_msg.payload.get("data", {})
            await broadcast_ws(data)
            
    except json.JSONDecodeError:
        logger.error(f"无效JSON: {message[:100]}")
    except Exception as e:
        logger.error(f"处理WebSocket消息错误: {e}")


async def broadcast_ws(data: dict):
    ws_msg = WSMessage(type=MessageType.RECOMMENDATION, payload=data)
    json_msg = ws_msg.to_json()
    
    disconnected = set()
    for ws in connected_websockets:
        try:
            await ws.send(json_msg)
        except Exception:
            disconnected.add(ws)
    
    for ws in disconnected:
        connected_websockets.discard(ws)
        ws_client_info.pop(ws, None)


async def websocket_handler(websocket: WebSocketServerProtocol):
    connected_websockets.add(websocket)
    ws_client_info[websocket] = {
        "connected_at": datetime.now().isoformat(),
        "client_type": "web"
    }
    logger.info(f"WebSocket客户端连接, 当前连接数: {len(connected_websockets)}")
    
    welcome = WSMessage(
        type=MessageType.SYSTEM,
        payload={"status": "connected", "server_time": datetime.now().isoformat()}
    )
    await websocket.send(welcome.to_json())
    
    try:
        async for message in websocket:
            await handle_ws_message(websocket, message)
    except Exception as e:
        logger.error(f"WebSocket异常: {e}")
    finally:
        connected_websockets.discard(websocket)
        ws_client_info.pop(websocket, None)
        logger.info(f"WebSocket客户端断开, 当前连接数: {len(connected_websockets)}")


async def start_websocket_server():
    async with websockets.serve(websocket_handler, "0.0.0.0", 8765):
        logger.info("WebSocket服务启动: ws://0.0.0.0:8765")
        await asyncio.Future()


@app.get("/api/news/latest", response_model=ApiResponse)
async def get_news_latest(limit: int = Query(default=10, ge=1, le=100)):
    try:
        news_list = get_latest_news(limit=limit)
        
        result = []
        for item in news_list:
            result.append(NewsItem(
                id=item['id'],
                title=item['title'],
                source=item['source'],
                publish_time=item['publish_time'],
                analysis=item['analysis'],
                sectors=item['sectors'],
                stocks=[StockItem(**s) for s in item['stocks']]
            ))
        
        return ApiResponse(
            code=0,
            message="success",
            data=result,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"获取资讯失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/news/{news_id}", response_model=ApiResponse)
async def get_news_detail(news_id: int):
    try:
        news = get_news_by_id(news_id)
        if not news:
            raise HTTPException(status_code=404, detail="News not found")
        
        return ApiResponse(
            code=0,
            message="success",
            data=[NewsItem(
                id=news['id'],
                title=news['title'],
                source=news['source'],
                publish_time=news['publish_time'],
                analysis=news['analysis'],
                sectors=news['sectors'],
                stocks=[StockItem(**s) for s in news['stocks']]
            )],
            timestamp=datetime.now().isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取资讯详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


async def main():
    import uvicorn
    
    ws_task = asyncio.create_task(start_websocket_server())
    config = uvicorn.Config(app, host="0.0.0.0", port=8766, log_level="info")
    server = uvicorn.Server(config)
    
    logger.info("=" * 50)
    logger.info("HTTP API 服务启动: http://0.0.0.0:8766")
    logger.info("WebSocket 服务启动: ws://0.0.0.0:8765")
    logger.info("API 路由已加载:")
    logger.info("  - /api/strategies/*  (策略管理)")
    logger.info("  - /api/backtests/*   (回测管理)")
    logger.info("=" * 50)
    
    try:
        await asyncio.gather(
            server.serve(),
            ws_task
        )
    except asyncio.CancelledError:
        logger.info("正在关闭服务...")
        ws_task.cancel()
        await server.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("服务已停止")
