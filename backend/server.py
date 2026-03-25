"""
AI Trading Server

整合服务:
- 资讯分析 API
- 策略管理 API
- 回测管理 API
- WebSocket 实时推送 (使用 python-socketio)
"""

import socketio
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import asyncio
import logging

from recommendation.db import get_latest_news, get_news_by_id
from backtest.src.routers import strategy_router, backtest_router, preview_router
from trading.routers import trading_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOPIC_RECOMMENDATION = "recommendation"
TOPIC_ZIXUAN = "zixuan"
TOPIC_BACKTEST = "backtest"
TOPIC_TRADING = "trading"

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

sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins="*",
    ping_timeout=60,
    ping_interval=25
)
socketio_app = socketio.ASGIApp(sio, static_files={
    '/': 'public/index.html'
})

app.mount('/socket.io', socketio_app)


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


@sio.event
async def connect(sid, environ):
    logger.info(f"Client connected: {sid}")
    await sio.emit('connected', {'status': 'ok', 'sid': sid}, room=sid)


@sio.event
async def disconnect(sid):
    logger.info(f"Client disconnected: {sid}")


@sio.event
async def subscribe(sid, data):
    topics = data.get('topics', []) if isinstance(data, dict) else data
    logger.info(f"Client {sid} subscribed to: {topics}")
    for topic in topics:
        await sio.enter_room(sid, topic)
    await sio.emit('subscribed', {'topics': topics}, room=sid)


@sio.event
async def unsubscribe(sid, data):
    topics = data.get('topics', []) if isinstance(data, dict) else data
    logger.info(f"Client {sid} unsubscribed from: {topics}")
    for topic in topics:
        await sio.leave_room(sid, topic)
    await sio.emit('unsubscribed', {'topics': topics}, room=sid)


@sio.event
async def heartbeat(sid):
    await sio.emit('heartbeat', {'server_time': datetime.now().isoformat()}, room=sid)


# ============================================================
# 外部服务推送事件处理
# 外部服务通过此事件推送数据，服务端转发到对应主题
# ============================================================
@sio.event
async def push_from_external(sid, data):
    """
    接收外部服务推送的数据，转发到对应主题
    data 格式:
    {
        "topic": "zixuan",           # 目标主题
        "data": [...] 或 {...}       # 推送数据
    }
    """
    topic = data.get('topic')
    payload = data.get('data')
    
    if not topic or payload is None:
        logger.warning(f"[push_from_external] 缺少 topic 或 data: {data}")
        return
    
    logger.info(f"[push_from_external] 收到推送 -> topic: {topic}, data: {str(payload)[:100]}...")
    
    if topic == TOPIC_ZIXUAN:
        await sio.emit(TOPIC_ZIXUAN, payload, room=TOPIC_ZIXUAN)
    elif topic == TOPIC_RECOMMENDATION:
        await sio.emit(TOPIC_RECOMMENDATION, payload, room=TOPIC_RECOMMENDATION)
    elif topic.startswith('backtest'):
        await sio.emit(topic, payload, room=topic)
    elif topic == TOPIC_TRADING:
        await sio.emit(TOPIC_TRADING, payload, room=TOPIC_TRADING)
    else:
        # 通用主题广播
        await sio.emit(topic, payload, room=topic)
    
    # 确认推送成功
    await sio.emit('push_ack', {'topic': topic, 'status': 'ok'}, room=sid)


async def publish_recommendation(data: dict):
    await sio.emit(TOPIC_RECOMMENDATION, data, room=TOPIC_RECOMMENDATION)


async def publish_zixuan(data: list):
    await sio.emit(TOPIC_ZIXUAN, data, room=TOPIC_ZIXUAN)


async def publish_backtest(backtest_id: int, data: dict):
    topic = f"{TOPIC_BACKTEST}.{backtest_id}"
    await sio.emit(topic, data, room=topic)


async def publish_trading(data: dict):
    await sio.emit(TOPIC_TRADING, data, room=TOPIC_TRADING)


app.include_router(strategy_router, prefix="/api")
app.include_router(backtest_router, prefix="/api")
app.include_router(preview_router, prefix="/api")
app.include_router(trading_router)


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
    
    config = uvicorn.Config(app, host="0.0.0.0", port=8766, log_level="info")
    server = uvicorn.Server(config)
    
    logger.info("=" * 50)
    logger.info("HTTP API + Socket.IO 服务启动: http://0.0.0.0:8766")
    logger.info("Socket.IO: ws://0.0.0.0:8766/socket.io")
    logger.info("API 路由已加载:")
    logger.info("  - /api/strategies/*  (策略管理)")
    logger.info("  - /api/backtests/*   (回测管理)")
    logger.info("  - /api/trading/*     (交易服务)")
    logger.info("  - /socket.io         (WebSocket Pub/Sub)")
    logger.info("  - /push_from_external (外部推送入口)")
    logger.info("=" * 50)
    
    await server.serve()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("服务已停止")
