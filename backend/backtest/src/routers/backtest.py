"""
回测管理 API 路由
"""

import asyncio
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from common.database import get_db
from backtest.src.models import Backtest, Strategy, BacktestStatus
from backtest.src.schemas import (
    ApiResponse, BacktestListResponse, BacktestCreate, BacktestDetailResponse, BacktestResult,
    BacktestCancelRequest, BacktestProgressResponse, BacktestPerformanceResponse,
    BacktestTradesResponse, BacktestLogsResponse, BacktestEquityResponse,
    TradeListResponse, LogListResponse, EquityCurveResponse, PerformanceResponse
)

router = APIRouter(prefix="/backtests", tags=["回测管理"])


async def _run_backtest_task(backtest_id: int, strategy_code: str, params: dict, db: AsyncSession):
    from backtest.src.engine import executor

    try:
        await executor.execute(
            backtest_id=backtest_id,
            strategy_code=strategy_code,
            params=params,
            db_session=db
        )
    except Exception:
        # 状态与错误信息已由执行器写回数据库，这里只避免未捕获后台任务异常污染日志
        pass


@router.get("", response_model=BacktestListResponse)
async def list_backtests(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=10, ge=1, le=100, description="每页数量"),
    strategy_id: Optional[int] = Query(default=None, description="策略ID筛选"),
    status: Optional[BacktestStatus] = Query(default=None, description="状态筛选"),
    db: AsyncSession = Depends(get_db)
):
    """获取回测记录列表"""
    query = select(Backtest).join(Strategy)
    count_query = select(func.count(Backtest.id)).join(Strategy)
    
    if strategy_id:
        query = query.where(Backtest.strategy_id == strategy_id)
        count_query = count_query.where(Backtest.strategy_id == strategy_id)
    
    if status:
        query = query.where(Backtest.status == status)
        count_query = count_query.where(Backtest.status == status)
    
    query = query.order_by(Backtest.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    backtests = result.scalars().all()
    
    count_result = await db.execute(count_query)
    total = count_result.scalar()
    
    items = []
    for bt in backtests:
        strategy_result = await db.execute(select(Strategy).where(Strategy.id == bt.strategy_id))
        strategy = strategy_result.scalar_one_or_none()
        
        items.append({
            "id": bt.id,
            "strategy_id": bt.strategy_id,
            "strategy_name": strategy.name if strategy else None,
            "status": bt.status.value if bt.status else None,
            "start_date": bt.start_date,
            "end_date": bt.end_date,
            "total_return": bt.total_return,
            "sharpe_ratio": bt.sharpe_ratio,
            "progress": bt.progress,
            "created_at": bt.created_at.isoformat() if bt.created_at else None
        })
    
    return BacktestListResponse(
        code=0,
        message="success",
        data={
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": items
        }
    )


@router.post("", response_model=ApiResponse)
async def create_backtest(
    data: BacktestCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建并启动回测任务"""
    strategy_result = await db.execute(
        select(Strategy).where(Strategy.id == data.strategy_id)
    )
    strategy = strategy_result.scalar_one_or_none()
    
    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在")
    
    backtest = Backtest(
        strategy_id=data.strategy_id,
        status=BacktestStatus.PENDING,
        start_date=data.params.start_date,
        end_date=data.params.end_date,
        frequency=data.params.frequency,
        initial_capital=data.params.initial_capital,
        metrics={"runtime_params": data.params.model_dump()},
        user_id=1
    )
    
    db.add(backtest)
    await db.flush()
    await db.commit()
    await db.refresh(backtest)
    
    return ApiResponse(
        code=0,
        message="回测任务已创建",
        data={
            "backtest_id": backtest.id,
            "strategy_id": backtest.strategy_id,
            "status": backtest.status.value,
            "progress": backtest.progress,
            "created_at": backtest.created_at.isoformat() if backtest.created_at else None
        }
    )


@router.get("/{backtest_id}", response_model=BacktestDetailResponse)
async def get_backtest(
    backtest_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取回测详情"""
    result = await db.execute(select(Backtest).where(Backtest.id == backtest_id))
    backtest = result.scalar_one_or_none()
    
    if not backtest:
        raise HTTPException(status_code=404, detail="回测不存在")
    
    strategy_result = await db.execute(select(Strategy).where(Strategy.id == backtest.strategy_id))
    strategy = strategy_result.scalar_one_or_none()
    
    runtime_params = {}
    if isinstance(backtest.metrics, dict):
        runtime_params = backtest.metrics.get("runtime_params", {}) or {}

    response_params = {
        "start_date": backtest.start_date,
        "end_date": backtest.end_date,
        "frequency": backtest.frequency,
        "initial_capital": backtest.initial_capital,
        "commission": runtime_params.get("commission", 0.0003),
        "use_min_commission": runtime_params.get("use_min_commission", True),
        "min_commission": runtime_params.get("min_commission", 5.0),
        "slippage": runtime_params.get("slippage", 0.0001),
        "fill_ratio": runtime_params.get("fill_ratio", 1.0),
        "adjust_mode": runtime_params.get("adjust_mode", "qfq"),
        "benchmark_code": runtime_params.get("benchmark_code", "000300.SH"),
        "symbols": runtime_params.get("symbols", []),
        "match_mode": runtime_params.get("match_mode", "open"),
    }

    return BacktestDetailResponse(
        code=0,
        message="success",
        data={
            "backtest_id": backtest.id,
            "strategy_id": backtest.strategy_id,
            "strategy_name": strategy.name if strategy else None,
            "status": backtest.status.value if backtest.status else None,
            "params": response_params,
            "results": {
                "final_equity": backtest.final_equity,
                "total_return": backtest.total_return,
                "benchmark_return": backtest.benchmark_return,
                "annual_return": backtest.annual_return,
                "max_drawdown": backtest.max_drawdown,
                "sharpe_ratio": backtest.sharpe_ratio,
                "win_rate": backtest.win_rate,
                "profit_loss_ratio": backtest.profit_loss_ratio
            },
            "progress": backtest.progress,
            "error_message": backtest.error_message,
            "execution_time": backtest.execution_time,
            "created_at": backtest.created_at.isoformat() if backtest.created_at else None,
            "completed_at": backtest.completed_at.isoformat() if backtest.completed_at else None
        }
    )


@router.get("/{backtest_id}/progress", response_model=BacktestProgressResponse)
async def get_backtest_progress(
    backtest_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取回测进度"""
    result = await db.execute(select(Backtest).where(Backtest.id == backtest_id))
    backtest = result.scalar_one_or_none()
    
    if not backtest:
        raise HTTPException(status_code=404, detail="回测不存在")
    
    return BacktestProgressResponse(
        code=0,
        message="success",
        data={
            "backtest_id": backtest.id,
            "status": backtest.status.value if backtest.status else None,
            "progress": backtest.progress,
            "current_date": None,
            "message": None
        }
    )


@router.post("/{backtest_id}/run", response_model=ApiResponse)
async def run_backtest(
    backtest_id: int,
    db: AsyncSession = Depends(get_db)
):
    """运行回测（异步）"""
    result = await db.execute(select(Backtest).where(Backtest.id == backtest_id))
    backtest = result.scalar_one_or_none()
    
    if not backtest:
        raise HTTPException(status_code=404, detail="回测不存在")
    
    if backtest.status not in [BacktestStatus.PENDING, BacktestStatus.RUNNING]:
        raise HTTPException(status_code=400, detail=f"回测状态不允许运行: {backtest.status.value}")
    
    result = await db.execute(select(Strategy).where(Strategy.id == backtest.strategy_id))
    strategy = result.scalar_one_or_none()
    
    if not strategy:
        raise HTTPException(status_code=404, detail="关联策略不存在")
    
    runtime_params = {}
    if isinstance(backtest.metrics, dict):
        runtime_params = backtest.metrics.get("runtime_params", {}) or {}

    params = {
        "start_date": backtest.start_date,
        "end_date": backtest.end_date,
        "initial_capital": backtest.initial_capital,
        "frequency": backtest.frequency,
        "commission": runtime_params.get("commission", strategy.config.get("commission", 0.0003) if isinstance(strategy.config, dict) else 0.0003),
        "use_min_commission": runtime_params.get("use_min_commission", strategy.config.get("use_min_commission", True) if isinstance(strategy.config, dict) else True),
        "min_commission": runtime_params.get("min_commission", strategy.config.get("min_commission", 5.0) if isinstance(strategy.config, dict) else 5.0),
        "slippage": runtime_params.get("slippage", strategy.config.get("slippage", 0.0001) if isinstance(strategy.config, dict) else 0.0001),
        "fill_ratio": runtime_params.get("fill_ratio", strategy.config.get("fill_ratio", 1.0) if isinstance(strategy.config, dict) else 1.0),
        "adjust_mode": runtime_params.get("adjust_mode", strategy.config.get("adjust_mode", "qfq") if isinstance(strategy.config, dict) else "qfq"),
        "benchmark_code": runtime_params.get("benchmark_code", strategy.config.get("benchmark_code", "000300.SH") if isinstance(strategy.config, dict) else "000300.SH"),
        "symbols": runtime_params.get("symbols", strategy.config.get("symbols", []) if isinstance(strategy.config, dict) else []),
        "match_mode": runtime_params.get("match_mode", strategy.config.get("match_mode", "open") if isinstance(strategy.config, dict) else "open"),
    }
    
    backtest.status = BacktestStatus.RUNNING
    backtest.started_at = datetime.now()
    await db.commit()
    
    asyncio.create_task(_run_backtest_task(backtest_id, strategy.code, params, db))
    
    return ApiResponse(
        code=0,
        message="回测已启动",
        data={
            "backtest_id": backtest_id,
            "status": "running"
        }
    )


@router.post("/{backtest_id}/cancel", response_model=ApiResponse)
async def cancel_backtest(
    backtest_id: int,
    db: AsyncSession = Depends(get_db)
):
    """取消回测"""
    result = await db.execute(select(Backtest).where(Backtest.id == backtest_id))
    backtest = result.scalar_one_or_none()
    
    if not backtest:
        raise HTTPException(status_code=404, detail="回测不存在")
    
    if backtest.status == BacktestStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="回测已完成，无法取消")
    
    backtest.status = BacktestStatus.CANCELLED
    await db.commit()
    
    return ApiResponse(
        code=0,
        message="回测任务已取消",
        data={
            "backtest_id": backtest.id,
            "status": backtest.status.value
        }
    )


@router.get("/{backtest_id}/trades", response_model=TradeListResponse)
async def get_backtest_trades(
    backtest_id: int,
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=50, ge=1, le=200, description="每页数量"),
    db: AsyncSession = Depends(get_db)
):
    """获取回测交易明细"""
    from backtest.src.models import BacktestTrade
    
    result = await db.execute(select(Backtest).where(Backtest.id == backtest_id))
    backtest = result.scalar_one_or_none()
    
    if not backtest:
        raise HTTPException(status_code=404, detail="回测不存在")
    
    query = select(BacktestTrade).where(BacktestTrade.backtest_id == backtest_id)
    count_query = select(func.count(BacktestTrade.id)).where(BacktestTrade.backtest_id == backtest_id)
    
    query = query.order_by(BacktestTrade.trade_time.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    trade_result = await db.execute(query)
    trades = trade_result.scalars().all()
    
    count_result = await db.execute(count_query)
    total = count_result.scalar()
    
    items = [
        {
            "id": t.id,
            "time": t.trade_time,
            "code": t.symbol,
            "name": t.name,
            "type": t.direction.value.upper(),
            "price": t.price,
            "quantity": t.quantity,
            "amount": t.amount,
            "profit": t.profit,
            "commission": t.commission
        }
        for t in trades
    ]
    
    return TradeListResponse(
        code=0,
        message="success",
        data={
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": items
        }
    )


@router.get("/{backtest_id}/logs", response_model=LogListResponse)
async def get_backtest_logs(
    backtest_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取回测系统日志"""
    from backtest.src.models import BacktestLog, LogLevel
    
    result = await db.execute(select(Backtest).where(Backtest.id == backtest_id))
    backtest = result.scalar_one_or_none()
    
    if not backtest:
        raise HTTPException(status_code=404, detail="回测不存在")
    
    query = select(BacktestLog).where(BacktestLog.backtest_id == backtest_id)
    query = query.order_by(BacktestLog.log_time)
    
    log_result = await db.execute(query)
    logs = log_result.scalars().all()
    
    error_count = sum(1 for log in logs if log.level == LogLevel.ERROR)
    warning_count = sum(1 for log in logs if log.level == LogLevel.WARNING)
    
    items = [
        {
            "time": log.log_time,
            "level": log.level.value,
            "message": log.message
        }
        for log in logs
    ]
    
    return LogListResponse(
        code=0,
        message="success",
        data={
            "backtest_id": backtest_id,
            "error_count": error_count,
            "warning_count": warning_count,
            "logs": items
        }
    )


@router.get("/{backtest_id}/equity-curve", response_model=EquityCurveResponse)
async def get_equity_curve(
    backtest_id: int,
    frequency: str = Query(default="1d", description="数据频率"),
    db: AsyncSession = Depends(get_db)
):
    """获取净值曲线数据"""
    from backtest.src.models import EquityCurve
    
    result = await db.execute(select(Backtest).where(Backtest.id == backtest_id))
    backtest = result.scalar_one_or_none()
    
    if not backtest:
        raise HTTPException(status_code=404, detail="回测不存在")
    
    query = select(EquityCurve).where(EquityCurve.backtest_id == backtest_id)
    query = query.order_by(EquityCurve.date)
    
    curve_result = await db.execute(query)
    curves = curve_result.scalars().all()
    
    data_points = [
        {
            "date": c.date,
            "equity": c.equity,
            "benchmark": c.benchmark,
            "returns": c.returns
        }
        for c in curves
    ]
    
    return EquityCurveResponse(
        code=0,
        message="success",
        data={
            "backtest_id": backtest_id,
            "benchmark": "CSI300",
            "frequency": frequency,
            "data_points": data_points
        }
    )


@router.get("/{backtest_id}/performance", response_model=PerformanceResponse)
async def get_performance(
    backtest_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取回测性能指标"""
    result = await db.execute(select(Backtest).where(Backtest.id == backtest_id))
    backtest = result.scalar_one_or_none()
    
    if not backtest:
        raise HTTPException(status_code=404, detail="回测不存在")
    
    return PerformanceResponse(
        code=0,
        message="success",
        data={
            "backtest_id": backtest_id,
            "summary": {
                "total_return": backtest.total_return,
                "annual_return": backtest.annual_return,
                "max_drawdown": backtest.max_drawdown,
                "sharpe_ratio": backtest.sharpe_ratio,
                "win_rate": backtest.win_rate,
                "profit_loss_ratio": backtest.profit_loss_ratio
            },
            "metrics": backtest.metrics if backtest.metrics else {}
        }
    )
