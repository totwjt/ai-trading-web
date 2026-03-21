"""
WebSocket 服务 - 回测进度推送

提供回测进度的实时 WebSocket 推送
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Set, Optional

from fastapi import WebSocket
from websockets import WebSocketServerProtocol

logger = logging.getLogger(__name__)


class WebSocketManager:
    """WebSocket 连接管理器"""
    
    def __init__(self):
        self._connections: Dict[str, Set[WebSocket]] = {}
        self._client_info: Dict[WebSocket, Dict] = {}
        self._lock = asyncio.Lock()
    
    async def connect(
        self, 
        websocket: WebSocket,
        client_id: Optional[str] = None,
        client_type: str = "web"
    ):
        """接受 WebSocket 连接"""
        await websocket.accept()
        
        async with self._lock:
            topic = f"backtest"
            if topic not in self._connections:
                self._connections[topic] = set()
            self._connections[topic].add(websocket)
            
            self._client_info[websocket] = {
                "client_id": client_id,
                "client_type": client_type,
                "connected_at": datetime.now().isoformat(),
                "topics": {topic}
            }
        
        logger.info(f"WebSocket connected: {client_type} - {client_id}")
        
        await self._send_system_message(
            websocket,
            "connected",
            {"server_time": datetime.now().isoformat()}
        )
    
    async def disconnect(self, websocket: WebSocket):
        """断开 WebSocket 连接"""
        async with self._lock:
            client_info = self._client_info.pop(websocket, {})
            topics = client_info.get("topics", set())
            
            for topic in topics:
                if topic in self._connections:
                    self._connections[topic].discard(websocket)
                    if not self._connections[topic]:
                        del self._connections[topic]
        
        logger.info(f"WebSocket disconnected: {client_info.get('client_id')}")
    
    async def subscribe(self, websocket: WebSocket, topics: list):
        """订阅主题"""
        async with self._lock:
            if websocket in self._client_info:
                self._client_info[websocket]["topics"].update(topics)
                for topic in topics:
                    if topic not in self._connections:
                        self._connections[topic] = set()
                    self._connections[topic].add(websocket)
        
        await self._send_system_message(
            websocket,
            "subscribed",
            {"topics": topics}
        )
    
    async def broadcast_backtest_progress(
        self,
        backtest_id: int,
        progress: int,
        current_date: Optional[str] = None,
        equity: Optional[float] = None
    ):
        """广播回测进度"""
        message = {
            "type": "backtest_progress",
            "payload": {
                "backtest_id": backtest_id,
                "progress": progress,
                "current_date": current_date,
                "equity": equity
            },
            "timestamp": datetime.now().isoformat()
        }
        
        topic = f"backtest.{backtest_id}"
        await self._broadcast(topic, message)
    
    async def broadcast_backtest_completed(
        self,
        backtest_id: int,
        status: str,
        results: Dict
    ):
        """广播回测完成"""
        message = {
            "type": "backtest_completed",
            "payload": {
                "backtest_id": backtest_id,
                "status": status,
                "results": results
            },
            "timestamp": datetime.now().isoformat()
        }
        
        topic = f"backtest.{backtest_id}"
        await self._broadcast(topic, message)
    
    async def broadcast_backtest_log(
        self,
        backtest_id: int,
        level: str,
        message: str,
        log_time: Optional[str] = None
    ):
        """广播回测日志"""
        message_data = {
            "type": "backtest_log",
            "payload": {
                "backtest_id": backtest_id,
                "level": level,
                "message": message,
                "time": log_time or datetime.now().strftime("%H:%M:%S")
            },
            "timestamp": datetime.now().isoformat()
        }
        
        topic = f"backtest.{backtest_id}"
        await self._broadcast(topic, message_data)
    
    async def _broadcast(self, topic: str, message: Dict):
        """向订阅者广播消息"""
        if topic not in self._connections:
            return
        
        disconnected = set()
        
        for websocket in self._connections[topic]:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.add(websocket)
        
        for ws in disconnected:
            await self.disconnect(ws)
    
    async def _send_system_message(
        self,
        websocket: WebSocket,
        status: str,
        payload: Dict
    ):
        """发送系统消息"""
        try:
            await websocket.send_json({
                "type": "system",
                "payload": {
                    "status": status,
                    **payload
                },
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Failed to send system message: {e}")


ws_manager = WebSocketManager()


async def websocket_handler(websocket: WebSocket):
    """WebSocket 消息处理"""
    await ws_manager.connect(websocket)
    
    try:
        async for message in websocket.iter_json():
            msg_type = message.get("type")
            payload = message.get("payload", {})
            
            if msg_type == "subscribe":
                topics = payload.get("topics", [])
                await ws_manager.subscribe(websocket, topics)
            
            elif msg_type == "heartbeat":
                await websocket.send_json({
                    "type": "heartbeat",
                    "payload": {
                        "status": "pong",
                        "server_time": datetime.now().isoformat()
                    }
                })
            
            elif msg_type == "push":
                data = payload.get("data", {})
                topic = payload.get("topic")
                if topic:
                    await ws_manager._broadcast(topic, data)
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await ws_manager.disconnect(websocket)
