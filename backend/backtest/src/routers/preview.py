"""
策略编译运行 API

提供策略代码的编译检查和预览功能
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.common.database import get_db
from backend.backtest.src.models import Backtest, Strategy, BacktestLog, LogLevel, BacktestStatus
from backend.backtest.src.schemas import ApiResponse, BacktestPreviewCreate, PreviewResponse, PreviewResult
from backend.strategy.src.compiler import compile_strategy, validate_backtrader_strategy, quick_preview_params

router = APIRouter(prefix="/backtests", tags=["策略编译运行"])


@router.post("/preview", response_model=PreviewResponse)
async def preview_strategy(
    data: BacktestPreviewCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    编译运行预览
    
    快速检查策略代码语法和安全性，使用短时间区间小数据
    """
    logs = []
    errors = []
    
    logs.append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "level": "INFO",
        "message": "开始编译检查..."
    })
    
    compile_result = compile_strategy(data.code)
    
    if not compile_result.success:
        errors.extend(compile_result.errors)
        for error in compile_result.errors:
            logs.append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "level": "ERROR",
                "message": error
            })
        return PreviewResponse(
            code=1 if errors else 0,
            message="编译失败" if errors else "success",
            data=PreviewResult(
                success=False,
                logs=logs,
                error="; ".join(errors)
            )
        )
    
    for warning in compile_result.warnings:
        logs.append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "level": "WARNING",
            "message": warning
        })
    
    logs.append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "level": "INFO",
        "message": "编译检查通过"
    })
    
    is_valid, validation_errors = validate_backtrader_strategy(data.code)
    if not is_valid:
        errors.extend(validation_errors)
        for error in validation_errors:
            logs.append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "level": "ERROR",
                "message": error
            })
        return PreviewResponse(
            code=1,
            message="策略验证失败",
            data=PreviewResult(
                success=False,
                logs=logs,
                error="; ".join(errors)
            )
        )
    
    logs.append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "level": "INFO",
        "message": "策略结构验证通过"
    })
    
    preview_params = quick_preview_params(data.params.model_dump())
    logs.append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "level": "INFO",
        "message": f"使用预览参数: {preview_params['start_date']} ~ {preview_params['end_date']}"
    })
    
    logs.append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "level": "INFO",
        "message": "开始运行回测预览..."
    })
    
    try:
        from backend.backtest.src.engine import BacktestEngine
        
        engine = BacktestEngine(
            strategy_code=data.code,
            start_date=preview_params["start_date"],
            end_date=preview_params["end_date"],
            initial_capital=preview_params["initial_capital"]
        )
        
        logs.append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "level": "INFO",
            "message": "回测引擎初始化完成"
        })
        
        results = await engine.run()
        
        logs.append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "level": "SUCCESS",
            "message": f"回测完成: 收益 {results.get('total_return', 0):.2f}%"
        })
        
        return PreviewResponse(
            code=0,
            message="success",
            data=PreviewResult(
                success=True,
                logs=logs,
                summary={
                    "total_return": results.get("total_return", 0),
                    "final_equity": results.get("final_equity", 0),
                    "initial_value": results.get("initial_value", 0)
                },
                equity_curve=engine.get_equity_curve()
            )
        )
        
    except Exception as e:
        logs.append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "level": "ERROR",
            "message": f"回测执行失败: {str(e)}"
        })
        
        return PreviewResponse(
            code=1,
            message="回测执行失败",
            data=PreviewResult(
                success=False,
                logs=logs,
                error=str(e)
            )
        )


@router.post("/{backtest_id}/run", response_model=ApiResponse)
async def run_backtest(
    backtest_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    运行回测（异步）
    
    创建回测任务并异步执行
    """
    from backend.backtest.src.engine import executor
    
    result = await db.execute(
        Backtest.__table__.select().where(Backtest.id == backtest_id)
    )
    backtest = result.fetchone()
    
    if not backtest:
        raise HTTPException(status_code=404, detail="回测不存在")
    
    if backtest.status != BacktestStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"回测状态不允许运行: {backtest.status}")
    
    strategy_result = await db.execute(
        Strategy.__table__.select().where(Strategy.id == backtest.strategy_id)
    )
    strategy = strategy_result.fetchone()
    
    if not strategy:
        raise HTTPException(status_code=404, detail="关联策略不存在")
    
    params = {
        "start_date": backtest.start_date,
        "end_date": backtest.end_date,
        "initial_capital": backtest.initial_capital,
        "frequency": backtest.frequency
    }
    
    backtest.status = BacktestStatus.RUNNING
    backtest.started_at = datetime.now()
    await db.commit()
    
    asyncio.create_task(
        executor.execute(
            backtest_id=backtest_id,
            strategy_code=strategy.code,
            params=params,
            db_session=db
        )
    )
    
    return ApiResponse(
        code=0,
        message="回测已启动",
        data={
            "backtest_id": backtest_id,
            "status": "running"
        }
    )


import asyncio
