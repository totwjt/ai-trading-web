import argparse
import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import select

from common.database import async_session_maker
from backtest.src.engine import BacktestEngine
from backtest.src.models import BacktestTrade, TradeDirection
from backtest.src.reconciliation import compare_trade_sequences, simulate_juejin_bollinger_trades


def _format_trade_row(trade: Dict[str, Any]) -> str:
    return (
        f"{trade['time']} | {trade['type']:<4} | {trade['code']} | "
        f"price={trade['price']:.6f} | qty={trade['quantity']}"
    )


async def _load_bt_trades(backtest_id: int) -> List[Dict[str, Any]]:
    async with async_session_maker() as session:
        rows = (
            await session.execute(
                select(BacktestTrade)
                .where(BacktestTrade.backtest_id == backtest_id)
                .order_by(BacktestTrade.trade_time.asc(), BacktestTrade.id.asc())
            )
        ).scalars().all()

    return [
        {
            "time": row.trade_time,
            "code": row.symbol,
            "type": "BUY" if row.direction == TradeDirection.BUY else "SELL",
            "price": float(row.price),
            "quantity": int(row.quantity),
            "amount": float(row.amount),
            "commission": float(row.commission or 0.0),
        }
        for row in rows
    ]


async def main() -> None:
    parser = argparse.ArgumentParser(description="对比掘金布林线策略与 BT 回测交易明细")
    parser.add_argument("--backtest-id", type=int, required=True, help="要对账的 BT 回测 ID")
    parser.add_argument("--symbol", default="600004.SH", help="标的代码，默认 600004.SH")
    parser.add_argument("--start-date", default="2024-03-01", help="开始日期 YYYY-MM-DD")
    parser.add_argument("--end-date", default="2026-03-01", help="结束日期 YYYY-MM-DD")
    parser.add_argument("--initial-capital", type=float, default=100000.0, help="初始资金")
    parser.add_argument("--commission", type=float, default=0.0003, help="手续费率")
    parser.add_argument("--min-commission", type=float, default=5.0, help="最低手续费")
    parser.add_argument("--adjust-mode", default="qfq", help="复权方式")
    parser.add_argument("--limit", type=int, default=10, help="比较前 N 笔交易")
    args = parser.parse_args()

    engine = BacktestEngine(
        strategy_code="",
        start_date=args.start_date,
        end_date=args.end_date,
        initial_capital=args.initial_capital,
        commission=args.commission,
        min_commission=args.min_commission,
        adjust_mode=args.adjust_mode,
        symbols=[args.symbol],
        match_mode="close",
    )

    frame = await engine._load_price_frame(args.symbol)
    juejin_trades = simulate_juejin_bollinger_trades(
        frame,
        args.symbol,
        commission_rate=args.commission,
        min_commission=args.min_commission,
    )
    bt_trades = await _load_bt_trades(args.backtest_id)
    comparison = compare_trade_sequences(juejin_trades, bt_trades, limit=args.limit)

    print("=== JUEJIN SIMULATED TRADES ===")
    for trade in juejin_trades[: args.limit]:
        print(_format_trade_row(trade))

    print("\n=== BT STORED TRADES ===")
    for trade in bt_trades[: args.limit]:
        print(_format_trade_row(trade))

    print("\n=== COMPARISON ===")
    matched = 0
    for row in comparison:
        if row["matched"]:
            matched += 1
        print(
            f"{row['index']:02d}. "
            f"exp={row['expected_time']} {row['expected_type']} @{row['expected_price']} "
            f"| act={row['actual_time']} {row['actual_type']} @{row['actual_price']} "
            f"| qty {row['expected_quantity']} vs {row['actual_quantity']} "
            f"| price_diff={row['price_diff']} | matched={row['matched']}"
        )

    print(
        f"\nMatched {matched}/{min(args.limit, len(juejin_trades), len(bt_trades))} "
        f"trades in the first {args.limit} comparisons."
    )


if __name__ == "__main__":
    asyncio.run(main())
