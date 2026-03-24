import asyncio
import json
from recommendation.models import WSMessage, MessageType

async def simulate_external_push():
    """模拟外部服务器推送自选股票实时行情"""
    import websockets
    
    uri = "ws://localhost:8765"
    
    async with websockets.connect(uri) as ws:
        # 1. 先建立连接
        connect_msg = WSMessage(
            type=MessageType.CONNECT,
            payload={
                "client_id": "test_client",
                "client_type": "zixuan",
                "action": "default"
            }
        )
        await ws.send(connect_msg.to_json())
        print("Sent connect message")
        
        # 等待连接响应
        response = await ws.recv()
        print(f"Connect response: {response}")
        
        # 等待几秒让服务器准备好
        await asyncio.sleep(1)
        
        # 2. 模拟外部服务器推送消息
        push_data = [
            {
                "ts_code": "600831.SH",
                "name": "广电网络",
                "pre_close": 3.62,
                "high": 3.85,
                "open": 3.74,
                "low": 3.65,
                "close": 3.85,
                "change": 0.23,
                "change_pct": 6.35,
                "vol": 18000000,
                "amount": 68000000,
                "trade_time": "2026-03-24 18:10:00"
            },
            {
                "ts_code": "000001.SZ",
                "name": "平安银行",
                "pre_close": 10.45,
                "high": 10.95,
                "open": 10.50,
                "low": 10.40,
                "close": 10.95,
                "change": 0.50,
                "change_pct": 4.78,
                "vol": 20000000,
                "amount": 215000000,
                "trade_time": "2026-03-24 18:10:00"
            }
        ]
        
        push_msg = WSMessage(
            type=MessageType.PUSH,
            payload={
                "target_type": "web",
                "target_action": "zixuan",
                "data": push_data
            }
        )
        await ws.send(push_msg.to_json())
        print("Sent push message")
        
        # 等待推送响应
        response = await ws.recv()
        print(f"Push response: {response}")

if __name__ == "__main__":
    asyncio.run(simulate_external_push())