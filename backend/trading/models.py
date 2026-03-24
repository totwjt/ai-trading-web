"""
股票交易服务 - 数据库模型
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Index

from common.database import Base


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