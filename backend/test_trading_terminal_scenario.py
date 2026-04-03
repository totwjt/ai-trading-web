"""
trading-terminal 场景联调脚本

目标场景:
1. 用户 u_1001 初始 3 个终端上线，页面侧动态订阅并显示在线
2. 新增第 4 个终端后，页面侧自动订阅第 4 个终端通道并显示在线
3. 4 个终端并发推送交易记录，页面侧都能实时收到并统计

运行:
  cd backend
  .venv/bin/python test_trading_terminal_scenario.py
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Set

from common.socketio_client import UnifiedSocketIOClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

SOCKETIO_URL = "http://localhost:8766"
USER_ID = "u_1001"
INITIAL_TERMINALS = ["terminal-node-1", "terminal-node-2", "terminal-node-3"]
NEW_TERMINAL = "terminal-node-4"
ALL_TERMINALS = INITIAL_TERMINALS + [NEW_TERMINAL]


class TradingTerminalScenario:
    def __init__(self) -> None:
        self.web_client = UnifiedSocketIOClient(url=SOCKETIO_URL, client_type="scenario_web")
        self.terminal_clients: Dict[str, UnifiedSocketIOClient] = {}
        self.subscribed_terminal_topics: Set[str] = set()
        self.control_topic = f"trading-terminal.control.{USER_ID}"

        self.online_terminals: Set[str] = set()
        self.received_records: Dict[str, List[dict]] = {t: [] for t in ALL_TERMINALS}

        self._phase1_ready = asyncio.Event()
        self._phase2_ready = asyncio.Event()
        self._phase3_ready = asyncio.Event()

    def terminal_topic(self, terminal_id: str) -> str:
        return f"trading-terminal.{USER_ID}.{terminal_id}"

    async def setup_web_side(self) -> None:
        def on_control(payload):
            if not isinstance(payload, dict):
                return
            event_type = payload.get("eventType")
            terminal_id = payload.get("terminalId")
            if payload.get("userId") != USER_ID or not terminal_id:
                return

            logger.info("[WEB] control event=%s terminal=%s", event_type, terminal_id)

            if event_type in {"terminal.added", "terminal.online"}:
                self.online_terminals.add(terminal_id)
                topic = self.terminal_topic(terminal_id)
                if topic not in self.subscribed_terminal_topics:
                    asyncio.create_task(self.web_client.subscribe([topic]))
                    self.web_client.on(topic, self._make_terminal_handler(terminal_id))
                    self.subscribed_terminal_topics.add(topic)
                    logger.info("[WEB] subscribed terminal topic: %s", topic)

            if event_type == "terminal.removed":
                self.online_terminals.discard(terminal_id)

            if len(self.online_terminals.intersection(INITIAL_TERMINALS)) == 3:
                self._phase1_ready.set()

            if NEW_TERMINAL in self.online_terminals:
                self._phase2_ready.set()

        def on_snapshot(payload):
            if not isinstance(payload, dict):
                return
            if payload.get("userId") != USER_ID:
                return
            terminals = payload.get("terminals") or []
            logger.info("[WEB] snapshot terminals=%s", len(terminals))
            for item in terminals:
                terminal_id = str(item.get("terminalId") or "")
                if not terminal_id:
                    continue
                if bool(item.get("online")):
                    self.online_terminals.add(terminal_id)
                topic = self.terminal_topic(terminal_id)
                if topic not in self.subscribed_terminal_topics:
                    asyncio.create_task(self.web_client.subscribe([topic]))
                    self.web_client.on(topic, self._make_terminal_handler(terminal_id))
                    self.subscribed_terminal_topics.add(topic)
                    logger.info("[WEB] subscribed terminal topic from snapshot: %s", topic)

        self.web_client.on(self.control_topic, on_control)
        self.web_client.on("terminal_snapshot", on_snapshot)

        ok = await self.web_client.connect()
        if not ok:
            raise RuntimeError("web client connect failed")

        await self.web_client.subscribe([self.control_topic])
        await self.web_client.emit("terminal_snapshot_request", {"userId": USER_ID})
        logger.info("[WEB] subscribed control topic and requested snapshot")

    def _make_terminal_handler(self, terminal_id: str):
        def _handler(payload):
            if not isinstance(payload, dict):
                return
            data = payload.get("data") or {}
            event_type = payload.get("eventType")
            if event_type == "trade.record.append":
                self.received_records[terminal_id].append(data)
                logger.info(
                    "[WEB] record received terminal=%s total=%s",
                    terminal_id,
                    len(self.received_records[terminal_id]),
                )
                if all(len(self.received_records[t]) > 0 for t in ALL_TERMINALS):
                    self._phase3_ready.set()

        return _handler

    async def start_terminal(self, terminal_id: str) -> None:
        client = UnifiedSocketIOClient(
            url=SOCKETIO_URL,
            client_type="scenario_terminal",
            client_id=f"scenario_{terminal_id}",
        )
        ok = await client.connect()
        if not ok:
            raise RuntimeError(f"terminal connect failed: {terminal_id}")

        await client.emit(
            "terminal_register",
            {
                "userId": USER_ID,
                "terminalId": terminal_id,
                "terminalName": terminal_id,
            },
        )
        await client.emit(
            "terminal_status_update",
            {
                "userId": USER_ID,
                "terminalId": terminal_id,
                "status": "online",
                "reason": "scenario_register_online",
            },
        )
        self.terminal_clients[terminal_id] = client
        logger.info("[TERM] registered: %s", terminal_id)

    async def heartbeat_once(self, terminal_id: str) -> None:
        client = self.terminal_clients[terminal_id]
        await client.emit(
            "terminal_heartbeat",
            {
                "userId": USER_ID,
                "terminalId": terminal_id,
                "ts": datetime.now().isoformat(),
            },
        )

    async def push_trade_record(self, terminal_id: str, seq: int) -> None:
        client = self.terminal_clients[terminal_id]
        record = {
            "tradeId": f"{terminal_id}-trade-{seq}",
            "time": datetime.now().strftime("%H:%M:%S"),
            "symbol": "600519" if terminal_id.endswith("1") else "601318",
            "name": "贵州茅台" if terminal_id.endswith("1") else "中国平安",
            "side": "buy" if seq % 2 == 1 else "sell",
            "price": 1700 + seq,
            "qty": 100 * seq,
        }
        await client.emit(
            "push_trading_terminal",
            {
                "userId": USER_ID,
                "terminalId": terminal_id,
                "eventType": "trade.record.append",
                "seq": seq,
                "data": record,
            },
        )
        logger.info("[TERM] pushed trade terminal=%s seq=%s", terminal_id, seq)

    async def run(self) -> None:
        await self.setup_web_side()

        for terminal_id in INITIAL_TERMINALS:
            await self.start_terminal(terminal_id)
            await self.heartbeat_once(terminal_id)

        await asyncio.wait_for(self._phase1_ready.wait(), timeout=8)
        logger.info("[PASS] 场景1通过：初始3终端在线且已订阅")

        await self.start_terminal(NEW_TERMINAL)
        await self.heartbeat_once(NEW_TERMINAL)

        await asyncio.wait_for(self._phase2_ready.wait(), timeout=8)
        logger.info("[PASS] 场景2通过：第4终端新增并在线订阅")

        await asyncio.gather(
            *[self.push_trade_record(t, idx + 1) for idx, t in enumerate(ALL_TERMINALS)]
        )

        await asyncio.wait_for(self._phase3_ready.wait(), timeout=8)
        logger.info("[PASS] 场景3通过：4终端均收到实时交易记录")

        logger.info("------ 摘要 ------")
        logger.info("online terminals: %s", sorted(self.online_terminals))
        for terminal_id in ALL_TERMINALS:
            logger.info(
                "terminal=%s records=%s",
                terminal_id,
                len(self.received_records[terminal_id]),
            )

    async def shutdown(self) -> None:
        for terminal_id, client in self.terminal_clients.items():
            try:
                await client.emit(
                    "terminal_unregister",
                    {"userId": USER_ID, "terminalId": terminal_id},
                )
            except Exception:
                pass
            await client.disconnect()

        await self.web_client.disconnect()


async def main() -> None:
    scenario = TradingTerminalScenario()
    try:
        await scenario.run()
    finally:
        await scenario.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
