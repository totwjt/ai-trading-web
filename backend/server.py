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
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
import logging
import uuid

import httpx
from recommendation.db import get_latest_news, get_news_by_id
from backtest.src.routers import strategy_router, backtest_router, preview_router
from trading.routers import trading_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOPIC_RECOMMENDATION = "recommendation"
TOPIC_ZIXUAN = "zixuan"
TOPIC_BACKTEST = "backtest"
TOPIC_TRADING = "trading"
TOPIC_RISK = "risk"
TOPIC_TRADING_TERMINAL = "trading-terminal"

TERMINAL_HEARTBEAT_TIMEOUT = 30
TERMINAL_HEARTBEAT_CHECK_INTERVAL = 5

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


terminal_registry: Dict[str, Dict[str, Any]] = {}
sid_terminal_map: Dict[str, str] = {}
terminal_monitor_task: Optional[asyncio.Task] = None


def now_iso() -> str:
    return datetime.now().isoformat()


def get_user_id(data: Dict[str, Any]) -> str:
    return str(data.get("userId") or data.get("user_id") or "").strip()


def get_terminal_id(data: Dict[str, Any]) -> str:
    raw_terminal_id = str(data.get("terminalId") or data.get("terminal_id") or "").strip()
    if raw_terminal_id:
        return raw_terminal_id

    raw_mac = str(data.get("macAddress") or data.get("mac_address") or "").strip().lower()
    if not raw_mac:
        return ""

    mac_normalized = raw_mac.replace(":", "-").replace(".", "-")
    return f"mac-{mac_normalized}"


def get_terminal_name(data: Dict[str, Any]) -> str:
    return str(data.get("terminalName") or data.get("terminal_name") or "").strip()


def get_mac_address(data: Dict[str, Any]) -> str:
    return str(data.get("macAddress") or data.get("mac_address") or "").strip()


def get_account_name(data: Dict[str, Any]) -> str:
    return str(data.get("accountName") or data.get("account_name") or "").strip()


def terminal_key(user_id: str, terminal_id: str) -> str:
    return f"{user_id}:{terminal_id}"


def terminal_topic(user_id: str, terminal_id: str) -> str:
    return f"{TOPIC_TRADING_TERMINAL}.{user_id}.{terminal_id}"


def terminal_control_topic(user_id: str) -> str:
    return f"{TOPIC_TRADING_TERMINAL}.control.{user_id}"


def build_terminal_event(
    user_id: str,
    terminal_id: str,
    event_type: str,
    data: Optional[Dict[str, Any]] = None,
    seq: Optional[int] = None
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "v": "1.0",
        "msgId": str(uuid.uuid4()),
        "ts": now_iso(),
        "userId": user_id,
        "terminalId": terminal_id,
        "eventType": event_type,
        "data": data or {},
    }
    if seq is not None:
        payload["seq"] = seq
    return payload


async def emit_terminal_control(
    user_id: str,
    terminal_id: str,
    event_type: str,
    data: Optional[Dict[str, Any]] = None
):
    topic = terminal_control_topic(user_id)
    event_payload = build_terminal_event(user_id, terminal_id, event_type, data=data)
    await sio.emit(topic, event_payload, room=topic)


def build_terminal_snapshot(user_id: str) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for info in terminal_registry.values():
        if info["userId"] != user_id:
            continue
        items.append({
            "userId": info["userId"],
            "terminalId": info["terminalId"],
            "terminalName": info.get("terminalName") or info["terminalId"],
            "macAddress": info.get("macAddress") or "",
            "accountName": info.get("accountName") or "",
            "online": info["online"],
            "statusSource": info.get("statusSource") or "terminal_service",
            "lastHeartbeatAt": info["lastHeartbeatAt"],
            "connectedAt": info["connectedAt"],
            "updatedAt": info["updatedAt"],
        })
    return items


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
    key = sid_terminal_map.pop(sid, None)
    if not key or key not in terminal_registry:
        return

    info = terminal_registry[key]
    if info["online"]:
        info["online"] = False
        info["updatedAt"] = now_iso()
        await emit_terminal_control(
            info["userId"],
            info["terminalId"],
            "terminal.offline",
            {
                "terminalName": info.get("terminalName") or info["terminalId"],
                "reason": "service_disconnect",
                "statusSource": "terminal_service"
            }
        )


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


@sio.event
async def terminal_register(sid, data):
    """
    终端客户端注册
    data:
    {
      "userId": "u_1001",
      "terminalId": "terminal-node-1",
      "terminalName": "柜台A"
    }
    """
    if not isinstance(data, dict):
        await sio.emit("terminal_error", {"message": "invalid payload"}, room=sid)
        return

    user_id = get_user_id(data)
    terminal_id = get_terminal_id(data)
    terminal_name = get_terminal_name(data) or terminal_id
    mac_address = get_mac_address(data)
    account_name = get_account_name(data)
    initial_status = str(data.get("status") or "").strip().lower()
    if not user_id or not terminal_id:
        await sio.emit(
            "terminal_error",
            {"message": "userId and (terminalId or macAddress) are required"},
            room=sid
        )
        return

    key = terminal_key(user_id, terminal_id)
    prev = terminal_registry.get(key)
    if prev and prev.get("sid") and prev["sid"] != sid:
        old_sid = prev["sid"]
        sid_terminal_map.pop(old_sid, None)
        try:
            await sio.disconnect(old_sid)
        except Exception:
            logger.warning("disconnect previous terminal sid failed: %s", old_sid)

    topic = terminal_topic(user_id, terminal_id)
    control_topic = terminal_control_topic(user_id)
    await sio.enter_room(sid, topic)
    await sio.enter_room(sid, control_topic)

    terminal_registry[key] = {
        "userId": user_id,
        "terminalId": terminal_id,
        "terminalName": terminal_name,
        "macAddress": mac_address,
        "accountName": account_name,
        "sid": sid,
        # 在线状态由终端 Python 服务主动上报 terminal_status_update
        "online": initial_status == "online",
        "statusSource": "terminal_service",
        "connectedAt": prev["connectedAt"] if prev else now_iso(),
        "lastHeartbeatAt": now_iso(),
        "updatedAt": now_iso(),
    }
    sid_terminal_map[sid] = key

    await sio.emit(
        "terminal_registered",
        {
            "userId": user_id,
            "terminalId": terminal_id,
            "terminalName": terminal_name,
            "macAddress": mac_address,
            "accountName": account_name,
            "topic": topic,
            "controlTopic": control_topic,
            "status": "ok",
        },
        room=sid
    )
    await emit_terminal_control(
        user_id,
        terminal_id,
        "terminal.added",
        {
            "terminalName": terminal_name,
            "macAddress": mac_address,
            "accountName": account_name
        }
    )
    if initial_status == "online":
        await emit_terminal_control(
            user_id,
            terminal_id,
            "terminal.online",
            {
                "terminalName": terminal_name,
                "macAddress": mac_address,
                "accountName": account_name,
                "statusSource": "terminal_service"
            }
        )


@sio.event
async def terminal_status_update(sid, data):
    """
    终端 Python 服务主动上报终端状态（在线/离线）
    data:
    {
      "userId": "u_1001",
      "terminalId": "terminal-node-1",
      "status": "online" | "offline",
      "reason": "manual" | "app_disconnected" | ...
    }
    """
    if not isinstance(data, dict):
        await sio.emit("terminal_error", {"message": "invalid payload"}, room=sid)
        return

    user_id = get_user_id(data)
    terminal_id = get_terminal_id(data)
    status = str(data.get("status") or "").strip().lower()
    reason = str(data.get("reason") or "").strip() or "terminal_service_report"

    if not user_id or not terminal_id or status not in {"online", "offline"}:
        await sio.emit(
            "terminal_error",
            {"message": "userId, (terminalId or macAddress) and status(online/offline) are required"},
            room=sid
        )
        return

    key = terminal_key(user_id, terminal_id)
    if key not in terminal_registry:
        await sio.emit("terminal_error", {"message": "terminal not registered"}, room=sid)
        return

    info = terminal_registry[key]
    next_online = status == "online"
    if info["online"] == next_online:
        info["updatedAt"] = now_iso()
        return

    info["online"] = next_online
    info["updatedAt"] = now_iso()
    event_type = "terminal.online" if next_online else "terminal.offline"
    await emit_terminal_control(
        info["userId"],
        info["terminalId"],
        event_type,
        {
            "terminalName": info.get("terminalName") or info["terminalId"],
            "macAddress": info.get("macAddress") or "",
            "accountName": info.get("accountName") or "",
            "reason": reason,
            "statusSource": "terminal_service"
        }
    )


@sio.event
async def terminal_heartbeat(sid, data):
    """
    终端心跳事件
    data:
    {
      "userId": "u_1001",
      "terminalId": "terminal-node-1",
      "ts": "..."
    }
    """
    key = sid_terminal_map.get(sid)
    payload = data if isinstance(data, dict) else {}
    user_id = get_user_id(payload)
    terminal_id = get_terminal_id(payload)
    if not key and user_id and terminal_id:
        key = terminal_key(user_id, terminal_id)

    if key and key in terminal_registry:
        terminal_registry[key]["lastHeartbeatAt"] = now_iso()
        terminal_registry[key]["updatedAt"] = now_iso()
        await sio.emit("terminal_heartbeat_ack", {"status": "ok", "serverTime": now_iso()}, room=sid)
        return

    await sio.emit("terminal_error", {"message": "terminal not registered (terminalId/macAddress)"}, room=sid)


@sio.event
async def terminal_unregister(sid, data):
    """
    终端主动下线并移除
    data:
    {
      "userId": "u_1001",
      "terminalId": "terminal-node-1"
    }
    """
    key = sid_terminal_map.pop(sid, None)
    payload = data if isinstance(data, dict) else {}
    user_id = get_user_id(payload)
    terminal_id = get_terminal_id(payload)
    if not key and user_id and terminal_id:
        key = terminal_key(user_id, terminal_id)

    if not key or key not in terminal_registry:
        await sio.emit("terminal_error", {"message": "terminal not found (terminalId/macAddress)"}, room=sid)
        return

    info = terminal_registry.pop(key)
    await emit_terminal_control(
        info["userId"],
        info["terminalId"],
        "terminal.removed",
        {"terminalName": info.get("terminalName") or info["terminalId"]}
    )
    await sio.emit(
        "terminal_unregistered",
        {"userId": info["userId"], "terminalId": info["terminalId"], "status": "ok"},
        room=sid
    )


@sio.event
async def terminal_snapshot_request(sid, data):
    """
    获取用户终端快照
    data:
    {
      "userId": "u_1001"
    }
    """
    payload = data if isinstance(data, dict) else {}
    user_id = get_user_id(payload)
    if not user_id:
        await sio.emit("terminal_error", {"message": "userId is required"}, room=sid)
        return

    control_topic = terminal_control_topic(user_id)
    await sio.enter_room(sid, control_topic)
    snapshot = build_terminal_snapshot(user_id)
    await sio.emit(
        "terminal_snapshot",
        {
            "v": "1.0",
            "userId": user_id,
            "ts": now_iso(),
            "terminals": snapshot
        },
        room=sid
    )


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
    elif topic == TOPIC_RISK:
        await sio.emit(TOPIC_RISK, payload, room=TOPIC_RISK)
    elif topic == TOPIC_TRADING_TERMINAL or topic.startswith(f"{TOPIC_TRADING_TERMINAL}."):
        await sio.emit(topic, payload, room=topic)
    else:
        # 通用主题广播
        await sio.emit(topic, payload, room=topic)
    
    # 确认推送成功
    await sio.emit('push_ack', {'topic': topic, 'status': 'ok'}, room=sid)


@sio.event
async def push_trading_terminal(sid, data):
    """
    终端交易推送（推荐事件）
    data:
    {
      "userId": "u_1001",
      "terminalId": "terminal-node-1",
      "eventType": "trade.record.append",
      "seq": 1,
      "data": {...}
    }
    """
    if not isinstance(data, dict):
        await sio.emit("terminal_error", {"message": "invalid payload"}, room=sid)
        return

    user_id = get_user_id(data)
    terminal_id = get_terminal_id(data)
    event_type = str(data.get("eventType") or data.get("event_type") or "").strip()
    payload = data.get("data")
    seq = data.get("seq")

    if not user_id or not terminal_id or not event_type:
        await sio.emit(
            "terminal_error",
            {"message": "userId, terminalId and eventType are required"},
            room=sid
        )
        return

    terminal_event = build_terminal_event(
        user_id=user_id,
        terminal_id=terminal_id,
        event_type=event_type,
        data=payload if isinstance(payload, dict) else {"payload": payload},
        seq=seq if isinstance(seq, int) else None
    )
    topic = terminal_topic(user_id, terminal_id)
    await sio.emit(topic, terminal_event, room=topic)
    await sio.emit(
        "push_ack",
        {
            "topic": topic,
            "status": "ok",
            "eventType": event_type
        },
        room=sid
    )


async def publish_recommendation(data: dict):
    await sio.emit(TOPIC_RECOMMENDATION, data, room=TOPIC_RECOMMENDATION)


async def publish_zixuan(data: list):
    await sio.emit(TOPIC_ZIXUAN, data, room=TOPIC_ZIXUAN)


async def publish_backtest(backtest_id: int, data: dict):
    topic = f"{TOPIC_BACKTEST}.{backtest_id}"
    await sio.emit(topic, data, room=topic)


async def publish_trading(data: dict):
    await sio.emit(TOPIC_TRADING, data, room=TOPIC_TRADING)


async def publish_risk(data: dict):
    await sio.emit(TOPIC_RISK, data, room=TOPIC_RISK)


async def publish_trading_terminal(
    user_id: str,
    terminal_id: str,
    event_type: str,
    data: Optional[Dict[str, Any]] = None,
    seq: Optional[int] = None
):
    topic = terminal_topic(user_id, terminal_id)
    event_payload = build_terminal_event(
        user_id=user_id,
        terminal_id=terminal_id,
        event_type=event_type,
        data=data,
        seq=seq
    )
    await sio.emit(topic, event_payload, room=topic)


async def terminal_heartbeat_monitor():
    while True:
        await asyncio.sleep(TERMINAL_HEARTBEAT_CHECK_INTERVAL)
        now = datetime.now()
        for key, info in list(terminal_registry.items()):
            if not info["online"]:
                continue
            try:
                last = datetime.fromisoformat(info["lastHeartbeatAt"])
            except ValueError:
                info["lastHeartbeatAt"] = now_iso()
                continue

            if (now - last).total_seconds() > TERMINAL_HEARTBEAT_TIMEOUT:
                info["online"] = False
                info["updatedAt"] = now_iso()
                sid = info.get("sid")
                if sid:
                    sid_terminal_map.pop(sid, None)
                await emit_terminal_control(
                    info["userId"],
                    info["terminalId"],
                    "terminal.offline",
                    {
                        "terminalName": info.get("terminalName") or info["terminalId"],
                        "reason": "service_heartbeat_timeout",
                        "statusSource": "terminal_service"
                    }
                )


@app.on_event("startup")
async def on_startup():
    global terminal_monitor_task
    if terminal_monitor_task is None or terminal_monitor_task.done():
        terminal_monitor_task = asyncio.create_task(terminal_heartbeat_monitor())
        logger.info("terminal heartbeat monitor started")


@app.on_event("shutdown")
async def on_shutdown():
    global terminal_monitor_task
    if terminal_monitor_task:
        terminal_monitor_task.cancel()
        try:
            await terminal_monitor_task
        except asyncio.CancelledError:
            pass
        terminal_monitor_task = None


app.include_router(strategy_router, prefix="/api")
app.include_router(backtest_router, prefix="/api")
app.include_router(preview_router, prefix="/api")
app.include_router(trading_router)

EXTERNAL_API = "http://192.168.66.141:8000"


@app.get("/strategy_info")
async def get_strategy_info():
    """获取策略配置"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{EXTERNAL_API}/strategy_info")
            if response.status_code == 200:
                return response.json()
            return {"switchSta": False, "buy_5m": 0, "sell_5m": 0}
    except Exception as e:
        logger.error(f"获取策略配置失败: {e}")
        return {"switchSta": False, "buy_5m": 0, "sell_5m": 0}


@app.post("/strategy_action")
async def strategy_action(request: dict):
    """策略操作"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{EXTERNAL_API}/strategy_action", json=request)
            if response.status_code == 200:
                return {"code": 0, "message": "success"}
            return {"code": 1, "message": "操作失败"}
    except Exception as e:
        logger.error(f"策略操作失败: {e}")
        return {"code": 1, "message": str(e)}


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
