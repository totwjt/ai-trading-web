"""
策略编译运行 API

提供策略代码的编译检查和预览功能
"""

import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from common.database import get_db
from backtest.src.models import Backtest, Strategy, BacktestLog, LogLevel, BacktestStatus
from backtest.src.schemas import ApiResponse, BacktestPreviewCreate, PreviewResponse, PreviewResult, EquityPoint
from strategy.src.compiler import compile_strategy, validate_backtrader_strategy, quick_preview_params
from backtest.src.engine import BacktestEngine

router = APIRouter(prefix="/preview", tags=["策略预览"])


@router.post("/validate", response_model=ApiResponse)
async def validate_strategy(
    code: str
):
    result = compile_strategy(code)
    
    return ApiResponse(
        code=0 if result["valid"] else 1,
        message="策略验证通过" if result["valid"] else "策略验证失败",
        data={
            "valid": result["valid"],
            "errors": result.get("errors", []),
            "warnings": result.get("warnings", [])
        }
    )


@router.post("/run", response_model=PreviewResponse)
async def preview_backtest(
    data: BacktestPreviewCreate,
    db: AsyncSession = Depends(get_db)
):
    logs: List[Dict[str, Any]] = []
    
    try:
        preview_params = quick_preview_params({
            "start_date": data.params.start_date,
            "end_date": data.params.end_date,
            "frequency": data.params.frequency
        })
        
        logs.append({
            "id": 1,
            "log_time": datetime.now().isoformat(),
            "level": "INFO",
            "message": f"预览参数: {preview_params['start_date']} ~ {preview_params['end_date']}"
        })
        
        validation_ok, validation_errors = validate_backtrader_strategy(data.code)
        if not validation_ok:
            logs.append({
                "id": len(logs) + 1,
                "log_time": datetime.now().isoformat(),
                "level": "ERROR",
                "message": f"策略验证失败: {validation_errors[0] if validation_errors else 'Unknown error'}"
            })
            return PreviewResponse(
                code=1,
                message="策略验证失败",
                data=PreviewResult(
                    success=False,
                    logs=logs,
                    error=validation_errors[0] if validation_errors else "Unknown error"
                )
            )
        
        engine = BacktestEngine(
            strategy_code=data.code,
            start_date=preview_params["start_date"],
            end_date=preview_params["end_date"],
            initial_capital=preview_params["initial_capital"]
        )
        
        logs.append({
            "id": len(logs) + 1,
            "log_time": datetime.now().isoformat(),
            "level": "INFO",
            "message": "回测引擎初始化完成（365天单股票快速验证）"
        })
        
        results = await engine.run(is_preview=True)
        
        logs.append({
            "id": len(logs) + 1,
            "log_time": datetime.now().isoformat(),
            "level": "INFO",
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
            "id": len(logs) + 1,
            "log_time": datetime.now().isoformat(),
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
