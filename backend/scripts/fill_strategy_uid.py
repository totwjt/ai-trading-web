"""
回填 strategies 表中 uid 字段的存量数据

执行 UPDATE strategies SET uid = users.uid 通过 user_id 关联映射。
可多次安全执行（幂等，只更新 uid 为空/空字符串的行）。

用法:
    cd backend && python scripts/fill_strategy_uid.py
"""

import asyncio
import sys
import os

# 确保能 import common.database
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from common.database import engine


async def fill_strategy_uid():
    print("[migration] 开始回填 strategies.uid ...")
    async with engine.begin() as conn:
        # 确保 uid 列存在
        await conn.execute(text(
            "ALTER TABLE strategies ADD COLUMN IF NOT EXISTS uid VARCHAR(64)"
        ))

        # 回填存量的空 uid
        result = await conn.execute(text("""
            UPDATE strategies
            SET uid = (SELECT uid FROM users WHERE id = strategies.user_id)
            WHERE uid IS NULL OR uid = ''
        """))
        print(f"[migration] 回填完成，影响行数: {result.rowcount}")

        # 验证
        verify = await conn.execute(text(
            "SELECT COUNT(*) FROM strategies WHERE uid IS NULL OR uid = ''"
        ))
        remaining = verify.scalar()
        if remaining == 0:
            print("[migration] 所有策略数据 uid 已完整填充 ✓")
        else:
            print(f"[migration] 警告: 仍有 {remaining} 条策略 uid 为空（可能 users 表中缺少对应记录）")


async def main():
    try:
        await fill_strategy_uid()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
