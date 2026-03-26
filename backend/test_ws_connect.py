"""
WebSocket 连接测试 - 快速测试能否连接到服务器
用法: python test_ws_connect.py
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common.socketio_client import UnifiedSocketIOClient


async def test_connect():
    server_url = input("请输入服务器地址 (直接回车使用默认 http://localhost:8766): ").strip() or "http://localhost:8766"
    
    print(f"正在连接到 {server_url}...")
    
    client = UnifiedSocketIOClient(
        url=server_url,
        client_type="test_connection"
    )
    
    connected = await client.connect()
    
    if connected:
        print("✅ 连接成功!")
        
        print("订阅 risk topic...")
        await client.subscribe(['risk'])
        await asyncio.sleep(1)
        
        print("✅ 订阅成功!")
        print("测试完成，连接已关闭")
        
        await client.disconnect()
    else:
        print("❌ 连接失败")
        return False
    
    return True


if __name__ == "__main__":
    asyncio.run(test_connect())
