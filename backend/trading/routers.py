"""
股票交易服务 - 股票检索 API
"""

from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import logging
import httpx

from common.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, delete
from trading.models import Watchlist

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

trading_router = APIRouter(prefix="/api/trading", tags=["trading"])

EXTERNAL_API = "http://192.168.66.141:8888"


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


# ==================== 路由 ====================

@trading_router.get("/stock/search", response_model=StockSearchResponse)
async def search_stocks(
    keyword: str = Query(..., description="搜索关键词，支持股票代码或名称"),
    limit: int = Query(default=20, ge=1, le=100, description="返回结果数量"),
    db: AsyncSession = Depends(get_db)
):
    """
    股票检索 API
    支持按股票代码(ts_code)或名称(name)模糊查询
    """
    try:
        search_pattern = f"%{keyword}%"
        logger.info(f"Searching stocks: keyword={keyword}, pattern={search_pattern}, limit={limit}")
        
        query = text("""
            SELECT ts_code, name, industry, market, list_date 
            FROM stock_basic 
            WHERE ts_code LIKE :pattern OR name LIKE :pattern
            LIMIT :limit
        """)
        
        logger.info(f"Executing query with params: pattern={search_pattern}, limit={limit}")
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
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{EXTERNAL_API}/stock/realtime")
            data = response.json()
            items = data.get("data", [])
            
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
            "code": 0,
            "message": "success",
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
            if response.status_code == 200:
                return {
                    "code": 0,
                    "message": "success",
                    "data": {"ts_code": ts_code},
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