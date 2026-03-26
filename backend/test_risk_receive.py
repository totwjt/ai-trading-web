"""
风控数据接收测试程序
模拟客户端接收 risk topic 实时推送消息
验证后端 WebSocket 推送是否正常工作

用法:
    python test_risk_receive.py
"""

import asyncio
import logging

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common.socketio_client import UnifiedSocketIOClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

SOCKETIO_URL = "http://localhost:8766"


async def main():
    client = UnifiedSocketIOClient(
        url=SOCKETIO_URL,
        client_type="risk_test_receiver"
    )

    received_count = 0

    def on_risk(data):
        nonlocal received_count
        received_count += 1
        logger.info(f"📥 收到 risk 推送 [{received_count}]: {data}")

    client.on('risk', on_risk)

    logger.info(f"正在连接 {SOCKETIO_URL}...")
    
    if await client.connect():
        logger.info("✅ 已连接，订阅 risk topic...")
        await client.subscribe(['risk'])
        
        logger.info("等待接收消息... (按 Ctrl+C 退出)")
        
        try:
            await client.wait()
        except KeyboardInterrupt:
            logger.info("收到中断信号")
    else:
        logger.error("❌ 连接失败")


if __name__ == "__main__":
    asyncio.run(main())
