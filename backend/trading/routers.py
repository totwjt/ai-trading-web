"""
股票交易服务 - 股票检索 API
"""

from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import datetime
import logging
import httpx
import re

from common.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
try:
    from pypinyin import Style, lazy_pinyin
except ImportError:  # pragma: no cover - dependency is declared in requirements
    Style = None
    lazy_pinyin = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

trading_router = APIRouter(prefix="/api/trading", tags=["trading"])

EXTERNAL_API = "http://192.168.66.143:8000"
TRADER_API = "http://192.168.66.155:8003"
ORDER_API = "http://192.168.66.135:8000"
TRADE_RECORD_API = "http://192.168.66.135:8001"


# ==================== 数据模型 ====================

class StockSearchResult(BaseModel):
    """股票搜索结果"""
    ts_code: str
    name: str
    industry: Optional[str] = None
    market: Optional[str] = None
    list_date: Optional[str] = None


class StockSearchResponse(BaseModel):
    """股票搜索响应"""
    code: int = 0
    message: str = "success"
    data: List[StockSearchResult]
    total: int = 0
    timestamp: str = ""


class TerminalItem(BaseModel):
    uid: str
    terminal_id: str
    terminal_name: Optional[str] = None
    mac_address: str
    account_name: str
    active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class OrderRequest(BaseModel):
    stock_code: str
    stock_name: str
    price: float
    quantity: int
    position_level: Optional[int] = None


class TerminalRenameRequest(BaseModel):
    uid: str
    terminal_name: str
    terminal_id: Optional[str] = None
    mac_address: Optional[str] = None


class PendingOrderCreateRequest(BaseModel):
    uid: str
    stock_code: str
    stock_name: str
    scheduled_at: str


class PendingOrderUpdateRequest(BaseModel):
    scheduled_at: str


class PendingOrderStatusUpdateRequest(BaseModel):
    status: Literal["pending", "success", "triggered", "cancelled"]
    terminal_id: Optional[str] = None
    remark: Optional[str] = None


class PendingOrderConfigUpsertRequest(BaseModel):
    uid: str
    enabled: bool = True
    default_delay_minutes: int = 10
    auto_submit: bool = False


def get_stock_name_initials(name: str) -> str:
    """生成股票名称首字母简写，例如“平安银行” -> “payh”"""
    if not name:
        return ""

    if lazy_pinyin is None or Style is None:
        return "".join(ch.lower() for ch in name if ch.isascii() and ch.isalnum())

    initials = lazy_pinyin(
        name,
        style=Style.FIRST_LETTER,
        errors=lambda chars: [ch.lower() for ch in chars if ch.isalnum()]
    )
    return "".join(part.lower() for part in initials if part and part.isalnum())


def parse_iso_datetime(value: str) -> datetime:
    raw = str(value or "").strip()
    if not raw:
        raise ValueError("scheduled_at is required")
    normalized = raw.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is not None:
        return parsed.astimezone().replace(tzinfo=None)
    return parsed


def get_stock_match_score(keyword: str, ts_code: str, name: str) -> Optional[int]:
    """返回匹配分值，值越小表示相关性越高"""
    normalized_keyword = keyword.strip().lower()
    normalized_code = (ts_code or "").lower()
    normalized_name = (name or "").lower()
    initials = get_stock_name_initials(name)

    if not normalized_keyword:
        return None
    if normalized_code == normalized_keyword or normalized_name == normalized_keyword:
        return 0
    if normalized_code.startswith(normalized_keyword):
        return 1
    if normalized_name.startswith(normalized_keyword):
        return 2
    if initials.startswith(normalized_keyword):
        return 3
    if normalized_keyword in normalized_code:
        return 4
    if normalized_keyword in normalized_name:
        return 5
    if normalized_keyword in initials:
        return 6
    return None


# ==================== 路由 ====================

@trading_router.get("/stock/search", response_model=StockSearchResponse)
async def search_stocks(
    keyword: str = Query(..., description="搜索关键词，支持股票代码、名称或首字母简写"),
    limit: int = Query(default=20, ge=1, le=100, description="返回结果数量"),
    db: AsyncSession = Depends(get_db)
):
    """
    股票检索 API
    支持按股票代码(ts_code)、名称(name)或股票名称首字母简写查询
    """
    try:
        normalized_keyword = keyword.strip().lower()
        search_pattern = f"%{keyword.strip()}%"
        is_initials_search = bool(re.fullmatch(r"[a-zA-Z]+", keyword.strip()))

        logger.info(
            "Searching stocks: keyword=%s, pattern=%s, limit=%s, initials_search=%s",
            keyword,
            search_pattern,
            limit,
            is_initials_search
        )

        if is_initials_search:
            query = text("""
                SELECT ts_code, name, industry, market, list_date
                FROM stock_basic
            """)
            result = await db.execute(query)
            all_rows = result.fetchall()
            ranked_rows = []

            for row in all_rows:
                score = get_stock_match_score(normalized_keyword, row[0], row[1])
                if score is not None:
                    ranked_rows.append((score, row))

            ranked_rows.sort(key=lambda item: (item[0], item[1][0]))
            rows = [row for _, row in ranked_rows[:limit]]
        else:
            query = text("""
                SELECT ts_code, name, industry, market, list_date
                FROM stock_basic
                WHERE ts_code LIKE :pattern OR name LIKE :pattern
                LIMIT :limit
            """)
            result = await db.execute(query, {"pattern": search_pattern, "limit": limit})
            rows = result.fetchall()

        logger.info(f"Query returned {len(rows)} rows")

        stocks = [
            StockSearchResult(
                ts_code=row[0],
                name=row[1],
                industry=row[2],
                market=row[3],
                list_date=row[4] if row[4] else None
            )
            for row in rows
        ]

        logger.info(f"Returning {len(stocks)} stocks: {[s.ts_code for s in stocks]}")

        return StockSearchResponse(
            code=0,
            message="success",
            data=stocks,
            total=len(stocks),
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"股票搜索失败: {e}")
        return StockSearchResponse(
            code=0,
            message="success",
            data=[],
            total=0,
            timestamp=datetime.now().isoformat()
        )


@trading_router.get("/stock/realtime/{ts_code}", response_model=dict)
async def get_stock_realtime(ts_code: str, db: AsyncSession = Depends(get_db)):
    """
    获取单只股票实时行情
    """
    try:
        query = text("""
            SELECT ts_code, trade_time, open, high, low, close, vol
            FROM stock_daily
            WHERE ts_code = :ts_code
            ORDER BY trade_time DESC
            LIMIT 1
        """)

        result = await db.execute(query, {"ts_code": ts_code})
        row = result.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="股票数据不存在")

        return {
            "ts_code": row[0],
            "trade_time": row[1].strftime("%Y-%m-%d %H:%M:%S") if row[1] else None,
            "open": float(row[2]) if row[2] else 0,
            "high": float(row[3]) if row[3] else 0,
            "low": float(row[4]) if row[4] else 0,
            "close": float(row[5]) if row[5] else 0,
            "vol": int(row[6]) if row[6] else 0
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取实时行情失败: {e}")
        return {
            "ts_code": ts_code,
            "trade_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "open": 0,
            "high": 0,
            "low": 0,
            "close": 0,
            "vol": 0
        }


@trading_router.get("/watchlist")
async def get_watchlist(db: AsyncSession = Depends(get_db)):
    """获取自选股票列表"""
    try:
        logger.info(f"正在请求外部API: {EXTERNAL_API}/stock/realtime")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{EXTERNAL_API}/stock/realtime")

            logger.info(f"外部API响应状态: {response.status_code}")
            if response.status_code != 200:
                logger.error(f"外部API请求失败: {response.status_code}")
                return {
                    "code": 1,
                    "message": f"获取自选列表失败: {response.status_code}",
                    "data": [],
                    "total": 0,
                    "timestamp": datetime.now().isoformat()
                }

            data = response.json()
            items = data.get("data", [])

            if not items:
                return {
                    "code": 0,
                    "message": "success",
                    "data": [],
                    "total": 0,
                    "timestamp": datetime.now().isoformat()
                }

            watchlist_data = []
            for item in items:
                close = item.get("close") or 0
                pre_close = item.get("pre_close") or 0
                change = close - pre_close
                change_pct = (change / pre_close * 100) if pre_close else 0

                watchlist_data.append({
                    "ts_code": item.get("ts_code"),
                    "name": item.get("name"),
                    "pre_close": pre_close,
                    "open": item.get("open"),
                    "high": item.get("high"),
                    "low": item.get("low"),
                    "close": close,
                    "change": change,
                    "change_pct": round(change_pct, 2),
                    "vol": item.get("vol"),
                    "amount": item.get("amount"),
                    "num": item.get("num"),
                    "ask_price1": item.get("ask_price1"),
                    "ask_volume1": item.get("ask_volume1"),
                    "bid_price1": item.get("bid_price1"),
                    "bid_volume1": item.get("bid_volume1"),
                    "trade_time": item.get("trade_time")
                })

            return {
                "code": 0,
                "message": "success",
                "data": watchlist_data,
                "total": len(watchlist_data),
                "timestamp": datetime.now().isoformat()
            }

    except Exception as e:
        logger.error(f"获取自选列表失败: {e}")
        return {
            "code": 1,
            "message": str(e),
            "data": [],
            "total": 0,
            "timestamp": datetime.now().isoformat()
        }


@trading_router.post("/watchlist/{ts_code}")
async def add_watchlist(
    ts_code: str,
    db: AsyncSession = Depends(get_db)
):
    """添加自选股票"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{EXTERNAL_API}/ts_code",
                json={"ts_code": ts_code}
            )
            # 200: 成功
            # 400 + "already exists": 已经是自选了，也算成功
            if response.status_code == 200:
                return {
                    "code": 0,
                    "message": "success",
                    "data": {"ts_code": ts_code},
                    "timestamp": datetime.now().isoformat()
                }
            elif response.status_code == 400:
                try:
                    error_data = response.json()
                    if "already exists" in error_data.get("detail", ""):
                        return {
                            "code": 0,
                            "message": "success",
                            "data": {"ts_code": ts_code},
                            "timestamp": datetime.now().isoformat()
                        }
                except:
                    pass
                return {
                    "code": 1,
                    "message": error_data.get("detail", "添加失败"),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "code": 1,
                    "message": "添加失败",
                    "timestamp": datetime.now().isoformat()
                }
    except Exception as e:
        logger.error(f"添加自选失败: {e}")
        return {
            "code": 1,
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }


@trading_router.delete("/watchlist/{ts_code}")
async def remove_watchlist(ts_code: str, db: AsyncSession = Depends(get_db)):
    """删除自选股票"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(f"{EXTERNAL_API}/ts_code/{ts_code}")
            if response.status_code == 200:
                return {
                    "code": 0,
                    "message": "success",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "code": 1,
                    "message": "删除失败",
                    "timestamp": datetime.now().isoformat()
                }
    except Exception as e:
        logger.error(f"删除自选失败: {e}")
        return {
            "code": 1,
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }


@trading_router.get("/terminals")
async def get_user_terminals(
    uid: str = Query(..., description="用户ID，例如 u_1001"),
    db: AsyncSession = Depends(get_db)
):
    """获取用户终端列表"""
    try:
        query = text(
            """
            SELECT uid, terminal_id, terminal_name, mac_address, account_name, active, created_at, updated_at
            FROM (
              SELECT
                uid,
                terminal_id,
                terminal_name,
                mac_address,
                account_name,
                active,
                created_at,
                updated_at,
                ROW_NUMBER() OVER (
                  PARTITION BY LOWER(mac_address)
                  ORDER BY COALESCE(updated_at, created_at) DESC, id DESC
                ) AS rn
              FROM terminals
              WHERE uid = :uid
            ) dedup
            WHERE rn = 1
            ORDER BY COALESCE(updated_at, created_at) DESC, terminal_id ASC
            """
        )
        result = await db.execute(query, {"uid": uid})
        rows = result.fetchall()

        terminals = [
            TerminalItem(
                uid=row[0],
                terminal_id=row[1],
                terminal_name=row[2],
                mac_address=row[3],
                account_name=row[4],
                active=bool(row[5]),
                created_at=row[6].isoformat() if row[6] else None,
                updated_at=row[7].isoformat() if row[7] else None,
            )
            for row in rows
        ]

        return {
            "code": 0,
            "message": "success",
            "data": terminals,
            "total": len(terminals),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"获取终端列表失败: {e}")
        return {
            "code": 1,
            "message": str(e),
            "data": [],
            "total": 0,
            "timestamp": datetime.now().isoformat()
        }


@trading_router.patch("/terminals/name")
async def update_terminal_name(
    payload: TerminalRenameRequest,
    db: AsyncSession = Depends(get_db)
):
    """更新终端显示名称（优先按 uid+mac_address，fallback uid+terminal_id）"""
    try:
        uid = payload.uid.strip()
        terminal_name = payload.terminal_name.strip()
        terminal_id = (payload.terminal_id or "").strip()
        mac_address = (payload.mac_address or "").strip()

        if not uid or not terminal_name:
            return {
                "code": 1,
                "message": "uid and terminal_name are required",
                "timestamp": datetime.now().isoformat()
            }

        updated = 0
        if mac_address:
            update_by_mac = text(
                """
                UPDATE terminals
                SET terminal_name = :terminal_name, updated_at = NOW()
                WHERE uid = :uid AND LOWER(mac_address) = LOWER(:mac_address)
                """
            )
            result = await db.execute(
                update_by_mac,
                {"uid": uid, "mac_address": mac_address, "terminal_name": terminal_name}
            )
            updated = result.rowcount or 0

        if updated == 0 and terminal_id:
            update_by_terminal_id = text(
                """
                UPDATE terminals
                SET terminal_name = :terminal_name, updated_at = NOW()
                WHERE uid = :uid AND terminal_id = :terminal_id
                """
            )
            result = await db.execute(
                update_by_terminal_id,
                {"uid": uid, "terminal_id": terminal_id, "terminal_name": terminal_name}
            )
            updated = result.rowcount or 0

        if updated == 0:
            return {
                "code": 1,
                "message": "terminal not found",
                "timestamp": datetime.now().isoformat()
            }

        await db.commit()
        return {
            "code": 0,
            "message": "success",
            "data": {
                "uid": uid,
                "terminal_id": terminal_id,
                "mac_address": mac_address,
                "terminal_name": terminal_name,
                "updated_rows": updated
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        await db.rollback()
        logger.error(f"更新终端名称失败: {e}")
        return {
            "code": 1,
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }


@trading_router.post("/order")
async def create_order(order: OrderRequest):
    """快速交易下单（代理到外部交易接口）"""
    try:
        payload = {
            "stock_code": order.stock_code,
            "stock_name": order.stock_name,
            "price": order.price,
            "quantity": order.quantity
        }
        if order.position_level is not None:
            payload["position_level"] = order.position_level

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(f"{ORDER_API}/api/order", json=payload)
            result = response.json() if response.content else {}
            if response.status_code >= 400:
                return {
                    "code": 1,
                    "message": result.get("detail") if isinstance(result, dict) else f"下单失败: {response.status_code}",
                    "data": result if isinstance(result, dict) else {},
                    "timestamp": datetime.now().isoformat()
                }

            return {
                "code": 0,
                "message": "success",
                "data": result if isinstance(result, dict) else {},
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"快速下单失败: {e}")
        return {
            "code": 1,
            "message": str(e),
            "data": {},
            "timestamp": datetime.now().isoformat()
        }


@trading_router.get("/pending-orders")
async def get_pending_orders(
    uid: str = Query(..., description="用户ID，例如 u_1001"),
    db: AsyncSession = Depends(get_db)
):
    """获取挂单列表"""
    try:
        query = text(
            """
            SELECT id, uid, stock_code, stock_name, scheduled_at, status, created_at, updated_at
            FROM pending_orders
            WHERE uid = :uid AND status = 'pending'
            ORDER BY scheduled_at ASC, id DESC
            """
        )
        result = await db.execute(query, {"uid": uid})
        rows = result.fetchall()
        return {
            "code": 0,
            "message": "success",
            "data": [
                {
                    "id": row[0],
                    "uid": row[1],
                    "stock_code": row[2],
                    "stock_name": row[3],
                    "scheduled_at": row[4].isoformat() if row[4] else None,
                    "status": row[5] or "pending",
                    "created_at": row[6].isoformat() if row[6] else None,
                    "updated_at": row[7].isoformat() if row[7] else None,
                }
                for row in rows
            ],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error("获取挂单列表失败: %s", e)
        return {
            "code": 1,
            "message": str(e),
            "data": [],
            "timestamp": datetime.now().isoformat()
        }


@trading_router.post("/pending-orders")
async def create_pending_order(
    payload: PendingOrderCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """新增挂单"""
    try:
        uid = payload.uid.strip()
        stock_code = payload.stock_code.strip().upper()
        stock_name = payload.stock_name.strip()
        if not uid or not stock_code or not stock_name:
            return {
                "code": 1,
                "message": "uid, stock_code, stock_name are required",
                "timestamp": datetime.now().isoformat()
            }

        scheduled_at = parse_iso_datetime(payload.scheduled_at)

        query = text(
            """
            INSERT INTO pending_orders (uid, stock_code, stock_name, scheduled_at, status, created_at, updated_at)
            VALUES (:uid, :stock_code, :stock_name, :scheduled_at, 'pending', NOW(), NOW())
            RETURNING id, uid, stock_code, stock_name, scheduled_at, status, created_at, updated_at
            """
        )
        result = await db.execute(
            query,
            {
                "uid": uid,
                "stock_code": stock_code,
                "stock_name": stock_name,
                "scheduled_at": scheduled_at,
            }
        )
        row = result.fetchone()
        return {
            "code": 0,
            "message": "success",
            "data": {
                "id": row[0],
                "uid": row[1],
                "stock_code": row[2],
                "stock_name": row[3],
                "scheduled_at": row[4].isoformat() if row[4] else None,
                "status": row[5] or "pending",
                "created_at": row[6].isoformat() if row[6] else None,
                "updated_at": row[7].isoformat() if row[7] else None,
            },
            "timestamp": datetime.now().isoformat()
        }
    except ValueError as e:
        return {
            "code": 1,
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error("新增挂单失败: %s", e)
        return {
            "code": 1,
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }


@trading_router.patch("/pending-orders/{pending_order_id}")
async def update_pending_order(
    pending_order_id: int,
    payload: PendingOrderUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """更新挂单时间"""
    try:
        scheduled_at = parse_iso_datetime(payload.scheduled_at)
        query = text(
            """
            UPDATE pending_orders
            SET scheduled_at = :scheduled_at, updated_at = NOW()
            WHERE id = :id AND status = 'pending'
            RETURNING id
            """
        )
        result = await db.execute(query, {"id": pending_order_id, "scheduled_at": scheduled_at})
        row = result.fetchone()
        if not row:
            return {
                "code": 1,
                "message": "pending order not found",
                "timestamp": datetime.now().isoformat()
            }
        return {
            "code": 0,
            "message": "success",
            "timestamp": datetime.now().isoformat()
        }
    except ValueError as e:
        return {
            "code": 1,
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error("更新挂单失败: %s", e)
        return {
            "code": 1,
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }


@trading_router.patch("/pending-orders/{pending_order_id}/status")
async def update_pending_order_status(
    pending_order_id: int,
    payload: PendingOrderStatusUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """更新挂单状态（供终端回调使用）"""
    try:
        query = text(
            """
            UPDATE pending_orders
            SET status = :status, updated_at = NOW()
            WHERE id = :id
            RETURNING id, status, updated_at
            """
        )
        result = await db.execute(
            query,
            {
                "id": pending_order_id,
                "status": payload.status
            }
        )
        row = result.fetchone()
        if not row:
            return {
                "code": 1,
                "message": "pending order not found",
                "timestamp": datetime.now().isoformat()
            }

        return {
            "code": 0,
            "message": "success",
            "data": {
                "id": row[0],
                "status": row[1],
                "updated_at": row[2].isoformat() if row[2] else None,
                "terminal_id": payload.terminal_id,
                "remark": payload.remark
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error("更新挂单状态失败: %s", e)
        return {
            "code": 1,
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }


@trading_router.delete("/pending-orders/{pending_order_id}")
async def delete_pending_order(
    pending_order_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除挂单"""
    try:
        query = text("DELETE FROM pending_orders WHERE id = :id")
        result = await db.execute(query, {"id": pending_order_id})
        if result.rowcount == 0:
            return {
                "code": 1,
                "message": "pending order not found",
                "timestamp": datetime.now().isoformat()
            }
        return {
            "code": 0,
            "message": "success",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error("删除挂单失败: %s", e)
        return {
            "code": 1,
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }


@trading_router.get("/pending-order-config")
async def get_pending_order_config(
    uid: str = Query(..., description="用户ID，例如 u_1001"),
    db: AsyncSession = Depends(get_db)
):
    """获取挂单配置"""
    try:
        query = text(
            """
            SELECT uid, enabled, default_delay_minutes, auto_submit, updated_at
            FROM pending_order_configs
            WHERE uid = :uid
            LIMIT 1
            """
        )
        result = await db.execute(query, {"uid": uid})
        row = result.fetchone()
        if not row:
            return {
                "code": 0,
                "message": "success",
                "data": {
                    "uid": uid,
                    "enabled": True,
                    "default_delay_minutes": 10,
                    "auto_submit": False,
                    "updated_at": None
                },
                "timestamp": datetime.now().isoformat()
            }
        return {
            "code": 0,
            "message": "success",
            "data": {
                "uid": row[0],
                "enabled": bool(row[1]),
                "default_delay_minutes": int(row[2] or 10),
                "auto_submit": bool(row[3]),
                "updated_at": row[4].isoformat() if row[4] else None
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error("获取挂单配置失败: %s", e)
        return {
            "code": 1,
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }


@trading_router.put("/pending-order-config")
async def update_pending_order_config(
    payload: PendingOrderConfigUpsertRequest,
    db: AsyncSession = Depends(get_db)
):
    """保存挂单配置"""
    try:
        uid = payload.uid.strip()
        if not uid:
            return {
                "code": 1,
                "message": "uid is required",
                "timestamp": datetime.now().isoformat()
            }
        delay = max(1, min(1440, int(payload.default_delay_minutes)))

        query = text(
            """
            INSERT INTO pending_order_configs (uid, enabled, default_delay_minutes, auto_submit, created_at, updated_at)
            VALUES (:uid, :enabled, :default_delay_minutes, :auto_submit, NOW(), NOW())
            ON CONFLICT (uid)
            DO UPDATE SET
              enabled = EXCLUDED.enabled,
              default_delay_minutes = EXCLUDED.default_delay_minutes,
              auto_submit = EXCLUDED.auto_submit,
              updated_at = NOW()
            """
        )
        await db.execute(
            query,
            {
                "uid": uid,
                "enabled": payload.enabled,
                "default_delay_minutes": delay,
                "auto_submit": payload.auto_submit,
            }
        )
        return {
            "code": 0,
            "message": "success",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error("保存挂单配置失败: %s", e)
        return {
            "code": 1,
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }


@trading_router.get("/trade-records/by-machine")
async def get_trade_records_by_machine(
    machine_code: str = Query(..., description="终端MAC地址"),
    start_time: Optional[str] = Query(default=None, description="开始时间 ISO8601"),
    end_time: Optional[str] = Query(default=None, description="结束时间 ISO8601"),
):
    """按终端机器编码（MAC）获取交易记录（代理外部交易记录服务）"""
    try:
        params = {"machine_code": machine_code}
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time

        async with httpx.AsyncClient(timeout=12.0) as client:
            response = await client.get(f"{TRADE_RECORD_API}/api/trade-records/by-machine", params=params)
            if response.status_code >= 400:
                logger.error("按机器查询交易记录失败: status=%s machine_code=%s", response.status_code, machine_code)
                return {
                    "code": 1,
                    "message": f"获取交易记录失败: {response.status_code}",
                    "data": [],
                    "timestamp": datetime.now().isoformat()
                }
            records = response.json()
            if not isinstance(records, list):
                records = []
            return {
                "code": 0,
                "message": "success",
                "data": records,
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"按机器查询交易记录异常 machine_code={machine_code}: {e}")
        return {
            "code": 1,
            "message": str(e),
            "data": [],
            "timestamp": datetime.now().isoformat()
        }


# ==================== 交易记录接口 ====================

@trading_router.get("/trades")
async def get_trades(db: AsyncSession = Depends(get_db)):
    """获取交易记录"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{TRADER_API}/trader/trades")

            if response.status_code != 200:
                logger.error(f"获取交易记录失败: {response.status_code}")
                return {
                    "code": 1,
                    "message": "获取交易记录失败",
                    "data": [],
                    "timestamp": datetime.now().isoformat()
                }

            data = response.json()
            # 转换为前端需要的格式
            trades = data.get("data", [])
            result = []
            for i, trade in enumerate(trades):
                result.append({
                    "id": trade.get("id") or i + 1,
                    "ts_code": trade.get("code", ""),
                    "name": trade.get("name", ""),
                    "direction": trade.get("direction", "buy"),
                    "price": float(trade.get("price", 0)),
                    "quantity": int(trade.get("amount", 0) * 100) if trade.get("amount") else 0,
                    "amount": float(trade.get("amount", 0)),
                    "time": trade.get("time", ""),
                    "status": "success"
                })

            return {
                "code": 0,
                "message": "success",
                "data": result,
                "total": len(result),
                "timestamp": datetime.now().isoformat()
            }

    except Exception as e:
        logger.error(f"获取交易记录失败: {e}")
        return {
            "code": 1,
            "message": str(e),
            "data": [],
            "timestamp": datetime.now().isoformat()
        }


@trading_router.get("/today_trades")
async def get_today_trades(db: AsyncSession = Depends(get_db)):
    """获取当日成交"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{TRADER_API}/trader/today_trades")

            if response.status_code != 200:
                logger.error(f"获取当日成交失败: {response.status_code}")
                return {
                    "code": 1,
                    "message": "获取当日成交失败",
                    "data": [],
                    "timestamp": datetime.now().isoformat()
                }

            data = response.json()
            trades = data.get("data", [])
            result = []
            for i, trade in enumerate(trades):
                result.append({
                    "id": trade.get("id") or i + 1,
                    "ts_code": trade.get("code", ""),
                    "name": trade.get("name", ""),
                    "direction": trade.get("direction", "buy"),
                    "price": float(trade.get("price", 0)),
                    "quantity": int(trade.get("amount", 0) * 100) if trade.get("amount") else 0,
                    "amount": float(trade.get("amount", 0)),
                    "time": trade.get("time", ""),
                    "status": "success"
                })

            return {
                "code": 0,
                "message": "success",
                "data": result,
                "total": len(result),
                "timestamp": datetime.now().isoformat()
            }

    except Exception as e:
        logger.error(f"获取当日成交失败: {e}")
        return {
            "code": 1,
            "message": str(e),
            "data": [],
            "timestamp": datetime.now().isoformat()
        }


# ==================== 系统状态接口 ====================

@trading_router.get("/system_status")
async def get_system_status(db: AsyncSession = Depends(get_db)):
    """获取系统连接状态"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{TRADER_API}/trader/status")

            if response.status_code != 200:
                return {
                    "code": 1,
                    "message": "获取系统状态失败",
                    "data": False,
                    "timestamp": datetime.now().isoformat()
                }

            data = response.json()
            return {
                "code": 0,
                "message": "success",
                "data": data.get("data", False),
                "timestamp": datetime.now().isoformat()
            }

    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        return {
            "code": 1,
            "message": str(e),
            "data": False,
            "timestamp": datetime.now().isoformat()
        }


# ==================== 策略配置接口 ====================

@trading_router.get("/strategy_info")
async def get_strategy_info():
    """获取策略配置"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{EXTERNAL_API}/strategy_info")
            if response.status_code == 200:
                data = response.json()
                return {
                    "switchSta": data.get("switchSta", False),
                    "buy_5m": data.get("buy_5m", 0),
                    "sell_5m": data.get("sell_5m", 0)
                }
            return {"switchSta": False, "buy_5m": 0, "sell_5m": 0}
    except Exception as e:
        logger.error(f"获取策略配置失败: {e}")
        return {"switchSta": False, "buy_5m": 0, "sell_5m": 0}


class StrategyActionRequest(BaseModel):
    """策略操作请求"""
    action: str
    sta: Optional[bool] = None
    type: Optional[str] = None
    value: Optional[float] = None


@trading_router.post("/strategy_action")
async def strategy_action(request: StrategyActionRequest):
    """策略操作"""
    try:
        payload = {"action": request.action}
        if request.sta is not None:
            payload["sta"] = request.sta
        if request.type:
            payload["type"] = request.type
        if request.value is not None:
            payload["value"] = request.value

        async with httpx.AsyncClient() as client:
            response = await client.post(f"{EXTERNAL_API}/strategy_action", json=payload)
            if response.status_code == 200:
                return {"code": 0, "message": "success", "data": response.json()}
            return {"code": 1, "message": "操作失败", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"策略操作失败: {e}")
        return {"code": 1, "message": str(e), "timestamp": datetime.now().isoformat()}
