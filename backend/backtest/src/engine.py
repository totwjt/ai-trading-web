"""
Backtrader 回测引擎封装

提供异步回测执行能力
"""

import asyncio
import logging
import traceback
from datetime import datetime
from typing import Optional, Callable, Dict, Any, List

import backtrader as bt

from backend.backtest.src.models import (
    Backtest, BacktestStatus, BacktestTrade, BacktestLog, EquityCurve, LogLevel
)

logger = logging.getLogger(__name__)


class BacktestCallbacks:
    """回测回调函数集合"""
    
    def __init__(
        self,
        on_progress: Optional[Callable[[int, str], None]] = None,
        on_log: Optional[Callable[[str, str, str], None]] = None
    ):
        self.on_progress = on_progress
        self.on_log = on_log
    
    def progress(self, progress: int, message: str = ""):
        if self.on_progress:
            self.on_progress(progress, message)
    
    def log(self, level: str, message: str):
        if self.on_log:
            self.on_log(level, message)


class BacktestEngine:
    """
    Backtrader 回测引擎
    
    封装 Backtrader 的 Cerebro，提供异步执行和结果收集能力
    """
    
    def __init__(
        self,
        strategy_code: str,
        start_date: str,
        end_date: str,
        initial_capital: float = 1000000.0,
        commission: float = 0.0003,
        benchmark_code: str = "000300.SH"
    ):
        self.strategy_code = strategy_code
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.commission = commission
        self.benchmark_code = benchmark_code
        
        self.cerebro = None
        self.results = {}
        self.trades = []
        self.logs = []
        self.equity_curve = []
        
    def _create_cerebro(self) -> bt.Cerebro:
        """创建 Cerebro 实例"""
        cerebro = bt.Cerebro()
        
        cerebro.broker.setcash(self.initial_capital)
        cerebro.broker.setcommission(commission=self.commission)
        
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
        cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")
        
        return cerebro
    
    def _load_data(self, cerebro: bt.Cerebro, symbols: List[str]):
        """
        加载数据
        
        注意: 实际项目中应该从 PostgreSQL 加载数据
        这里使用 Backtrader 的数据源
        """
        for symbol in symbols:
            data = bt.feeds.GenericCSVData(
                dataname=f"data/{symbol}.csv",
                fromdate=datetime.strptime(self.start_date, "%Y-%m-%d"),
                todate=datetime.strptime(self.end_date, "%Y-%m-%d"),
                dtformat="%Y-%m-%d",
                datetime=0,
                open=1,
                high=2,
                low=3,
                close=4,
                volume=5,
                openinterest=-1
            )
            cerebro.adddata(data)
    
    def _create_strategy(self, cerebro: bt.Cerebro):
        """
        创建策略实例
        
        从策略代码动态创建策略类
        """
        namespace = {}
        exec(self.strategy_code, namespace)
        
        strategy_class = None
        for name, obj in namespace.items():
            if isinstance(obj, type) and issubclass(obj, bt.Strategy) and obj != bt.Strategy:
                strategy_class = obj
                break
        
        if strategy_class:
            cerebro.addstrategy(strategy_class)
        else:
            raise ValueError("策略代码中未找到有效的策略类")
    
    async def run(
        self,
        callbacks: Optional[BacktestCallbacks] = None,
        is_preview: bool = False
    ) -> Dict[str, Any]:
        """
        执行回测
        
        Args:
            callbacks: 回调函数
            is_preview: 是否为预览模式（缩短时间范围）
        """
        if callbacks is None:
            callbacks = BacktestCallbacks()
        
        try:
            callbacks.log(LogLevel.INFO.value, "Cerebro engine initialized.")
            callbacks.progress(5, "初始化完成")
            
            callbacks.log(LogLevel.INFO.value, f"Loading data feeds...")
            callbacks.progress(10, "加载数据")
            
            self.cerebro = self._create_cerebro()
            
            callbacks.log(LogLevel.INFO.value, "Adding Strategy to Brain.")
            callbacks.progress(20, "添加策略")
            
            self._create_strategy(self.cerebro)
            
            callbacks.log(LogLevel.INFO.value, "Starting backtest loop...")
            callbacks.progress(30, "开始回测")
            
            initial_value = self.cerebro.broker.getvalue()
            
            results = await asyncio.get_event_loop().run_in_executor(
                None, self.cerebro.run
            )
            
            callbacks.progress(90, "计算结果")
            
            final_value = self.cerebro.broker.getvalue()
            
            callbacks.log(LogLevel.SUCCESS.value, f"Backtest completed.")
            callbacks.progress(100, "回测完成")
            
            self.results = {
                "initial_value": initial_value,
                "final_value": final_value,
                "total_return": ((final_value - initial_value) / initial_value) * 100,
                "final_equity": final_value
            }
            
            return self.results
            
        except Exception as e:
            error_msg = f"Backtest failed: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            callbacks.log(LogLevel.ERROR.value, error_msg)
            raise
    
    def get_trades(self) -> List[Dict[str, Any]]:
        """获取交易记录"""
        return self.trades
    
    def get_equity_curve(self) -> List[Dict[str, Any]]:
        """获取权益曲线"""
        return self.equity_curve


class BacktestExecutor:
    """
    回测任务执行器
    
    管理回测任务的异步执行和状态更新
    """
    
    def __init__(self):
        self._running_tasks: Dict[int, asyncio.Task] = {}
        self._cancel_flags: Dict[int, bool] = {}
    
    async def execute(
        self,
        backtest_id: int,
        strategy_code: str,
        params: Dict[str, Any],
        db_session,
        callbacks: Optional[BacktestCallbacks] = None
    ) -> Dict[str, Any]:
        """
        执行回测任务
        
        Args:
            backtest_id: 回测记录ID
            strategy_code: 策略代码
            params: 回测参数
            db_session: 数据库会话
            callbacks: 回调函数
        """
        from backend.backtest.src.models import Backtest
        
        self._cancel_flags[backtest_id] = False
        
        engine = BacktestEngine(
            strategy_code=strategy_code,
            start_date=params.get("start_date"),
            end_date=params.get("end_date"),
            initial_capital=params.get("initial_capital", 1000000.0),
            commission=params.get("commission", 0.0003)
        )
        
        async def progress_callback(progress: int, message: str):
            if self._cancel_flags.get(backtest_id, False):
                raise asyncio.CancelledError()
            
            backtest = await db_session.get(Backtest, backtest_id)
            if backtest:
                backtest.progress = progress
                await db_session.commit()
        
        async def log_callback(level: str, message: str):
            log_entry = BacktestLog(
                backtest_id=backtest_id,
                log_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                level=LogLevel(level),
                message=message
            )
            db_session.add(log_entry)
            await db_session.commit()
        
        engine.callbacks = BacktestCallbacks(
            on_progress=progress_callback,
            on_log=log_callback
        )
        
        try:
            results = await engine.run(callbacks)
            
            backtest = await db_session.get(Backtest, backtest_id)
            if backtest:
                backtest.status = BacktestStatus.COMPLETED
                backtest.progress = 100
                backtest.final_equity = results.get("final_equity")
                backtest.total_return = results.get("total_return")
                backtest.execution_time = results.get("execution_time", 0)
                backtest.completed_at = datetime.now()
                await db_session.commit()
            
            return results
            
        except asyncio.CancelledError:
            backtest = await db_session.get(Backtest, backtest_id)
            if backtest:
                backtest.status = BacktestStatus.CANCELLED
                await db_session.commit()
            return {"status": "cancelled"}
        
        except Exception as e:
            backtest = await db_session.get(Backtest, backtest_id)
            if backtest:
                backtest.status = BacktestStatus.FAILED
                backtest.error_message = str(e)
                await db_session.commit()
            raise
    
    def cancel(self, backtest_id: int):
        """取消回测任务"""
        self._cancel_flags[backtest_id] = True
        if backtest_id in self._running_tasks:
            self._running_tasks[backtest_id].cancel()


executor = BacktestExecutor()
