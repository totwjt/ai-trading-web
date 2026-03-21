"""
策略与回测系统数据库模型

表结构:
- Strategy: 用户策略
- Backtest: 回测记录
- BacktestTrade: 回测交易明细
- BacktestLog: 回测系统日志
- EquityCurve: 净值曲线数据点
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime, 
    ForeignKey, Enum as SQLEnum, JSON, Boolean, Index
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from common.database import Base


class StrategyStatus(str, Enum):
    """策略状态枚举"""
    RUNNING = "running"      # 运行中
    PAUSED = "paused"        # 已暂停
    STOPPED = "stopped"      # 已停止
    ERROR = "error"          # 错误


class BacktestStatus(str, Enum):
    """回测状态枚举"""
    PENDING = "pending"      # 等待中
    RUNNING = "running"      # 运行中
    COMPLETED = "completed"   # 已完成
    FAILED = "failed"        # 失败
    CANCELLED = "cancelled"  # 已取消


class TradeDirection(str, Enum):
    """交易方向枚举"""
    BUY = "buy"
    SELL = "sell"


class LogLevel(str, Enum):
    """日志级别枚举"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    SUCCESS = "SUCCESS"


class Strategy(Base):
    """
    策略表
    
    存储用户的量化交易策略
    """
    __tablename__ = "strategies"
    
    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # 基本信息
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="策略名称")
    strategy_type: Mapped[str] = mapped_column(String(50), nullable=True, comment="策略类型")
    
    # 用户ID (写死)
    user_id: Mapped[int] = mapped_column(Integer, default=1, comment="用户ID")
    
    # 策略状态
    status: Mapped[StrategyStatus] = mapped_column(
        SQLEnum(StrategyStatus), 
        default=StrategyStatus.PAUSED,
        comment="策略状态"
    )
    
    # 策略代码 (Python)
    code: Mapped[str] = mapped_column(Text, nullable=False, comment="策略代码")
    
    # 策略配置 (JSON)
    config: Mapped[dict] = mapped_column(JSON, default=dict, comment="策略配置")
    
    # 描述
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="策略描述")
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        server_default=func.now(),
        comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间"
    )
    
    # 关系
    backtests: Mapped[List["Backtest"]] = relationship(
        "Backtest", 
        back_populates="strategy",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<Strategy(id={self.id}, name='{self.name}', status='{self.status}')>"


class Backtest(Base):
    """
    回测记录表
    
    存储每次回测的参数和结果
    """
    __tablename__ = "backtests"
    
    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # 关联策略
    strategy_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("strategies.id", ondelete="CASCADE"),
        nullable=False,
        comment="关联策略ID"
    )
    
    # 用户ID
    user_id: Mapped[int] = mapped_column(Integer, default=1, comment="用户ID")
    
    # 回测状态
    status: Mapped[BacktestStatus] = mapped_column(
        SQLEnum(BacktestStatus),
        default=BacktestStatus.PENDING,
        comment="回测状态"
    )
    
    # 回测参数
    start_date: Mapped[str] = mapped_column(String(10), nullable=False, comment="开始日期")
    end_date: Mapped[str] = mapped_column(String(10), nullable=False, comment="结束日期")
    initial_capital: Mapped[float] = mapped_column(Float, default=1000000.0, comment="初始资金")
    frequency: Mapped[str] = mapped_column(String(10), default="1d", comment="数据频率")
    
    # 回测结果
    final_equity: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="期末权益")
    total_return: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="总收益率(%)")
    benchmark_return: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="基准收益率(%)")
    annual_return: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="年化收益率(%)")
    max_drawdown: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="最大回撤(%)")
    sharpe_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="夏普比率")
    win_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="胜率(%)")
    profit_loss_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="盈亏比")
    
    # 扩展指标 (JSON)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict, comment="扩展性能指标")
    
    # 错误信息
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="错误信息")
    
    # 进度 (0-100)
    progress: Mapped[int] = mapped_column(Integer, default=0, comment="回测进度")
    
    # 执行时间
    execution_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="执行时间(秒)")
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        comment="创建时间"
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="开始时间")
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="完成时间")
    
    # 关系
    strategy: Mapped["Strategy"] = relationship("Strategy", back_populates="backtests")
    trades: Mapped[List["BacktestTrade"]] = relationship(
        "BacktestTrade",
        back_populates="backtest",
        cascade="all, delete-orphan"
    )
    logs: Mapped[List["BacktestLog"]] = relationship(
        "BacktestLog",
        back_populates="backtest",
        cascade="all, delete-orphan"
    )
    equity_curve: Mapped[List["EquityCurve"]] = relationship(
        "EquityCurve",
        back_populates="backtest",
        cascade="all, delete-orphan"
    )
    
    # 索引
    __table_args__ = (
        Index("idx_backtests_strategy_id", "strategy_id"),
        Index("idx_backtests_user_id", "user_id"),
        Index("idx_backtests_status", "status"),
        Index("idx_backtests_created_at", "created_at"),
    )
    
    def __repr__(self):
        return f"<Backtest(id={self.id}, strategy_id={self.strategy_id}, status='{self.status}')>"


class BacktestTrade(Base):
    """
    回测交易明细表
    
    存储回测产生的每笔交易
    """
    __tablename__ = "backtest_trades"
    
    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # 关联回测
    backtest_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("backtests.id", ondelete="CASCADE"),
        nullable=False,
        comment="关联回测ID"
    )
    
    # 交易信息
    trade_time: Mapped[str] = mapped_column(String(30), nullable=False, comment="成交时间")
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, comment="股票代码")
    name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="股票名称")
    direction: Mapped[TradeDirection] = mapped_column(
        SQLEnum(TradeDirection),
        nullable=False,
        comment="交易方向"
    )
    price: Mapped[float] = mapped_column(Float, nullable=False, comment="成交价格")
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, comment="成交数量")
    amount: Mapped[float] = mapped_column(Float, nullable=False, comment="成交金额")
    commission: Mapped[float] = mapped_column(Float, default=0.0, comment="手续费")
    profit: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="盈亏")
    
    # 关系
    backtest: Mapped["Backtest"] = relationship("Backtest", back_populates="trades")
    
    # 索引
    __table_args__ = (
        Index("idx_trades_backtest_id", "backtest_id"),
        Index("idx_trades_symbol", "symbol"),
    )
    
    def __repr__(self):
        return f"<BacktestTrade(id={self.id}, symbol='{self.symbol}', direction='{self.direction}')>"


class BacktestLog(Base):
    """
    回测系统日志表
    
    存储回测执行过程中的日志
    """
    __tablename__ = "backtest_logs"
    
    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # 关联回测
    backtest_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("backtests.id", ondelete="CASCADE"),
        nullable=False,
        comment="关联回测ID"
    )
    
    # 日志信息
    log_time: Mapped[str] = mapped_column(String(30), nullable=False, comment="日志时间")
    level: Mapped[LogLevel] = mapped_column(SQLEnum(LogLevel), nullable=False, comment="日志级别")
    message: Mapped[str] = mapped_column(Text, nullable=False, comment="日志内容")
    
    # 关系
    backtest: Mapped["Backtest"] = relationship("Backtest", back_populates="logs")
    
    # 索引
    __table_args__ = (
        Index("idx_logs_backtest_id", "backtest_id"),
    )
    
    def __repr__(self):
        return f"<BacktestLog(id={self.id}, level='{self.level}')>"


class EquityCurve(Base):
    """
    净值曲线数据点表
    
    存储回测的权益曲线数据
    """
    __tablename__ = "equity_curves"
    
    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # 关联回测
    backtest_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("backtests.id", ondelete="CASCADE"),
        nullable=False,
        comment="关联回测ID"
    )
    
    # 数据点
    date: Mapped[str] = mapped_column(String(10), nullable=False, comment="日期")
    equity: Mapped[float] = mapped_column(Float, nullable=False, comment="策略权益")
    benchmark: Mapped[float] = mapped_column(Float, nullable=False, comment="基准权益")
    returns: Mapped[float] = mapped_column(Float, default=0.0, comment="日收益率(%)")
    
    # 关系
    backtest: Mapped["Backtest"] = relationship("Backtest", back_populates="equity_curve")
    
    # 索引
    __table_args__ = (
        Index("idx_equity_backtest_id", "backtest_id"),
        Index("idx_equity_date", "date"),
    )
    
    def __repr__(self):
        return f"<EquityCurve(id={self.id}, date='{self.date}')>"
