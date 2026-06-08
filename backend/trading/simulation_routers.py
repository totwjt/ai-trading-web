"""
模拟交易服务 - 转发到外部 Simulation API
"""

from fastapi import APIRouter, Query, Request
from typing import Optional
import logging
import httpx
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

simulation_router = APIRouter(prefix="/api/trading/simulations", tags=["simulations"])

SIMULATION_API = os.getenv("SIMULATION_API", "http://host.docker.internal:7000")


def authorization_headers(request: Request) -> dict:
    auth_header = request.headers.get("authorization") or ""
    if not auth_header:
        return {}
    return {"Authorization": auth_header}


# ==================== 统计信息（必须在 /{id} 之前） ====================

@simulation_router.get("/stats")
async def get_simulation_stats(request: Request):
    """获取统计信息"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{SIMULATION_API}/api/simulations/stats",
                headers=authorization_headers(request)
            )
            return response.json()
    except Exception as e:
        logger.error(f"get_simulation_stats failed: {e}")
        return {"code": 1, "message": str(e), "data": None}


# ==================== 可用策略列表（必须在 /{id} 之前） ====================

@simulation_router.get("/available-strategies")
async def get_available_strategies(request: Request):
    """获取所有可用策略的列表"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{SIMULATION_API}/api/available-strategies",
                headers=authorization_headers(request)
            )
            return response.json()
    except Exception as e:
        logger.error(f"get_available_strategies failed: {e}")
        return {"code": 1, "message": str(e), "data": None}


# ==================== 策略名称 ====================

@simulation_router.get("/strategies/{id}/name")
async def get_strategy_name(id: int, request: Request):
    """根据ID获取策略名称"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{SIMULATION_API}/api/strategies/{id}/name",
                headers=authorization_headers(request)
            )
            return response.json()
    except Exception as e:
        logger.error(f"get_strategy_name failed: {e}")
        return {"code": 1, "message": str(e), "data": None}


# ==================== 模拟列表（分页、筛选） ====================

@simulation_router.get("/")
async def get_simulations(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    status: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None)
):
    """从数据库获取模拟交易历史记录列表"""
    try:
        params = {"page": page, "page_size": page_size}
        if status:
            params["status"] = status
        if search:
            params["search"] = search

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{SIMULATION_API}/api/simulations",
                params=params,
                headers=authorization_headers(request)
            )
            return response.json()
    except Exception as e:
        logger.error(f"get_simulations failed: {e}")
        return {"code": 1, "message": str(e), "data": None}


# ==================== 创建模拟 ====================

@simulation_router.post("/")
async def create_simulation(request: Request):
    """创建模拟"""
    try:
        body = await request.json()
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{SIMULATION_API}/api/simulations",
                json=body,
                headers=authorization_headers(request)
            )
            return response.json()
    except Exception as e:
        logger.error(f"create_simulation failed: {e}")
        return {"code": 1, "message": str(e), "data": None}


# ==================== 从选股创建模拟 ====================

@simulation_router.post("/from-selection")
async def create_simulation_from_selection(request: Request):
    """从选股API获取股票并创建模拟交易"""
    try:
        body = await request.json()
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{SIMULATION_API}/api/simulations/from-selection",
                json=body,
                headers=authorization_headers(request)
            )
            return response.json()
    except Exception as e:
        logger.error(f"create_simulation_from_selection failed: {e}")
        return {"code": 1, "message": str(e), "data": None}


# ==================== 模拟详情 ====================

@simulation_router.get("/{id}")
async def get_simulation(id: int, request: Request):
    """获取模拟详情"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{SIMULATION_API}/api/simulations/{id}",
                headers=authorization_headers(request)
            )
            return response.json()
    except Exception as e:
        logger.error(f"get_simulation failed: {e}")
        return {"code": 1, "message": str(e), "data": None}


# ==================== 删除模拟 ====================

@simulation_router.delete("/{id}")
async def delete_simulation(id: str, request: Request):
    """删除模拟"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.delete(
                f"{SIMULATION_API}/api/simulations/{id}",
                headers=authorization_headers(request)
            )
            return response.json()
    except Exception as e:
        logger.error(f"delete_simulation failed: {e}")
        return {"code": 1, "message": str(e), "data": None}


# ==================== 暂停 ====================

@simulation_router.post("/{id}/pause")
async def pause_simulation(id: int, request: Request):
    """暂停模拟"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{SIMULATION_API}/api/simulations/{id}/pause",
                headers=authorization_headers(request)
            )
            return response.json()
    except Exception as e:
        logger.error(f"pause_simulation failed: {e}")
        return {"code": 1, "message": str(e), "data": None}


# ==================== 启动 ====================

@simulation_router.post("/{id}/start")
async def start_simulation(id: int, request: Request):
    """启动A股实盘模拟交易"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{SIMULATION_API}/api/simulations/{id}/start",
                headers=authorization_headers(request)
            )
            return response.json()
    except Exception as e:
        logger.error(f"start_simulation failed: {e}")
        return {"code": 1, "message": str(e), "data": None}


# ==================== 恢复 ====================

@simulation_router.post("/{id}/resume")
async def resume_simulation(id: int, request: Request):
    """恢复模拟"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{SIMULATION_API}/api/simulations/{id}/resume",
                headers=authorization_headers(request)
            )
            return response.json()
    except Exception as e:
        logger.error(f"resume_simulation failed: {e}")
        return {"code": 1, "message": str(e), "data": None}


# ==================== 停止 ====================

@simulation_router.post("/{id}/stop")
async def stop_simulation(id: int, request: Request):
    """停止模拟"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{SIMULATION_API}/api/simulations/{id}/stop",
                headers=authorization_headers(request)
            )
            return response.json()
    except Exception as e:
        logger.error(f"stop_simulation failed: {e}")
        return {"code": 1, "message": str(e), "data": None}


# ==================== 持仓列表 ====================

@simulation_router.get("/{id}/holdings")
async def get_holdings(id: int, request: Request):
    """获取持仓列表"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{SIMULATION_API}/api/simulations/{id}/holdings",
                headers=authorization_headers(request)
            )
            return response.json()
    except Exception as e:
        logger.error(f"get_holdings failed: {e}")
        return {"code": 1, "message": str(e), "data": None}


# ==================== 交易记录 ====================

@simulation_router.get("/{id}/trades")
async def get_trades(
    id: int,
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100)
):
    """获取交易记录"""
    try:
        params = {"page": page, "page_size": page_size}
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{SIMULATION_API}/api/simulations/{id}/trades",
                params=params,
                headers=authorization_headers(request)
            )
            return response.json()
    except Exception as e:
        logger.error(f"get_trades failed: {e}")
        return {"code": 1, "message": str(e), "data": None}


# ==================== 模拟运行状态 ====================

@simulation_router.get("/{id}/status")
async def get_simulation_status(id: int, request: Request):
    """获取模拟运行状态"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{SIMULATION_API}/api/simulations/{id}/status",
                headers=authorization_headers(request)
            )
            return response.json()
    except Exception as e:
        logger.error(f"get_simulation_status failed: {e}")
        return {"code": 1, "message": str(e), "data": None}


# ==================== A股交易状态 ====================

@simulation_router.get("/{id}/market-status")
async def get_market_status(id: int, request: Request):
    """获取A股交易状态"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{SIMULATION_API}/api/simulations/{id}/market-status",
                headers=authorization_headers(request)
            )
            return response.json()
    except Exception as e:
        logger.error(f"get_market_status failed: {e}")
        return {"code": 1, "message": str(e), "data": None}


# ==================== 策略引擎状态 ====================

@simulation_router.get("/{id}/strategy/status")
async def get_strategy_status(id: int, request: Request):
    """获取策略引擎状态"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{SIMULATION_API}/api/simulations/{id}/strategy/status",
                headers=authorization_headers(request)
            )
            return response.json()
    except Exception as e:
        logger.error(f"get_strategy_status failed: {e}")
        return {"code": 1, "message": str(e), "data": None}


# ==================== 组合价值 ====================

@simulation_router.get("/{id}/portfolio/value")
async def get_portfolio_value(id: int, request: Request):
    """获取投资组合价值"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{SIMULATION_API}/api/simulations/{id}/portfolio/value",
                headers=authorization_headers(request)
            )
            return response.json()
    except Exception as e:
        logger.error(f"get_portfolio_value failed: {e}")
        return {"code": 1, "message": str(e), "data": None}


# ==================== 手动交易 ====================

@simulation_router.post("/{id}/manual-trade")
async def execute_manual_trade(id: int, request: Request):
    """执行手动交易"""
    try:
        body = await request.json()
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{SIMULATION_API}/api/simulations/{id}/manual-trade",
                json=body,
                headers=authorization_headers(request)
            )
            return response.json()
    except Exception as e:
        logger.error(f"execute_manual_trade failed: {e}")
        return {"code": 1, "message": str(e), "data": None}


# ==================== 订单列表 ====================

@simulation_router.get("/{id}/orders")
async def get_orders(
    id: int,
    request: Request,
    status: Optional[str] = Query(default=None)
):
    """获取订单列表"""
    try:
        params = {}
        if status:
            params["status"] = status
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{SIMULATION_API}/api/simulations/{id}/orders",
                params=params,
                headers=authorization_headers(request)
            )
            return response.json()
    except Exception as e:
        logger.error(f"get_orders failed: {e}")
        return {"code": 1, "message": str(e), "data": None}


# ==================== 创建订单 ====================

@simulation_router.post("/{id}/orders")
async def create_order(id: int, request: Request):
    """创建新订单"""
    try:
        body = await request.json()
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{SIMULATION_API}/api/simulations/{id}/orders",
                json=body,
                headers=authorization_headers(request)
            )
            return response.json()
    except Exception as e:
        logger.error(f"create_order failed: {e}")
        return {"code": 1, "message": str(e), "data": None}


# ==================== 取消订单 ====================

@simulation_router.post("/{id}/orders/{order_id}/cancel")
async def cancel_order(id: int, order_id: int, request: Request):
    """取消订单"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{SIMULATION_API}/api/simulations/{id}/orders/{order_id}/cancel",
                headers=authorization_headers(request)
            )
            return response.json()
    except Exception as e:
        logger.error(f"cancel_order failed: {e}")
        return {"code": 1, "message": str(e), "data": None}
