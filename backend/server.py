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
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from common.database import async_session_maker
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


def log_terminal_event(event: str, **fields: Any) -> None:
    details = " ".join(f"{k}={fields[k]}" for k in sorted(fields.keys()))
    if details:
        logger.info("[terminal] event=%s %s", event, details)
    else:
        logger.info("[terminal] event=%s", event)


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


def normalize_mac(mac_address: str) -> str:
    return mac_address.strip().lower()


def find_terminal_key_by_mac(user_id: str, mac_address: str) -> Optional[str]:
    normalized = normalize_mac(mac_address)
    if not normalized:
        return None

    for key, info in terminal_registry.items():
        if info.get("userId") != user_id:
            continue
        if normalize_mac(str(info.get("macAddress") or "")) == normalized:
            return key
    return None


def resolve_terminal_key(
    sid: str,
    user_id: str,
    terminal_id: str,
    mac_address: str
) -> Optional[str]:
    key = sid_terminal_map.get(sid)
    if key and key in terminal_registry:
        return key

    if user_id and terminal_id:
        key_by_id = terminal_key(user_id, terminal_id)
        if key_by_id in terminal_registry:
            return key_by_id

    if user_id and mac_address:
        return find_terminal_key_by_mac(user_id, mac_address)

    return None


async def find_terminal_from_db_by_mac(user_id: str, mac_address: str) -> Optional[Dict[str, str]]:
    normalized = normalize_mac(mac_address)
    if not user_id or not normalized:
        return None

    query = text(
        """
        SELECT terminal_id, terminal_name, account_name, mac_address
        FROM terminals
        WHERE uid = :uid AND LOWER(mac_address) = :mac
        ORDER BY COALESCE(updated_at, created_at) DESC, id DESC
        LIMIT 1
        """
    )
    try:
        async with async_session_maker() as session:
            result = await session.execute(query, {"uid": user_id, "mac": normalized})
            row = result.fetchone()
            if not row:
                return None
            return {
                "terminalId": str(row[0] or "").strip(),
                "terminalName": str(row[1] or "").strip(),
                "accountName": str(row[2] or "").strip(),
                "macAddress": str(row[3] or "").strip(),
            }
    except Exception as error:
        logger.warning("query terminal from db failed: uid=%s mac=%s error=%s", user_id, normalized, error)
        return None


async def find_db_terminals_by_uid(user_id: str) -> Dict[str, Dict[str, str]]:
    if not user_id:
        return {}

    query = text(
        """
        SELECT terminal_id, terminal_name, account_name, mac_address
        FROM terminals
        WHERE uid = :uid
        """
    )
    result_map: Dict[str, Dict[str, str]] = {}
    try:
        async with async_session_maker() as session:
            result = await session.execute(query, {"uid": user_id})
            for row in result.fetchall():
                mac = normalize_mac(str(row[3] or ""))
                if not mac:
                    continue
                result_map[mac] = {
                    "terminalId": str(row[0] or "").strip(),
                    "terminalName": str(row[1] or "").strip(),
                    "accountName": str(row[2] or "").strip(),
                    "macAddress": str(row[3] or "").strip(),
                }
    except Exception as error:
        logger.warning("query terminals by uid failed: uid=%s error=%s", user_id, error)
    return result_map


def mac_to_terminal_id(mac_address: str) -> str:
    normalized = normalize_mac(mac_address).replace(":", "-").replace(".", "-")
    return f"mac-{normalized}" if normalized else ""


async def ensure_terminal_in_db(
    user_id: str,
    terminal_id: str,
    terminal_name: str,
    mac_address: str,
    account_name: str
) -> Optional[Dict[str, str]]:
    normalized_mac = normalize_mac(mac_address)
    if not user_id or not normalized_mac:
        return None

    requested_terminal_id = terminal_id or mac_to_terminal_id(mac_address)
    requested_terminal_name = terminal_name or requested_terminal_id
    requested_account_name = account_name or ""

    select_by_mac_query = text(
        """
        SELECT id, terminal_id, terminal_name, account_name, mac_address
        FROM terminals
        WHERE uid = :uid AND LOWER(mac_address) = :mac
        ORDER BY COALESCE(updated_at, created_at) DESC, id DESC
        LIMIT 1
        FOR UPDATE
        """
    )
    update_by_id_query = text(
        """
        UPDATE terminals
        SET
          terminal_name = CASE
            WHEN terminal_name IS NULL OR terminal_name = '' THEN :terminal_name
            ELSE terminal_name
          END,
          account_name = CASE
            WHEN account_name IS NULL OR account_name = '' THEN :account_name
            ELSE account_name
          END,
          updated_at = NOW()
        WHERE id = :id
        """
    )
    insert_query = text(
        """
        INSERT INTO terminals (
          uid, terminal_id, terminal_name, mac_address, account_name, active, created_at, updated_at
        )
        VALUES (
          :uid, :terminal_id, :terminal_name, :mac_address, :account_name, TRUE, NOW(), NOW()
        )
        """
    )
    select_by_terminal_id_query = text(
        """
        SELECT uid, terminal_id
        FROM terminals
        WHERE terminal_id = :terminal_id
        LIMIT 1
        """
    )

    try:
        async with async_session_maker() as session:
            async with session.begin():
                result = await session.execute(
                    select_by_mac_query,
                    {"uid": user_id, "mac": normalized_mac}
                )
                row = result.fetchone()
                if row:
                    db_id = row[0]
                    canonical_terminal_id = str(row[1] or "").strip() or requested_terminal_id
                    canonical_terminal_name = str(row[2] or "").strip() or requested_terminal_name
                    canonical_account_name = str(row[3] or "").strip() or requested_account_name
                    canonical_mac = str(row[4] or "").strip() or mac_address
                    await session.execute(
                        update_by_id_query,
                        {
                            "id": db_id,
                            "terminal_name": requested_terminal_name,
                            "account_name": requested_account_name
                        }
                    )
                    return {
                        "terminalId": canonical_terminal_id,
                        "terminalName": canonical_terminal_name,
                        "accountName": canonical_account_name,
                        "macAddress": canonical_mac
                    }

                candidate_terminal_id = requested_terminal_id
                terminal_id_owner = await session.execute(
                    select_by_terminal_id_query,
                    {"terminal_id": candidate_terminal_id}
                )
                owner_row = terminal_id_owner.fetchone()
                if owner_row and str(owner_row[0]) != user_id:
                    candidate_terminal_id = mac_to_terminal_id(mac_address) or candidate_terminal_id

                await session.execute(
                    insert_query,
                    {
                        "uid": user_id,
                        "terminal_id": candidate_terminal_id,
                        "terminal_name": requested_terminal_name or candidate_terminal_id,
                        "mac_address": mac_address,
                        "account_name": requested_account_name
                    }
                )

                return {
                    "terminalId": candidate_terminal_id,
                    "terminalName": requested_terminal_name or candidate_terminal_id,
                    "accountName": requested_account_name,
                    "macAddress": mac_address
                }
    except IntegrityError as error:
        logger.warning("ensure terminal in db integrity error: uid=%s mac=%s error=%s", user_id, mac_address, error)
        return await find_terminal_from_db_by_mac(user_id, mac_address)
    except Exception as error:
        logger.warning("ensure terminal in db failed: uid=%s mac=%s error=%s", user_id, mac_address, error)
        return None


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
        log_terminal_event("disconnect.skip", sid=sid, reason="no_terminal_mapping")
        return

    info = terminal_registry[key]
    if info["online"]:
        info["online"] = False
        info["updatedAt"] = now_iso()
        log_terminal_event(
            "disconnect.offline_emit",
            sid=sid,
            userId=info["userId"],
            terminalId=info["terminalId"],
            macAddress=info.get("macAddress") or "",
            reason="service_disconnect"
        )
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
    status_provided = initial_status in {"online", "offline"}
    log_terminal_event(
        "register.request",
        sid=sid,
        userId=user_id,
        terminalId=terminal_id,
        macAddress=mac_address,
        status=initial_status or "empty",
        statusProvided=status_provided
    )
    if not user_id or not terminal_id:
        await sio.emit(
            "terminal_error",
            {"message": "userId and (terminalId or macAddress) are required"},
            room=sid
        )
        log_terminal_event("register.reject", sid=sid, reason="missing_user_or_terminal")
        return
    if not mac_address:
        await sio.emit(
            "terminal_error",
            {"message": "macAddress is required"},
            room=sid
        )
        log_terminal_event("register.reject", sid=sid, reason="missing_mac_address")
        return

    db_terminal = await ensure_terminal_in_db(
        user_id=user_id,
        terminal_id=terminal_id,
        terminal_name=terminal_name,
        mac_address=mac_address,
        account_name=account_name
    )
    if db_terminal:
        log_terminal_event(
            "register.db_sync",
            sid=sid,
            userId=user_id,
            macAddress=mac_address,
            terminalId=db_terminal.get("terminalId") or "",
            terminalName=db_terminal.get("terminalName") or "",
            accountName=db_terminal.get("accountName") or ""
        )
    else:
        await sio.emit(
            "terminal_error",
            {"message": "register db sync failed"},
            room=sid
        )
        log_terminal_event("register.reject", sid=sid, reason="db_sync_failed")
        return

    requested_key = terminal_key(user_id, terminal_id)
    key = requested_key
    existing_key_by_mac = find_terminal_key_by_mac(user_id, mac_address)
    if existing_key_by_mac:
        log_terminal_event(
            "register.dedupe_hit",
            sid=sid,
            userId=user_id,
            requestedTerminalId=terminal_id,
            existingKey=existing_key_by_mac,
            macAddress=mac_address
        )
        key = existing_key_by_mac
    elif db_terminal and db_terminal.get("terminalId"):
        key = terminal_key(user_id, db_terminal["terminalId"])

    prev = terminal_registry.get(key)
    canonical_terminal_id = (
        prev["terminalId"]
        if prev else
        (db_terminal.get("terminalId") if db_terminal and db_terminal.get("terminalId") else terminal_id)
    )
    terminal_name = (
        (prev["terminalName"] if prev else "")
        or (db_terminal.get("terminalName") if db_terminal else "")
        or get_terminal_name(data)
        or canonical_terminal_id
    )
    mac_address = (
        mac_address
        or (str(prev.get("macAddress") or "") if prev else "")
        or (db_terminal.get("macAddress") if db_terminal else "")
    )
    account_name = (
        (str(prev.get("accountName") or "") if prev else "")
        or (db_terminal.get("accountName") if db_terminal else "")
        or account_name
    )

    if prev and prev.get("sid") and prev["sid"] != sid:
        old_sid = prev["sid"]
        sid_terminal_map.pop(old_sid, None)
        try:
            await sio.disconnect(old_sid)
        except Exception:
            logger.warning("disconnect previous terminal sid failed: %s", old_sid)

    topic = terminal_topic(user_id, canonical_terminal_id)
    control_topic = terminal_control_topic(user_id)
    await sio.enter_room(sid, topic)
    await sio.enter_room(sid, control_topic)

    next_online = prev["online"] if (prev and not status_provided) else (initial_status == "online")
    terminal_registry[key] = {
        "userId": user_id,
        "terminalId": canonical_terminal_id,
        "terminalName": terminal_name,
        "macAddress": mac_address,
        "accountName": account_name,
        "sid": sid,
        # 在线状态由终端 Python 服务主动上报 terminal_status_update
        "online": next_online,
        "statusSource": "terminal_service",
        "connectedAt": prev["connectedAt"] if prev else now_iso(),
        "lastHeartbeatAt": now_iso(),
        "updatedAt": now_iso(),
    }
    sid_terminal_map[sid] = key
    log_terminal_event(
        "register.applied",
        sid=sid,
        key=key,
        isNew=prev is None,
        userId=user_id,
        terminalId=canonical_terminal_id,
        requestedTerminalId=terminal_id,
        macAddress=mac_address,
        accountName=account_name,
        online=next_online
    )

    await sio.emit(
        "terminal_registered",
        {
            "userId": user_id,
            "terminalId": canonical_terminal_id,
            "terminalName": terminal_name,
            "macAddress": mac_address,
            "accountName": account_name,
            "topic": topic,
            "controlTopic": control_topic,
            "status": "ok",
        },
        room=sid
    )

    if not prev:
        log_terminal_event(
            "register.emit_added",
            sid=sid,
            userId=user_id,
            terminalId=canonical_terminal_id,
            macAddress=mac_address
        )
        await emit_terminal_control(
            user_id,
            canonical_terminal_id,
            "terminal.added",
            {
                "terminalName": terminal_name,
                "macAddress": mac_address,
                "accountName": account_name
            }
        )

    if next_online:
        log_terminal_event(
            "register.emit_online",
            sid=sid,
            userId=user_id,
            terminalId=canonical_terminal_id,
            macAddress=mac_address
        )
        await emit_terminal_control(
            user_id,
            canonical_terminal_id,
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
    mac_address = get_mac_address(data)
    status = str(data.get("status") or "").strip().lower()
    reason = str(data.get("reason") or "").strip() or "terminal_service_report"
    log_terminal_event(
        "status_update.request",
        sid=sid,
        userId=user_id,
        terminalId=terminal_id,
        macAddress=mac_address,
        status=status,
        reason=reason
    )

    if not user_id or not terminal_id or status not in {"online", "offline"}:
        await sio.emit(
            "terminal_error",
            {"message": "userId, (terminalId or macAddress) and status(online/offline) are required"},
            room=sid
        )
        log_terminal_event("status_update.reject", sid=sid, reason="invalid_payload")
        return

    key = resolve_terminal_key(sid, user_id, terminal_id, mac_address)
    if not key or key not in terminal_registry:
        await sio.emit("terminal_error", {"message": "terminal not registered"}, room=sid)
        log_terminal_event("status_update.reject", sid=sid, reason="terminal_not_registered")
        return

    info = terminal_registry[key]
    next_online = status == "online"
    if info["online"] == next_online:
        info["updatedAt"] = now_iso()
        log_terminal_event(
            "status_update.noop",
            sid=sid,
            userId=info["userId"],
            terminalId=info["terminalId"],
            status=status
        )
        return

    info["online"] = next_online
    info["updatedAt"] = now_iso()
    log_terminal_event(
        "status_update.applied",
        sid=sid,
        userId=info["userId"],
        terminalId=info["terminalId"],
        macAddress=info.get("macAddress") or "",
        status=status,
        reason=reason
    )
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
    mac_address = get_mac_address(payload)
    if not key:
        key = resolve_terminal_key(sid, user_id, terminal_id, mac_address)

    if key and key in terminal_registry:
        terminal_registry[key]["lastHeartbeatAt"] = now_iso()
        terminal_registry[key]["updatedAt"] = now_iso()
        info = terminal_registry[key]
        log_terminal_event(
            "heartbeat.ok",
            sid=sid,
            userId=info["userId"],
            terminalId=info["terminalId"],
            macAddress=info.get("macAddress") or ""
        )
        await sio.emit("terminal_heartbeat_ack", {"status": "ok", "serverTime": now_iso()}, room=sid)
        return

    await sio.emit("terminal_error", {"message": "terminal not registered (terminalId/macAddress)"}, room=sid)
    log_terminal_event(
        "heartbeat.reject",
        sid=sid,
        userId=user_id,
        terminalId=terminal_id,
        macAddress=mac_address,
        reason="terminal_not_registered"
    )


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
    mac_address = get_mac_address(payload)
    if not key:
        key = resolve_terminal_key(sid, user_id, terminal_id, mac_address)

    if not key or key not in terminal_registry:
        await sio.emit("terminal_error", {"message": "terminal not found (terminalId/macAddress)"}, room=sid)
        log_terminal_event(
            "unregister.reject",
            sid=sid,
            userId=user_id,
            terminalId=terminal_id,
            macAddress=mac_address,
            reason="terminal_not_found"
        )
        return

    info = terminal_registry.pop(key)
    log_terminal_event(
        "unregister.applied",
        sid=sid,
        userId=info["userId"],
        terminalId=info["terminalId"],
        macAddress=info.get("macAddress") or ""
    )
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
        log_terminal_event("snapshot.reject", sid=sid, reason="missing_user")
        return

    control_topic = terminal_control_topic(user_id)
    await sio.enter_room(sid, control_topic)
    snapshot = build_terminal_snapshot(user_id)
    db_terminals = await find_db_terminals_by_uid(user_id)
    if db_terminals:
        for item in snapshot:
            mac = normalize_mac(str(item.get("macAddress") or ""))
            db_item = db_terminals.get(mac)
            if not db_item:
                continue
            if db_item.get("terminalId"):
                item["terminalId"] = db_item["terminalId"]
            if db_item.get("terminalName"):
                item["terminalName"] = db_item["terminalName"]
            if db_item.get("accountName"):
                item["accountName"] = db_item["accountName"]
            if db_item.get("macAddress"):
                item["macAddress"] = db_item["macAddress"]
    log_terminal_event(
        "snapshot.emit",
        sid=sid,
        userId=user_id,
        count=len(snapshot)
    )
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
                log_terminal_event(
                    "monitor.timeout_offline_emit",
                    userId=info["userId"],
                    terminalId=info["terminalId"],
                    macAddress=info.get("macAddress") or "",
                    timeoutSeconds=TERMINAL_HEARTBEAT_TIMEOUT
                )
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
