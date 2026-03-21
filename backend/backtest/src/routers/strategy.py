"""
策略管理 API 路由
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from common.database import get_db
from backtest.src.models import Strategy, StrategyStatus
from backtest.src.schemas import (
    ApiResponse, StrategyCreate, StrategyUpdate, StrategyAction,
    StrategyItem, StrategyListResponse, StrategyDetailResponse
)

router = APIRouter(prefix="/strategies", tags=["策略管理"])


@router.get("", response_model=StrategyListResponse)
async def list_strategies(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=10, ge=1, le=100, description="每页数量"),
    status: Optional[StrategyStatus] = Query(default=None, description="筛选状态"),
    db: AsyncSession = Depends(get_db)
):
    """获取策略列表"""
    query = select(Strategy)
    count_query = select(func.count(Strategy.id))
    
    if status:
        query = query.where(Strategy.status == status)
        count_query = count_query.where(Strategy.status == status)
    
    query = query.order_by(Strategy.updated_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    strategies = result.scalars().all()
    
    count_result = await db.execute(count_query)
    total = count_result.scalar()
    
    items = [
        {
            "id": s.id,
            "name": s.name,
            "strategy_type": s.strategy_type,
            "status": s.status.value if s.status else None,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "updated_at": s.updated_at.isoformat() if s.updated_at else None
        }
        for s in strategies
    ]
    
    return StrategyListResponse(
        code=0,
        message="success",
        data={
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": items
        }
    )


@router.get("/{strategy_id}", response_model=StrategyDetailResponse)
async def get_strategy(
    strategy_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取策略详情"""
    result = await db.execute(select(Strategy).where(Strategy.id == strategy_id))
    strategy = result.scalar_one_or_none()
    
    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在")
    
    return StrategyDetailResponse(
        code=0,
        message="success",
        data={
            "id": strategy.id,
            "name": strategy.name,
            "strategy_type": strategy.strategy_type,
            "status": strategy.status.value if strategy.status else None,
            "code": strategy.code,
            "config": strategy.config,
            "description": strategy.description,
            "created_at": strategy.created_at.isoformat() if strategy.created_at else None,
            "updated_at": strategy.updated_at.isoformat() if strategy.updated_at else None
        }
    )


@router.post("", response_model=ApiResponse)
async def create_strategy(
    data: StrategyCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建策略"""
    strategy = Strategy(
        name=data.name,
        strategy_type=data.strategy_type,
        code=data.code,
        config=data.config.model_dump() if data.config else {},
        description=data.description,
        status=StrategyStatus.PAUSED,
        user_id=1
    )
    
    db.add(strategy)
    await db.flush()
    await db.commit()
    await db.refresh(strategy)
    
    return ApiResponse(
        code=0,
        message="策略创建成功",
        data={
            "id": strategy.id,
            "name": strategy.name
        }
    )


@router.put("/{strategy_id}", response_model=ApiResponse)
async def update_strategy(
    strategy_id: int,
    data: StrategyUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新策略"""
    result = await db.execute(select(Strategy).where(Strategy.id == strategy_id))
    strategy = result.scalar_one_or_none()
    
    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在")
    
    update_data = data.model_dump(exclude_unset=True)
    if "config" in update_data and update_data["config"]:
        update_data["config"] = update_data["config"].model_dump() if hasattr(update_data["config"], "model_dump") else update_data["config"]
    
    for key, value in update_data.items():
        setattr(strategy, key, value)
    
    strategy.updated_at = datetime.now()
    
    await db.commit()
    
    return ApiResponse(
        code=0,
        message="策略更新成功",
        data={
            "id": strategy.id,
            "updated_at": strategy.updated_at.isoformat()
        }
    )


@router.delete("/{strategy_id}", response_model=ApiResponse)
async def delete_strategy(
    strategy_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除策略"""
    result = await db.execute(select(Strategy).where(Strategy.id == strategy_id))
    strategy = result.scalar_one_or_none()
    
    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在")
    
    await db.delete(strategy)
    await db.commit()
    
    return ApiResponse(
        code=0,
        message="策略删除成功",
        data=None
    )


@router.post("/{strategy_id}/action", response_model=ApiResponse)
async def strategy_action(
    strategy_id: int,
    data: StrategyAction,
    db: AsyncSession = Depends(get_db)
):
    """策略启停控制"""
    result = await db.execute(select(Strategy).where(Strategy.id == strategy_id))
    strategy = result.scalar_one_or_none()
    
    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在")
    
    action_map = {
        "start": StrategyStatus.RUNNING,
        "stop": StrategyStatus.STOPPED,
        "pause": StrategyStatus.PAUSED
    }
    
    if data.action not in action_map:
        raise HTTPException(status_code=400, detail=f"不支持的操作: {data.action}")
    
    new_status = action_map[data.action]
    strategy.status = new_status
    strategy.updated_at = datetime.now()
    
    await db.commit()
    
    return ApiResponse(
        code=0,
        message=f"策略已{data.action}",
        data={
            "id": strategy.id,
            "status": strategy.status.value
        }
    )
