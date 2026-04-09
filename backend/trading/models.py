"""
股票交易服务 - 数据库模型
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Index, ForeignKey, Boolean, Float

from common.database import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uid = Column(String(64), nullable=False, unique=True, index=True, comment="用户唯一标识")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")


class Terminal(Base):
    """终端表"""
    __tablename__ = "terminals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uid = Column(String(64), ForeignKey("users.uid"), nullable=False, index=True, comment="用户ID外键")
    terminal_id = Column(String(128), nullable=False, unique=True, index=True, comment="终端唯一标识")
    mac_address = Column(String(32), nullable=False, comment="终端设备MAC地址")
    account_name = Column(String(128), nullable=False, comment="终端账号名称(whoami)")
    terminal_name = Column(String(128), nullable=True, comment="终端显示名称")
    active = Column(Boolean, nullable=False, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    __table_args__ = (
        Index("idx_terminal_uid_terminal_id", "uid", "terminal_id"),
    )


class Watchlist(Base):
    """自选股票表"""
    __tablename__ = 'watchlist'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), nullable=False, index=True, comment='股票代码')
    name = Column(String(50), nullable=False, comment='股票名称')
    added_at = Column(DateTime, default=datetime.now, comment='添加时间')

    __table_args__ = (
        Index('idx_user_ts_code', 'ts_code'),
    )


class PendingOrder(Base):
    """挂单表"""
    __tablename__ = "pending_orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uid = Column(String(64), ForeignKey("users.uid"), nullable=False, index=True, comment="用户ID")
    stock_code = Column(String(20), nullable=False, index=True, comment="股票代码")
    stock_name = Column(String(64), nullable=False, comment="股票名称")
    order_price = Column(Float, nullable=False, comment="挂单价格")
    order_quantity = Column(Integer, nullable=False, comment="挂单数量")
    scheduled_at = Column(DateTime, nullable=False, index=True, comment="计划挂单时间")
    status = Column(String(16), nullable=False, default="pending", comment="状态: pending/success/triggered/cancelled")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    __table_args__ = (
        Index("idx_pending_orders_uid_status", "uid", "status"),
        Index("idx_pending_orders_uid_scheduled", "uid", "scheduled_at"),
    )


class PendingOrderConfig(Base):
    """挂单配置表"""
    __tablename__ = "pending_order_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uid = Column(String(64), ForeignKey("users.uid"), nullable=False, unique=True, index=True, comment="用户ID")
    enabled = Column(Boolean, nullable=False, default=True, comment="是否启用挂单")
    default_delay_minutes = Column(Integer, nullable=False, default=10, comment="默认挂单延迟分钟")
    auto_submit = Column(Boolean, nullable=False, default=False, comment="是否自动提交")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
