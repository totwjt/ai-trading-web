"""
数据库配置模块
提供 SQLAlchemy 异步引擎和会话管理
"""

import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator

# 数据库连接 URL (根据实际环境配置)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres@localhost:5432/tushare_sync",
)

# 创建异步引擎
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # 生产环境设为 False
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

# 创建会话工厂
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """SQLAlchemy 声明性基类"""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    依赖注入函数 - 获取数据库会话
    
    用于 FastAPI 路由中:
    @app.get("/items")
    async def get_items(db: AsyncSession = Depends(get_db)):
        ...
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """初始化数据库 - 创建所有表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 运行存量迁移
    await run_migrations()


async def run_migrations():
    """运行数据库迁移（安全地添加缺失的列 + 数据回填）"""
    async with engine.begin() as conn:
        # strategies 表新增 uid 字段（冗余字段，对应 users.uid）
        await conn.execute(text(
            "ALTER TABLE strategies ADD COLUMN IF NOT EXISTS uid VARCHAR(64)"
        ))

        # 回填存量数据的 uid（通过 users.id 映射 users.uid）
        await conn.execute(text("""
            UPDATE strategies
            SET uid = (SELECT uid FROM users WHERE id = strategies.user_id)
            WHERE uid IS NULL OR uid = ''
        """))


async def close_db():
    """关闭数据库连接"""
    await engine.dispose()
