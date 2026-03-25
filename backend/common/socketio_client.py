"""
统一 Socket.IO 客户端
用于服务间通信和服务端推送
"""

import asyncio
import logging
from typing import Optional, Callable, Any
from datetime import datetime

import socketio

logger = logging.getLogger(__name__)


class UnifiedSocketIOClient:
    """
    统一 Socket.IO 客户端
    封装连接、重连、心跳、订阅、推送等常用功能
    """
    
    def __init__(
        self,
        url: str = "http://localhost:8766",
        client_type: str = "python_service",
        client_id: Optional[str] = None,
        auto_reconnect: bool = True,
        heartbeat_interval: int = 25,
    ):
        self.url = url
        self.client_type = client_type
        self.client_id = client_id or f"{client_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.auto_reconnect = auto_reconnect
        
        self._sio: Optional[socketio.AsyncClient] = None
        self._handlers: dict = {}
        self._connected = False
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._heartbeat_interval = heartbeat_interval
        
        self._on_connect_callbacks = []
        self._on_disconnect_callbacks = []
        self._on_error_callbacks = []
    
    @property
    def is_connected(self) -> bool:
        return self._connected
    
    async def connect(self) -> bool:
        """连接到 Socket.IO 服务"""
        try:
            self._sio = socketio.AsyncClient(
                reconnection=self.auto_reconnect,
                reconnection_attempts=10,
                reconnection_delay=1,
                reconnection_delay_max=30,
            )
            
            self._setup_event_handlers()
            
            logger.info(f"[SocketIO Client] 连接到 {self.url}")
            await self._sio.connect(
                self.url,
                transports=['websocket'],
                wait=True,
                namespaces=['/'],
            )
            
            await self._on_connected()
            return True
            
        except Exception as e:
            logger.error(f"[SocketIO Client] 连接失败: {e}")
            self._notify_error(e)
            return False
    
    def _setup_event_handlers(self):
        """设置 Socket.IO 事件处理器"""
        if not self._sio:
            return
        
        @self._sio.event
        async def connect():
            logger.info(f"[SocketIO Client] 已连接 SID: {self._sio.sid}")
        
        @self._sio.event
        async def connected(data):
            logger.info(f"[SocketIO Client] 服务器确认: {data}")
            self._connected = True
            self._notify_connect()
        
        @self._sio.event
        async def disconnect():
            logger.info("[SocketIO Client] 连接断开")
            self._connected = False
            self._notify_disconnect()
        
        @self._sio.event
        async def connect_error(data):
            logger.error(f"[SocketIO Client] 连接错误: {data}")
            self._notify_error(Exception(str(data)))
        
        @self._sio.event
        async def subscribed(data):
            logger.info(f"[SocketIO Client] 订阅确认: {data}")
        
        @self._sio.event
        async def push_ack(data):
            logger.debug(f"[SocketIO Client] 推送确认: {data}")
        
        @self._sio.event
        async def heartbeat(data):
            logger.debug(f"[SocketIO Client] 心跳: {data}")
        
        for event_name, handler in self._handlers.items():
            self._sio.on(event_name)(handler)
    
    async def _on_connected(self):
        """连接成功后的处理"""
        self._connected = True
        self._notify_connect()
        await self.subscribe([])
    
    async def disconnect(self):
        """断开连接"""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None
        
        if self._sio:
            await self._sio.disconnect()
            self._sio = None
        
        self._connected = False
    
    async def subscribe(self, topics: list):
        """订阅主题"""
        if not self._sio or not self._connected:
            logger.warning("[SocketIO Client] 未连接，无法订阅")
            return False
        
        try:
            await self._sio.emit('subscribe', {'topics': topics})
            logger.info(f"[SocketIO Client] 已订阅主题: {topics}")
            return True
        except Exception as e:
            logger.error(f"[SocketIO Client] 订阅失败: {e}")
            return False
    
    async def unsubscribe(self, topics: list):
        """取消订阅"""
        if not self._sio or not self._connected:
            return False
        
        try:
            await self._sio.emit('unsubscribe', {'topics': topics})
            logger.info(f"[SocketIO Client] 已取消订阅: {topics}")
            return True
        except Exception as e:
            logger.error(f"[SocketIO Client] 取消订阅失败: {e}")
            return False
    
    async def emit(self, event: str, data: Any = None):
        """发送消息"""
        if not self._sio or not self._connected:
            logger.warning(f"[SocketIO Client] 未连接，无法发送 {event}")
            return False
        
        try:
            await self._sio.emit(event, data)
            logger.debug(f"[SocketIO Client] 已发送 {event}: {str(data)[:100]}...")
            return True
        except Exception as e:
            logger.error(f"[SocketIO Client] 发送失败: {e}")
            return False
    
    async def push_to_topic(self, topic: str, data: Any):
        """
        推送数据到指定主题
        用于向服务端推送数据（如外部数据源推送自选行情）
        """
        return await self.emit('push_from_external', {
            'topic': topic,
            'data': data
        })
    
    def on(self, event: str, handler: Callable):
        """注册事件处理器"""
        self._handlers[event] = handler
        if self._sio:
            self._sio.on(event)(handler)
        return self
    
    def on_connect(self, callback: Callable):
        """连接成功回调"""
        self._on_connect_callbacks.append(callback)
        return self
    
    def on_disconnect(self, callback: Callable):
        """断开连接回调"""
        self._on_disconnect_callbacks.append(callback)
        return self
    
    def on_error(self, callback: Callable):
        """错误回调"""
        self._on_error_callbacks.append(callback)
        return self
    
    def _notify_connect(self):
        for cb in self._on_connect_callbacks:
            try:
                if asyncio.iscoroutinefunction(cb):
                    asyncio.create_task(cb())
                else:
                    cb()
            except Exception as e:
                logger.error(f"[SocketIO Client] connect callback error: {e}")
    
    def _notify_disconnect(self):
        for cb in self._on_disconnect_callbacks:
            try:
                if asyncio.iscoroutinefunction(cb):
                    asyncio.create_task(cb())
                else:
                    cb()
            except Exception as e:
                logger.error(f"[SocketIO Client] disconnect callback error: {e}")
    
    def _notify_error(self, error: Exception):
        for cb in self._on_error_callbacks:
            try:
                if asyncio.iscoroutinefunction(cb):
                    asyncio.create_task(cb(error))
                else:
                    cb(error)
            except Exception as e:
                logger.error(f"[SocketIO Client] error callback error: {e}")
    
    async def wait(self):
        """等待连接断开"""
        if self._sio:
            await self._sio.wait()


async def create_client(
    url: str = "http://localhost:8766",
    client_type: str = "python_service",
) -> UnifiedSocketIOClient:
    """创建并连接客户端"""
    client = UnifiedSocketIOClient(url=url, client_type=client_type)
    await client.connect()
    return client
