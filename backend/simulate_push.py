"""
自选股票实时行情推送客户端
使用统一 Socket.IO 客户端连接到主服务

用法:
    python simulate_push.py              # 模拟推送测试数据
    python simulate_push.py --real      # 真实推送外部 API 数据
"""

import asyncio
import argparse
import logging
from datetime import datetime

import httpx

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.socketio_client import UnifiedSocketIOClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

EXTERNAL_API = "http://192.168.66.141:8000"
SOCKETIO_URL = "http://localhost:8766"


class ZixuanPusher:
    """自选股票行情推送器"""

    def __init__(self, url: str = SOCKETIO_URL):
        self.client = UnifiedSocketIOClient(
            url=url,
            client_type="zixuan_pusher"
        )
        self.push_interval = 5

    async def connect(self) -> bool:
        return await self.client.connect()

    async def disconnect(self):
        await self.client.disconnect()

    async def fetch_real_data(self) -> list:
        """从外部 API 获取真实自选数据"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as http:
                response = await http.get(f"{EXTERNAL_API}/stock/realtime")
                if response.status_code == 200:
                    data = response.json()
                    return data.get("data", [])
                else:
                    logger.error(f"外部API请求失败: {response.status_code}")
                    return []
        except Exception as e:
            logger.error(f"获取外部数据失败: {e}")
            return []

    async def push_mock_data(self):
        """推送模拟数据"""
        mock_data = [
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
                "trade_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
                "trade_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            {
                "ts_code": "600519.SH",
                "name": "贵州茅台",
                "pre_close": 1680.00,
                "high": 1700.00,
                "open": 1685.00,
                "low": 1675.00,
                "close": 1698.00,
                "change": 18.00,
                "change_pct": 1.07,
                "vol": 500000,
                "amount": 845000000,
                "trade_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        ]

        success = await self.client.push_to_topic("zixuan", mock_data)
        if success:
            logger.info(f"✅ 推送模拟数据成功: {len(mock_data)} 条")
        else:
            logger.error("❌ 推送模拟数据失败")

        return success

    async def push_real_data(self):
        """推送真实外部数据"""
        data = await self.fetch_real_data()
        if data:
            success = await self.client.push_to_topic("zixuan", data)
            if success:
                logger.info(f"✅ 推送真实数据成功: {len(data)} 条")
            else:
                logger.error("❌ 推送真实数据失败")
            return success
        return False

    async def run(self, mode: str = "mock", interval: int = 5):
        """运行推送循环"""
        self.push_interval = interval

        if not await self.connect():
            logger.error("连接失败，退出")
            return

        logger.info(f"开始推送自选数据 (模式: {mode}, 间隔: {interval}秒)")

        try:
            while True:
                if mode == "real":
                    await self.push_real_data()
                else:
                    await self.push_mock_data()

                await asyncio.sleep(self.push_interval)

        except asyncio.CancelledError:
            logger.info("推送任务取消")
        except KeyboardInterrupt:
            logger.info("收到中断信号")
        finally:
            await self.disconnect()
            logger.info("推送器已停止")


async def main():
    parser = argparse.ArgumentParser(description="自选股票行情推送")
    parser.add_argument("--real", action="store_true", help="使用真实外部API数据")
    parser.add_argument("--url", default=SOCKETIO_URL, help="Socket.IO服务地址")
    parser.add_argument("--interval", type=int, default=5, help="推送间隔(秒)")

    args = parser.parse_args()

    pusher = ZixuanPusher(url=args.url)
    mode = "real" if args.real else "mock"

    await pusher.run(mode=mode, interval=args.interval)


if __name__ == "__main__":
    asyncio.run(main())
