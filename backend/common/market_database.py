"""
行情数据库配置模块

仅用于读取行情与股票基础信息表：
- stock_daily
- stock_adj_factor
- index_daily
- stock_basic
"""

import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


MARKET_DATA_DATABASE_URL_ENV = "MARKET_DATA_DATABASE_URL"

MARKET_DATA_DATABASE_URL = os.getenv(MARKET_DATA_DATABASE_URL_ENV, "").strip()

if MARKET_DATA_DATABASE_URL:
    market_engine = create_async_engine(
        MARKET_DATA_DATABASE_URL,
        echo=False,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
    )

    market_async_session_maker = async_sessionmaker(
        market_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
else:
    market_engine = None
    market_async_session_maker = None


def _require_market_session_maker() -> async_sessionmaker[AsyncSession]:
    if market_async_session_maker is None:
        raise RuntimeError(f"{MARKET_DATA_DATABASE_URL_ENV} 未配置，无法访问行情数据库")
    return market_async_session_maker


async def get_market_db() -> AsyncGenerator[AsyncSession, None]:
    """获取行情数据库会话。"""
    session_maker = _require_market_session_maker()
    async with session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_market_db():
    """关闭行情数据库连接。"""
    if market_engine is not None:
        await market_engine.dispose()
