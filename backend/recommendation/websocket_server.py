"""
智能荐股 WebSocket Server
用于推送实时荐股消息给前端Vue3客户端
支持Python客户端连接进行数据同步
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Set, Dict, Any
import websockets
from websockets.server import WebSocketServerProtocol

from recommendation.models import WSMessage, MessageType, RecommendationMessage, News, Analysis

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

HOST = "0.0.0.0"
PORT = 8765

connected_clients: Set[WebSocketServerProtocol] = set()
client_info: Dict[WebSocketServerProtocol, Dict[str, Any]] = {}


async def register_client(websocket: WebSocketServerProtocol, path: str):
    """注册新的客户端连接"""
    connected_clients.add(websocket)
    client_info[websocket] = {
        "path": path,
        "connected_at": datetime.now().isoformat(),
        "client_type": "unknown"
    }
    logger.info(f"客户端连接: {websocket.remote_address}, 当前连接数: {len(connected_clients)}")
    
    welcome_msg = WSMessage(
        type=MessageType.SYSTEM,
        payload={
            "status": "connected",
            "message": "成功连接到智能荐股服务",
            "server_time": datetime.now().isoformat()
        }
    )
    await websocket.send(welcome_msg.to_json())


async def unregister_client(websocket: WebSocketServerProtocol):
    """注销客户端连接"""
    connected_clients.discard(websocket)
    client_info.pop(websocket, None)
    logger.info(f"客户端断开: 当前连接数: {len(connected_clients)}")


async def handle_client_message(websocket: WebSocketServerProtocol, message: str):
    """处理客户端消息"""
    try:
        ws_msg = WSMessage.from_json(message)
        
        logger.info(f"📥 收到客户端消息: type={ws_msg.type}, payload={json.dumps(ws_msg.payload, ensure_ascii=False)[:200]}")
        
        if ws_msg.type == MessageType.HEARTBEAT:
            response = WSMessage(
                type=MessageType.HEARTBEAT,
                payload={"status": "pong", "server_time": datetime.now().isoformat()}
            )
            await websocket.send(response.to_json())
            logger.info("📤 发送心跳响应")
            
        elif ws_msg.type == MessageType.SUBSCRIBE:
            client_info[websocket].update({
                "client_type": ws_msg.payload.get("client_type", "web"),
                "client_id": ws_msg.payload.get("client_id", ""),
                "action": ws_msg.payload.get("action", "default")
            })
            logger.info(f"📥 客户端订阅: {ws_msg.payload}")
            response = WSMessage(
                type=MessageType.SYSTEM,
                payload={"status": "subscribed", "topics": ws_msg.payload.get("topics", [])}
            )
            await websocket.send(response.to_json())
            
        elif ws_msg.type == MessageType.CONNECT:
            client_info[websocket].update({
                "client_type": ws_msg.payload.get("client_type", "web"),
                "client_id": ws_msg.payload.get("client_id", ""),
                "action": ws_msg.payload.get("action", "default")
            })
            logger.info(f"📥 客户端连接: {ws_msg.payload}")
            
            response = WSMessage(
                type=MessageType.SYSTEM,
                payload={
                    "status": "connected",
                    "client_id": ws_msg.payload.get("client_id", ""),
                    "client_type": ws_msg.payload.get("client_type", "web"),
                    "action": ws_msg.payload.get("action", "default"),
                    "server_time": datetime.now().isoformat()
                }
            )
            await websocket.send(response.to_json())
            logger.info(f"📤 发送连接响应给客户端")
            
        elif ws_msg.type == MessageType.PUSH:
            target_type = ws_msg.payload.get("target_type", "web")
            target_action = ws_msg.payload.get("target_action", "default")
            data = ws_msg.payload.get("data", {})
            logger.info(f"📤 推送给 {target_type}/{target_action}: {data.get('news', {}).get('title', '')[:30]}")
            
            await push_to_client(target_type, target_action, data)
            
            response = WSMessage(
                type=MessageType.SYSTEM,
                payload={"status": "pushed", "target": f"{target_type}/{target_action}"}
            )
            await websocket.send(response.to_json())
            
    except json.JSONDecodeError:
        logger.error(f"收到无效JSON: {message[:100]}")
    except Exception as e:
        logger.error(f"处理消息错误: {e}")


async def broadcast_to_clients(message: WSMessage, client_type: str = None, action: str = None):
    if not connected_clients:
        return
        
    json_msg = message.to_json()
    disconnected = set()
    
    for client in connected_clients:
        info = client_info.get(client, {})
        if client_type and info.get("client_type") != client_type:
            continue
        if action and info.get("action") != action:
            continue
        try:
            await client.send(json_msg)
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            disconnected.add(client)
    
    for client in disconnected:
        await unregister_client(client)


async def push_to_client(target_type: str, target_action: str, data: dict):
    ws_msg = WSMessage(
        type=MessageType.RECOMMENDATION,
        payload=data
    )
    await broadcast_to_clients(ws_msg, client_type=target_type, action=target_action)


async def send_to_specific_client(websocket: WebSocketServerProtocol, message: WSMessage):
    """发送消息给特定客户端"""
    try:
        await websocket.send(message.to_json())
    except Exception as e:
        logger.error(f"发送消息失败: {e}")


async def websocket_handler(websocket: WebSocketServerProtocol):
    """WebSocket 连接处理器"""
    await register_client(websocket, "")
    
    try:
        async for message in websocket:
            await handle_client_message(websocket, message)
    except websockets.exceptions.ConnectionClosed:
        logger.info("连接正常关闭")
    except Exception as e:
        logger.error(f"WebSocket错误: {e}")
    finally:
        await unregister_client(websocket)


async def start_server():
    """启动WebSocket服务器"""
    logger.info(f"启动WebSocket服务: ws://{HOST}:{PORT}")
    async with websockets.serve(websocket_handler, HOST, PORT):
        logger.info(f"WebSocket服务器运行中: ws://{HOST}:{PORT}")
        await asyncio.Future()


async def push_recommendation(data: dict):
    """推送荐股消息给所有前端客户端"""
    ws_msg = WSMessage(
        type=MessageType.RECOMMENDATION,
        payload=data
    )
    await broadcast_to_clients(ws_msg, client_type="web")
    logger.info(f"推送荐股消息: {data.get('news', {}).get('title', '')[:50]}")


async def push_to_all(data: dict):
    """推送消息给前端Web客户端"""
    ws_msg = WSMessage(
        type=MessageType.RECOMMENDATION,
        payload=data
    )
    await broadcast_to_clients(ws_msg, client_type="web")
    logger.info(f"推送消息给前端: {data.get('news', {}).get('title', '')[:50]}")


def load_sample_data():
    try:
        import os
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        v2_path = os.path.join(base_dir, "message-v2.json")
        if os.path.exists(v2_path):
            with open(v2_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                logger.info(f"加载 message-v2.json 格式数据: {len(data)} 条")
                return data
        
        old_path = os.path.join(base_dir, "message.json")
        if os.path.exists(old_path):
            with open(old_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                logger.info(f"加载 message.json 格式数据: {len(data)} 条")
                return data
        
        return []
    except Exception as e:
        logger.error(f"加载示例数据失败: {e}")
        return []


async def push_sample_periodically(interval: int = 10):
    """定时推送示例数据"""
    samples = load_sample_data()
    if not samples:
        logger.warning("没有示例数据可推送")
        return
    
    index = 0
    while True:
        if connected_clients:
            sample = samples[index % len(samples)]
            news = sample.get("news", {})
            news["publish_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            await push_to_all(sample)
            logger.info(f"推送第 {index + 1} 条数据: {news.get('title', '')[:30]}...")
            index += 1
        await asyncio.sleep(interval)


async def start_server_with_pusher(push_interval: int = 10):
    """启动服务器并定时推送数据"""
    logger.info(f"启动WebSocket服务: ws://{HOST}:{PORT}")
    
    server_task = asyncio.create_task(start_server())
    pusher_task = asyncio.create_task(push_sample_periodically(push_interval))
    
    try:
        await asyncio.gather(server_task, pusher_task)
    except asyncio.CancelledError:
        logger.info("服务器停止")


async def test_push_sample():
    """测试推送示例数据"""
    samples = load_sample_data()
    if samples:
        await push_to_all(samples[0])
        logger.info("示例数据推送完成")


if __name__ == "__main__":
    import sys
    
    interval = None
    if len(sys.argv) > 1:
        try:
            interval = int(sys.argv[1])
        except ValueError:
            pass
    
    try:
        if interval is not None and interval > 0:
            asyncio.run(start_server_with_pusher(interval))
        else:
            asyncio.run(start_server())
    except KeyboardInterrupt:
        logger.info("服务器停止")
