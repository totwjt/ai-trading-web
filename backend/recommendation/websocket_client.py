"""
智能荐股 WebSocket 客户端
用于其他咨询项目连接和同步数据
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Optional, Callable, Dict, Any
import websockets
from websockets.client import WebSocketClientProtocol

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RecommendationWebSocketClient:
    """WebSocket客户端 - 用于连接智能荐股服务"""
    
    def __init__(
        self,
        uri: str = "ws://localhost:8765",
        client_type: str = "python_client",
        on_message: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_connect: Optional[Callable[[], None]] = None,
        on_disconnect: Optional[Callable[[], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None
    ):
        self.uri = uri
        self.client_type = client_type
        self.websocket: Optional[WebSocketClientProtocol] = None
        self.on_message = on_message
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.on_error = on_error
        self.is_connected = False
        self._running = False
    
    async def connect(self) -> bool:
        """连接到WebSocket服务器"""
        try:
            self.websocket = await websockets.connect(self.uri)
            self.is_connected = True
            self._running = True
            
            connect_msg = {
                "type": "connect",
                "payload": {
                    "client_type": self.client_type,
                    "connected_at": datetime.now().isoformat()
                },
                "timestamp": datetime.now().isoformat(),
                "message_id": f"msg_{datetime.now().timestamp()}"
            }
            await self.websocket.send(json.dumps(connect_msg, ensure_ascii=False))
            
            if self.on_connect:
                self.on_connect()
                
            logger.info(f"已连接到: {self.uri}")
            return True
            
        except Exception as e:
            logger.error(f"连接失败: {e}")
            if self.on_error:
                self.on_error(e)
            return False
    
    async def disconnect(self):
        """断开连接"""
        self._running = False
        self.is_connected = False
        
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception as e:
                logger.error(f"关闭连接失败: {e}")
        
        if self.on_disconnect:
            self.on_disconnect()
        
        logger.info("已断开连接")
    
    async def subscribe(self, topics: list):
        """订阅主题"""
        if not self.is_connected:
            logger.warning("未连接，无法订阅")
            return False
            
        subscribe_msg = {
            "type": "subscribe",
            "payload": {
                "topics": topics,
                "client_type": self.client_type
            },
            "timestamp": datetime.now().isoformat(),
            "message_id": f"msg_{datetime.now().timestamp()}"
        }
        
        await self.websocket.send(json.dumps(subscribe_msg, ensure_ascii=False))
        logger.info(f"已订阅主题: {topics}")
        return True
    
    async def send_heartbeat(self):
        """发送心跳"""
        if not self.is_connected:
            return False
            
        heartbeat_msg = {
            "type": "heartbeat",
            "payload": {"status": "ping"},
            "timestamp": datetime.now().isoformat(),
            "message_id": f"msg_{datetime.now().timestamp()}"
        }
        
        await self.websocket.send(json.dumps(heartbeat_msg, ensure_ascii=False))
        return True
    
    async def send_recommendation(self, data: Dict[str, Any]):
        """发送荐股数据（用于同步给服务器）"""
        if not self.is_connected:
            logger.warning("未连接，无法发送数据")
            return False
            
        message = {
            "type": "recommendation",
            "payload": data,
            "timestamp": datetime.now().isoformat(),
            "message_id": f"msg_{datetime.now().timestamp()}"
        }
        
        await self.websocket.send(json.dumps(message, ensure_ascii=False))
        logger.info(f"已发送荐股数据: {data.get('news', {}).get('title', '')[:30]}...")
        return True
    
    async def receive_loop(self):
        """接收消息循环"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    msg_type = data.get("type")
                    
                    if msg_type == "heartbeat":
                        logger.debug("收到心跳")
                    elif msg_type == "system":
                        logger.info(f"系统消息: {data.get('payload', {})}")
                    elif msg_type == "recommendation":
                        logger.info(f"收到荐股消息: {data.get('payload', {}).get('news', {}).get('title', '')[:30]}...")
                        if self.on_message:
                            self.on_message(data.get("payload", {}))
                    else:
                        logger.info(f"收到消息: {data}")
                        
                except json.JSONDecodeError:
                    logger.error(f"收到无效JSON: {message[:100]}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("连接已关闭")
        except Exception as e:
            logger.error(f"接收消息错误: {e}")
            if self.on_error:
                self.on_error(e)
        finally:
            self.is_connected = False
            if self.on_disconnect:
                self.on_disconnect()
    
    async def run(self):
        """运行客户端"""
        if not await self.connect():
            return
        
        await self.subscribe(["recommendation"])
        
        await self.receive_loop()
    
    async def run_with_heartbeat(self, interval: int = 30):
        """运行客户端并定期发送心跳"""
        if not await self.connect():
            return
        
        await self.subscribe(["recommendation"])
        
        receive_task = asyncio.create_task(self.receive_loop())
        
        while self._running and self.is_connected:
            await asyncio.sleep(interval)
            if self._running and self.is_connected:
                await self.send_heartbeat()
        
        receive_task.cancel()


async def example_handler(data: Dict[str, Any]):
    """示例消息处理器"""
    news = data.get("news", {})
    analysis = data.get("analysis", {})
    
    print("\n" + "="*60)
    print(f"收到新推荐:")
    print(f"标题: {news.get('title', '')}")
    print(f"来源: {news.get('source', '')}")
    print(f"发布时间: {news.get('publish_time', '')}")
    print(f"利好板块: {', '.join(analysis.get('利好版块', []))}")
    print(f"利好股票: {', '.join(analysis.get('利好股票', []))}")
    print("="*60 + "\n")


async def example_sync_data():
    """示例：同步数据到服务器"""
    client = RecommendationWebSocketClient(
        uri="ws://localhost:8765",
        client_type="data_sync_client",
        on_message=example_handler
    )
    
    await client.connect()
    await client.subscribe(["recommendation"])
    
    sample_data = {
        "news": {
            "title": "测试新闻标题",
            "content": "测试内容",
            "publish_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "crawl_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": "测试来源",
            "url": "https://example.com"
        },
        "analysis": {
            "利好版块": ["测试板块1", "测试板块2"],
            "利好股票": ["600000(测试1)", "000001(测试2)"],
            "分析因素": ["测试因素1", "测试因素2"],
            "详细分析": "这是测试分析"
        }
    }
    
    await client.send_recommendation(sample_data)
    
    await asyncio.sleep(5)
    await client.disconnect()


async def example_listen_only():
    """示例：仅监听推荐消息"""
    client = RecommendationWebSocketClient(
        uri="ws://localhost:8765",
        client_type="listener",
        on_message=example_handler,
        on_connect=lambda: print("已连接"),
        on_disconnect=lambda: print("已断开")
    )
    
    await client.run_with_heartbeat(interval=30)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "sync":
        asyncio.run(example_sync_data())
    else:
        asyncio.run(example_listen_only())
