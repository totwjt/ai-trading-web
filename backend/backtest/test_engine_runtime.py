from datetime import datetime

import backtrader as bt
import pandas as pd

from backtest.src.engine import AShareCommissionInfo, BacktestEngine


def test_apply_price_adjustment_qfq_uses_latest_adj_factor():
    engine = BacktestEngine(
        strategy_code="",
        start_date="2024-01-01",
        end_date="2024-01-02",
        adjust_mode="qfq",
    )
    frame = pd.DataFrame(
        {
            "datetime": pd.to_datetime(["2024-01-01", "2024-01-02"]),
            "open": [10.0, 20.0],
            "high": [10.0, 20.0],
            "low": [10.0, 20.0],
            "close": [10.0, 20.0],
            "volume": [100.0, 100.0],
            "amount": [1000.0, 2000.0],
            "adj_factor": [1.0, 2.0],
        }
    )

    adjusted = engine._apply_price_adjustment(frame)

    assert adjusted.iloc[0]["close"] == 5.0
    assert adjusted.iloc[1]["close"] == 20.0
    assert adjusted.iloc[0]["volume"] == 200.0


def test_create_strategy_wrap_allows_indicator_initialization():
    code = """import backtrader as bt

class WrappedIndicatorStrategy(bt.Strategy):
    def __init__(self):
        self.bb = bt.indicators.BollingerBands(self.datas[0].close, period=2, devfactor=1)

    def next(self):
        if len(self) == 2 and not self.position:
            self.buy(size=1)
"""

    engine = BacktestEngine(
        strategy_code=code,
        start_date="2024-01-01",
        end_date="2024-01-03",
        initial_capital=100000,
        symbols=["000001.SZ"],
    )
    cerebro = engine._create_cerebro()

    frame = pd.DataFrame(
        {
            "open": [10.0, 11.0, 12.0],
            "high": [10.5, 11.5, 12.5],
            "low": [9.5, 10.5, 11.5],
            "close": [10.0, 11.0, 12.0],
            "volume": [1000.0, 1000.0, 1000.0],
            "amount": [10000.0, 11000.0, 12000.0],
            "adj_factor": [1.0, 1.0, 1.0],
        },
        index=pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
    )

    class TestFeed(bt.feeds.PandasData):
        lines = ("amount", "adj_factor")
        params = (
            ("datetime", None),
            ("open", "open"),
            ("high", "high"),
            ("low", "low"),
            ("close", "close"),
            ("volume", "volume"),
            ("openinterest", -1),
            ("amount", "amount"),
            ("adj_factor", "adj_factor"),
        )

    cerebro.adddata(TestFeed(dataname=frame, name="000001.SZ"))
    engine._create_strategy(cerebro)

    results = cerebro.run()
    strategy = results[0]

    assert hasattr(strategy, "_equity_history")
    assert len(strategy._equity_history) > 0


def test_create_cerebro_enables_close_matching_mode():
    engine = BacktestEngine(
        strategy_code="",
        start_date="2024-01-01",
        end_date="2024-01-03",
        match_mode="close",
    )

    cerebro = engine._create_cerebro()

    assert cerebro.broker.p.coc is True


def test_create_cerebro_can_disable_minimum_commission():
    commission_info = AShareCommissionInfo(
        commission=0.0003,
        use_min_commission=False,
        min_commission=5.0,
    )
    commission = commission_info._getcommission(size=100, price=10.0, pseudoexec=True)

    assert commission == 0.3


def test_calculate_trade_stats_uses_closed_trade_results():
    engine = BacktestEngine(
        strategy_code="",
        start_date="2024-01-01",
        end_date="2024-01-03",
        commission=0.0003,
        use_min_commission=True,
        min_commission=5.0,
    )
    metrics = {}

    engine._calculate_trade_stats(
        metrics,
        [
            {"time": "2024-01-01 00:00:00", "code": "600004.SH", "type": "BUY", "amount": 1000.0, "commission": 5.0, "profit": 0},
            {"time": "2024-01-02 00:00:00", "code": "600004.SH", "type": "SELL", "amount": 1100.0, "commission": 5.0, "profit": 90.0},
            {"time": "2024-01-03 00:00:00", "code": "600004.SH", "type": "BUY", "amount": 900.0, "commission": 5.0, "profit": 0},
            {"time": "2024-01-04 00:00:00", "code": "600004.SH", "type": "SELL", "amount": 800.0, "commission": 5.0, "profit": -20.0},
        ],
    )

    assert metrics["closed_trades"] == 2
    assert metrics["winning_trades"] == 1
    assert metrics["losing_trades"] == 1
    assert metrics["win_rate"] == 50.0
    assert metrics["total_commission"] == 20.0
    assert round(metrics["total_commission_without_min"], 2) == 1.14
    assert round(metrics["minimum_commission_impact"], 2) == 18.86
