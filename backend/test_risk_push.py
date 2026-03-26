"""
风控数据推送测试程序
模拟接收 risk topic 实时推送

用法:
    python test_risk_push.py              # 模拟推送测试数据
    python test_risk_push.py --interval 5 # 自定义推送间隔
"""

import asyncio
import argparse
import logging
import random
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.socketio_client import UnifiedSocketIOClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

SOCKETIO_URL = "http://localhost:8766"


class RiskPusher:
    """风控数据推送器"""

    def __init__(self, url: str = SOCKETIO_URL):
        self.client = UnifiedSocketIOClient(
            url=url,
            client_type="risk_pusher"
        )
        self.push_interval = 5

    async def connect(self) -> bool:
        return await self.client.connect()

    async def disconnect(self):
        await self.client.disconnect()

    def generate_mock_data(self):
        """生成模拟风控数据"""
        levels = ['紧急', '警告', '提示']
        level_weights = [0.1, 0.3, 0.6]

        stocks = [
            {'name': '宁德时代', 'code': '300750'},
            {'name': '贵州茅台', 'code': '600519'},
            {'name': '比亚迪', 'code': '002594'},
            {'name': '中国平安', 'code': '601318'},
            {'name': '东方财富', 'code': '300059'},
        ]

        events = [
            '触发止损规则',
            '触发止盈规则',
            '行业集中度接近限额',
            '单只股票仓位超限',
            '账户可用资金不足',
            '波动率异常',
            '流动性风险预警',
        ]

        results = [
            '已自动减仓 30%',
            '已自动清仓',
            '已发送预警通知',
            '等待人工确认',
            '已自动平仓',
        ]

        stock = random.choice(stocks)
        level = random.choices(levels, weights=level_weights)[0]
        event = random.choice(events)
        result = random.choice(results) if level == '紧急' else ''

        return {
            'level': level,
            'levelClass': 'text-up' if level == '紧急' else ('text-yellow-600' if level == '警告' else 'text-primary'),
            'borderClass': 'border-l-2 border-up' if level == '紧急' else ('border-l-2 border-yellow-600' if level == '警告' else 'border-l-2 border-primary'),
            'time': datetime.now().strftime('%H:%M:%S'),
            'title': f"{stock['name']} ({stock['code']}) {event}",
            'content': f"AI诊断: 检测到{stock['name']}出现异常波动，触发风控规则。",
            'result': result,
            'stock': stock,
            'timestamp': datetime.now().isoformat()
        }

    async def push_mock_data(self):
        """推送模拟数据"""
        data = self.generate_mock_data()
        success = await self.client.push_to_topic("risk", data)
        if success:
            logger.info(f"✅ 推送风控数据成功: [{data['level']}] {data['title']}")
        else:
            logger.error("❌ 推送风控数据失败")
        return success

    async def run(self, interval: int = 5):
        """运行推送循环"""
        self.push_interval = interval

        if not await self.connect():
            logger.error("连接失败，退出")
            return

        logger.info(f"开始推送风控数据 (间隔: {interval}秒)")

        try:
            while True:
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
    parser = argparse.ArgumentParser(description="风控数据推送测试")
    parser.add_argument("--url", default=SOCKETIO_URL, help="Socket.IO服务地址")
    parser.add_argument("--interval", type=int, default=5, help="推送间隔(秒)")

    args = parser.parse_args()

    pusher = RiskPusher(url=args.url)
    await pusher.run(interval=args.interval)


if __name__ == "__main__":
    asyncio.run(main())
