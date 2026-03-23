"""
Backtrader 回测引擎封装

提供基于 PostgreSQL 真实行情数据的回测执行能力。
"""

import asyncio
import logging
import traceback
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, List, Optional

import backtrader as bt
import pandas as pd
from sqlalchemy import text

from common.database import async_session_maker
from backtest.src.models import (
    Backtest,
    BacktestLog,
    BacktestStatus,
    BacktestTrade,
    EquityCurve,
    LogLevel,
    TradeDirection,
)

logger = logging.getLogger(__name__)

DEFAULT_BACKTEST_SYMBOLS = ["000001.SZ"]
DEFAULT_PREVIEW_SYMBOLS = ["000001.SZ", "000002.SZ", "600000.SH"]
MAX_FULL_BACKTEST_SYMBOLS = 100


def _date_to_db(value: str) -> str:
    return value.replace("-", "")


def _date_from_db(value: str) -> str:
    return f"{value[0:4]}-{value[4:6]}-{value[6:8]}"


def _get_history_start_date(start_date: str, lookback_days: int = 60) -> str:
    """计算历史数据开始日期（回测开始前N天）"""
    from datetime import datetime, timedelta
    dt = datetime.strptime(start_date, "%Y-%m-%d")
    dt = dt - timedelta(days=lookback_days)
    return dt.strftime("%Y-%m-%d")


def _to_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    return float(value)


class BacktestCallbacks:
    """回测回调函数集合"""

    def __init__(
        self,
        on_progress: Optional[Callable[[int, str], Awaitable[None]]] = None,
        on_log: Optional[Callable[[str, str], Awaitable[None]]] = None
    ):
        self.on_progress = on_progress
        self.on_log = on_log

    async def progress(self, progress: int, message: str = ""):
        if self.on_progress:
            await self.on_progress(progress, message)

    async def log(self, level: str, message: str):
        if self.on_log:
            await self.on_log(level, message)


class EquityRecorderMixin:
    """为用户策略补充净值曲线与交易记录。"""

    def __init__(self, *args, **kwargs):
        self._equity_history: List[Dict[str, Any]] = []
        self._trade_history: List[Dict[str, Any]] = []
        super().__init__(*args, **kwargs)

    def _record_equity_snapshot(self):
        current_dt = bt.num2date(self.datas[0].datetime[0]).date().isoformat()
        current_equity = float(self.broker.getvalue())
        if self._equity_history and self._equity_history[-1]["date"] == current_dt:
            self._equity_history[-1]["equity"] = current_equity
            return
        self._equity_history.append({"date": current_dt, "equity": current_equity})

    def prenext(self):
        super_method = getattr(super(), "prenext", None)
        if callable(super_method):
            super_method()
        self._record_equity_snapshot()

    def nextstart(self):
        super_method = getattr(super(), "nextstart", None)
        if callable(super_method):
            super_method()
        self._record_equity_snapshot()

    def next(self):
        super().next()
        self._record_equity_snapshot()

    def notify_order(self, order):
        super_method = getattr(super(), "notify_order", None)
        if callable(super_method):
            super_method(order)

        if order.status != order.Completed:
            return

        direction = TradeDirection.BUY if order.isbuy() else TradeDirection.SELL
        pnl = getattr(order.executed, "pnl", None)
        current_dt = bt.num2date(order.executed.dt).strftime("%Y-%m-%d %H:%M:%S")

        self._trade_history.append(
            {
                "time": current_dt,
                "code": getattr(order.data, "_name", "UNKNOWN"),
                "name": getattr(order.data, "_name", None),
                "type": direction.value.upper(),
                "price": float(order.executed.price),
                "quantity": int(abs(order.executed.size)),
                "amount": float(abs(order.executed.price * order.executed.size)),
                "profit": float(pnl) if pnl is not None else None,
                "commission": float(order.executed.comm or 0.0),
            }
        )


class BacktestEngine:
    """
    Backtrader 回测引擎

    基于 PostgreSQL 行情数据构建 Backtrader 数据源。
    """

    def __init__(
        self,
        strategy_code: str,
        start_date: str,
        end_date: str,
        initial_capital: float = 1000000.0,
        commission: float = 0.0003,
        benchmark_code: str = "000300.SH",
        frequency: str = "1d",
        symbols: Optional[List[str]] = None,
    ):
        self.strategy_code = strategy_code
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.commission = commission
        self.benchmark_code = benchmark_code
        self.frequency = frequency
        self.symbols = symbols or []

        self.cerebro: Optional[bt.Cerebro] = None
        self.results: Dict[str, Any] = {}
        self.trades: List[Dict[str, Any]] = []
        self.equity_curve: List[Dict[str, Any]] = []

    def _create_cerebro(self) -> bt.Cerebro:
        cerebro = bt.Cerebro()
        cerebro.broker.setcash(self.initial_capital)
        cerebro.broker.setcommission(commission=self.commission)
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
        cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")
        return cerebro

    async def _resolve_symbols(self, max_symbols: Optional[int]) -> List[str]:
        requested_symbols = [symbol for symbol in self.symbols if symbol]
        if requested_symbols:
            if max_symbols is None:
                return requested_symbols
            return requested_symbols[:max_symbols]

        async with async_session_maker() as session:
            # 完整回测：限制最多 MAX_FULL_BACKTEST_SYMBOLS 只，数据量 >= 50
            if max_symbols is None:
                rows = await session.execute(
                    text(
                        """
                        select ts_code
                        from stock_daily
                        where trade_date between :start_date and :end_date
                        group by ts_code
                        having count(*) >= 50
                        order by ts_code
                        limit :limit_num
                        """
                    ),
                    {
                        "start_date": _date_to_db(self.start_date),
                        "end_date": _date_to_db(self.end_date),
                        "limit_num": MAX_FULL_BACKTEST_SYMBOLS,
                    }
                )
                symbols = [row[0] for row in rows.fetchall()]
                await session.commit()
                return symbols

            # 预览模式：使用候选列表
            candidates = DEFAULT_PREVIEW_SYMBOLS
            rows = await session.execute(
                text(
                    """
                    select distinct ts_code
                    from stock_daily
                    where trade_date between :start_date and :end_date
                      and ts_code = any(:candidates)
                    order by ts_code
                    """
                ),
                {
                    "start_date": _date_to_db(self.start_date),
                    "end_date": _date_to_db(self.end_date),
                    "candidates": candidates,
                }
            )
            symbols = [row[0] for row in rows.fetchall()]
            if symbols:
                return symbols[:max_symbols]

            # fallback: 从时间区间内获取
            fallback_rows = await session.execute(
                text(
                    """
                    select ts_code
                    from stock_daily
                    where trade_date between :start_date and :end_date
                    group by ts_code
                    order by ts_code
                    limit :limit_num
                    """
                ),
                {
                    "start_date": _date_to_db(self.start_date),
                    "end_date": _date_to_db(self.end_date),
                    "limit_num": max_symbols,
                }
            )
            symbols = [row[0] for row in fallback_rows.fetchall()]
            await session.commit()
            return symbols

    async def _load_price_frame(self, symbol: str) -> pd.DataFrame:
        async with async_session_maker() as session:
            rows = await session.execute(
                text(
                    """
                    select
                        sd.trade_date,
                        sd.open,
                        sd.high,
                        sd.low,
                        sd.close,
                        sd.vol as volume,
                        sd.amount,
                        saf.adj_factor
                    from stock_daily sd
                    left join stock_adj_factor saf
                      on saf.ts_code = sd.ts_code
                     and saf.trade_date = sd.trade_date
                    where sd.ts_code = :symbol
                      and sd.trade_date between :hist_start_date and :end_date
                    order by sd.trade_date
                    """
                ),
                {
                    "symbol": symbol,
                    "hist_start_date": _date_to_db(_get_history_start_date(self.start_date)),
                    "end_date": _date_to_db(self.end_date),
                }
            )
            records = rows.mappings().all()
            await session.commit()

        if not records:
            raise ValueError(f"未找到 {symbol} 在 {self.start_date} ~ {self.end_date} 的行情数据")

        frame = pd.DataFrame(records)
        frame["datetime"] = pd.to_datetime(frame["trade_date"], format="%Y%m%d")
        frame["open"] = frame["open"].astype(float)
        frame["high"] = frame["high"].astype(float)
        frame["low"] = frame["low"].astype(float)
        frame["close"] = frame["close"].astype(float)
        frame["volume"] = frame["volume"].astype(float)
        frame["amount"] = frame["amount"].astype(float)
        frame["adj_factor"] = frame["adj_factor"].ffill().fillna(1.0).astype(float)
        frame = frame[["datetime", "open", "high", "low", "close", "volume", "amount", "adj_factor"]]
        frame.set_index("datetime", inplace=True)
        return frame

    async def _load_benchmark_series(self) -> Dict[str, float]:
        async with async_session_maker() as session:
            rows = await session.execute(
                text(
                    """
                    select trade_date, close
                    from index_daily
                    where ts_code = :benchmark_code
                      and trade_date between :start_date and :end_date
                    order by trade_date
                    """
                ),
                {
                    "benchmark_code": self.benchmark_code,
                    "start_date": _date_to_db(self.start_date),
                    "end_date": _date_to_db(self.end_date),
                }
            )
            records = rows.fetchall()
            await session.commit()

        if not records:
            return {}

        initial_close = float(records[0][1])
        benchmark_map: Dict[str, float] = {}
        for trade_date, close in records:
            trade_date_iso = _date_from_db(trade_date)
            benchmark_map[trade_date_iso] = self.initial_capital * (float(close) / initial_close)
        return benchmark_map

    async def _load_data(self, cerebro: bt.Cerebro, symbols: List[str]):
        class SqlPandasData(bt.feeds.PandasData):
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

        for symbol in symbols:
            frame = await self._load_price_frame(symbol)
            cerebro.adddata(SqlPandasData(dataname=frame, name=symbol))

    def _create_strategy(self, cerebro: bt.Cerebro):
        namespace = {}
        exec(self.strategy_code, namespace)

        user_strategy_class = None
        for _, obj in namespace.items():
            if isinstance(obj, type) and issubclass(obj, bt.Strategy) and obj != bt.Strategy:
                user_strategy_class = obj
                break

        if not user_strategy_class:
            raise ValueError("策略代码中未找到有效的策略类")

        wrapped_strategy = type(
            f"{user_strategy_class.__name__}Wrapped",
            (EquityRecorderMixin, user_strategy_class),
            {}
        )
        cerebro.addstrategy(wrapped_strategy)

    def _build_equity_curve(
        self,
        equity_history: List[Dict[str, Any]],
        benchmark_map: Dict[str, float]
    ):
        if not equity_history:
            self.equity_curve = []
            return

        last_benchmark = self.initial_capital
        curve: List[Dict[str, Any]] = []
        for point in equity_history:
            benchmark_value = benchmark_map.get(point["date"], last_benchmark)
            last_benchmark = benchmark_value
            returns = ((point["equity"] - self.initial_capital) / self.initial_capital) * 100
            curve.append(
                {
                    "date": point["date"],
                    "equity": point["equity"],
                    "benchmark": benchmark_value,
                    "returns": returns,
                }
            )
        self.equity_curve = curve

    async def run(
        self,
        callbacks: Optional[BacktestCallbacks] = None,
        is_preview: bool = False
    ) -> Dict[str, Any]:
        if callbacks is None:
            callbacks = BacktestCallbacks()

        try:
            await callbacks.log(LogLevel.INFO.value, "Cerebro engine initialized.")
            await callbacks.progress(5, "初始化完成")

            self.cerebro = self._create_cerebro()

            # 编译运行用1只快速验证，完整回测使用全量股票
            max_symbols = 1 if is_preview else None
            symbols = await self._resolve_symbols(max_symbols=max_symbols)
            if not symbols:
                raise ValueError("指定区间内未找到可用股票行情数据")

            await callbacks.log(LogLevel.INFO.value, f"Loading data feeds: {', '.join(symbols)}")
            await callbacks.progress(10, "加载真实行情数据")

            await self._load_data(self.cerebro, symbols)
            benchmark_map = await self._load_benchmark_series()

            await callbacks.log(LogLevel.INFO.value, "Adding Strategy to Brain.")
            await callbacks.progress(20, "加载策略")

            self._create_strategy(self.cerebro)

            await callbacks.log(LogLevel.INFO.value, "Starting backtest loop...")
            await callbacks.progress(30, "开始回测")

            initial_value = float(self.cerebro.broker.getvalue())
            strategy_instances = await asyncio.get_event_loop().run_in_executor(None, self.cerebro.run)

            await callbacks.progress(90, "整理回测结果")

            final_value = float(self.cerebro.broker.getvalue())
            strategy_instance = strategy_instances[0] if strategy_instances else None

            if strategy_instance is not None:
                self.trades = list(getattr(strategy_instance, "_trade_history", []))
                self._build_equity_curve(list(getattr(strategy_instance, "_equity_history", [])), benchmark_map)

            benchmark_return = None
            if self.equity_curve:
                last_point = self.equity_curve[-1]
                benchmark_return = ((last_point["benchmark"] - self.initial_capital) / self.initial_capital) * 100

            metrics = self._extract_metrics(
                strategy_instance,
                initial_value,
                final_value,
                benchmark_return
            )
            self.results = metrics
            return self.results

        except Exception as exc:
            error_msg = f"Backtest failed: {str(exc)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            await callbacks.log(LogLevel.ERROR.value, error_msg)
            raise

    def _extract_metrics(
        self,
        strategy_instance,
        initial_value: float,
        final_value: float,
        benchmark_return: Optional[float]
    ) -> Dict[str, Any]:
        def safe_get(d: dict, *keys, default=None):
            result = d
            for key in keys:
                if isinstance(result, dict):
                    result = result.get(key, default)
                else:
                    return default
            return result
        
        metrics = {
            "initial_value": initial_value,
            "final_value": final_value,
            "final_equity": final_value,
            "total_return": ((final_value - initial_value) / initial_value) * 100 if initial_value > 0 else 0,
            "benchmark_return": benchmark_return,
            "total_trades": 0,
            "annual_return": None,
            "max_drawdown": None,
            "sharpe_ratio": None,
            "win_rate": None,
            "profit_loss_ratio": None,
        }
        
        try:
            returns_analysis = strategy_instance.analyzers.returns.get_analysis()
            annual_return = safe_get(returns_analysis, 'rnorm100', 'avg', default=None)
            if annual_return is not None:
                metrics["annual_return"] = float(annual_return)
            else:
                metrics["annual_return"] = metrics["total_return"]
            
            dd_analysis = strategy_instance.analyzers.drawdown.get_analysis()
            max_dd = safe_get(dd_analysis, 'max', 'drawdown', default=None)
            if max_dd is not None:
                metrics["max_drawdown"] = float(max_dd)
            
            sharpe_analysis = strategy_instance.analyzers.sharpe.get_analysis()
            sharpe = safe_get(sharpe_analysis, 'sharperatio', default=None)
            if sharpe is not None:
                metrics["sharpe_ratio"] = float(sharpe)
            
            trades_analysis = strategy_instance.analyzers.trades.get_analysis()
            
            total_closed = safe_get(trades_analysis, 'total', 'closed', default=0)
            if total_closed and total_closed > 0:
                won = safe_get(trades_analysis, 'won', 'total', default=0)
                metrics["win_rate"] = (won / total_closed) * 100 if won else 0
                metrics["total_trades"] = int(total_closed)
            
            won_pnl = safe_get(trades_analysis, 'won', 'pnl', 'total', default=0)
            lost_pnl = safe_get(trades_analysis, 'lost', 'pnl', 'total', default=0)
            won_count = safe_get(trades_analysis, 'won', 'total', default=0)
            lost_count = safe_get(trades_analysis, 'lost', 'total', default=0)
            
            if won_count > 0 and lost_count > 0:
                avg_win = won_pnl / won_count if won_count > 0 else 0
                avg_loss = abs(lost_pnl / lost_count) if lost_count > 0 else 0
                if avg_loss > 0:
                    metrics["profit_loss_ratio"] = avg_win / avg_loss
            elif won_count > 0 and lost_count == 0:
                metrics["profit_loss_ratio"] = float('inf')
            
        except Exception as e:
            logger.warning(f"提取分析器指标失败: {e}")
        
        return metrics

    def get_trades(self) -> List[Dict[str, Any]]:
        return self.trades

    def get_equity_curve(self) -> List[Dict[str, Any]]:
        return self.equity_curve


class BacktestExecutor:
    """回测任务执行器"""

    def __init__(self):
        self._cancel_flags: Dict[int, bool] = {}

    async def _update_backtest(self, backtest_id: int, **fields):
        async with async_session_maker() as session:
            backtest = await session.get(Backtest, backtest_id)
            if backtest:
                for key, value in fields.items():
                    setattr(backtest, key, value)
                await session.commit()

    async def _insert_log(self, backtest_id: int, level: str, message: str):
        async with async_session_maker() as session:
            session.add(
                BacktestLog(
                    backtest_id=backtest_id,
                    log_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    level=LogLevel(level),
                    message=message,
                )
            )
            await session.commit()

    async def _replace_curve(self, backtest_id: int, curve_points: List[Dict[str, Any]]):
        async with async_session_maker() as session:
            await session.execute(text("delete from equity_curves where backtest_id = :id"), {"id": backtest_id})
            for point in curve_points:
                session.add(
                    EquityCurve(
                        backtest_id=backtest_id,
                        date=point["date"],
                        equity=_to_float(point["equity"]),
                        benchmark=_to_float(point["benchmark"], default=self._initial_capital_from_curve(curve_points)),
                        returns=_to_float(point["returns"]),
                    )
                )
            await session.commit()

    async def _replace_trades(self, backtest_id: int, trades: List[Dict[str, Any]]):
        async with async_session_maker() as session:
            await session.execute(text("delete from backtest_trades where backtest_id = :id"), {"id": backtest_id})
            for trade in trades:
                session.add(
                    BacktestTrade(
                        backtest_id=backtest_id,
                        trade_time=trade["time"],
                        symbol=trade["code"],
                        name=trade.get("name"),
                        direction=TradeDirection.BUY if trade["type"] == "BUY" else TradeDirection.SELL,
                        price=_to_float(trade["price"]),
                        quantity=int(trade["quantity"]),
                        amount=_to_float(trade["amount"]),
                        commission=_to_float(trade["commission"]),
                        profit=_to_float(trade["profit"]) if trade.get("profit") is not None else None,
                    )
                )
            await session.commit()

    def _initial_capital_from_curve(self, curve_points: List[Dict[str, Any]]) -> float:
        if not curve_points:
            return 1000000.0
        first_point = curve_points[0]
        return _to_float(first_point.get("benchmark"), 1000000.0)

    async def execute(
        self,
        backtest_id: int,
        strategy_code: str,
        params: Dict[str, Any],
        db_session=None,
        callbacks: Optional[BacktestCallbacks] = None
    ) -> Dict[str, Any]:
        self._cancel_flags[backtest_id] = False

        engine = BacktestEngine(
            strategy_code=strategy_code,
            start_date=params.get("start_date"),
            end_date=params.get("end_date"),
            initial_capital=params.get("initial_capital", 1000000.0),
            commission=params.get("commission", 0.0003),
            frequency=params.get("frequency", "1d"),
        )

        async def progress_callback(progress: int, message: str):
            if self._cancel_flags.get(backtest_id, False):
                raise asyncio.CancelledError()
            await self._update_backtest(backtest_id, progress=progress)

        async def log_callback(level: str, message: str):
            await self._insert_log(backtest_id, level, message)

        runtime_callbacks = BacktestCallbacks(
            on_progress=progress_callback,
            on_log=log_callback,
        )

        try:
            results = await engine.run(runtime_callbacks, is_preview=False)

            await self._replace_curve(backtest_id, engine.get_equity_curve())
            await self._replace_trades(backtest_id, engine.get_trades())
            await self._update_backtest(
                backtest_id,
                status=BacktestStatus.COMPLETED,
                progress=100,
                final_equity=results.get("final_equity"),
                total_return=results.get("total_return"),
                benchmark_return=results.get("benchmark_return"),
                execution_time=results.get("execution_time", 0),
                completed_at=datetime.now(),
                metrics={"total_trades": results.get("total_trades", 0)},
                error_message=None,
            )
            return results

        except asyncio.CancelledError:
            await self._update_backtest(backtest_id, status=BacktestStatus.CANCELLED)
            return {"status": "cancelled"}

        except Exception as exc:
            await self._update_backtest(
                backtest_id,
                status=BacktestStatus.FAILED,
                error_message=str(exc),
            )
            raise

    def cancel(self, backtest_id: int):
        self._cancel_flags[backtest_id] = True


executor = BacktestExecutor()
