"""
Pydantic 请求/响应模型

定义 API 的输入输出数据结构
"""

from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field

from backtest.src.models import StrategyStatus, BacktestStatus, TradeDirection, LogLevel


class ApiResponse(BaseModel):
    """通用 API 响应格式"""
    code: int = 0
    message: str = "success"
    data: Optional[Any] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class PaginationMeta(BaseModel):
    """分页元信息"""
    total: int
    page: int
    page_size: int


class PaginationResponse(BaseModel):
    """分页响应基类"""
    meta: PaginationMeta


# ============ Strategy Schemas ============

class StrategyConfig(BaseModel):
    """策略配置"""
    initial_capital: float = Field(default=1000000.0, description="初始资金")
    commission: float = Field(default=0.0003, description="手续费率")
    slippage: float = Field(default=0.0001, description="滑点")


class StrategyCreate(BaseModel):
    """创建策略请求"""
    name: str = Field(..., max_length=100, description="策略名称")
    strategy_type: Optional[str] = Field(None, description="策略类型")
    code: str = Field(..., description="策略代码")
    config: Optional[StrategyConfig] = Field(default_factory=StrategyConfig, description="策略配置")
    description: Optional[str] = Field(None, description="策略描述")


class StrategyUpdate(BaseModel):
    """更新策略请求"""
    name: Optional[str] = Field(None, max_length=100, description="策略名称")
    strategy_type: Optional[str] = Field(None, description="策略类型")
    code: Optional[str] = Field(None, description="策略代码")
    config: Optional[StrategyConfig] = Field(None, description="策略配置")
    description: Optional[str] = Field(None, description="策略描述")


class StrategyAction(BaseModel):
    """策略启停操作"""
    action: str = Field(..., description="操作类型: start/stop/pause")


class StrategyItem(BaseModel):
    """策略列表项"""
    id: int
    name: str
    strategy_type: Optional[str]
    status: StrategyStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StrategyListResponse(ApiResponse):
    """策略列表响应"""
    data: Dict[str, Any] = {
        "total": 0,
        "page": 1,
        "page_size": 10,
        "items": []
    }


class StrategyDetailResponse(ApiResponse):
    """策略详情响应"""
    data: Optional[Dict[str, Any]] = None


# ============ Backtest Schemas ============

class BacktestParams(BaseModel):
    """回测参数"""
    start_date: str = Field(..., description="开始日期 YYYY-MM-DD")
    end_date: str = Field(..., description="结束日期 YYYY-MM-DD")
    frequency: str = Field(default="1d", description="数据频率: 1d/1w/1m/5m/15m")
    initial_capital: float = Field(default=1000000.0, description="初始资金")


class BacktestCreate(BaseModel):
    """创建回测请求"""
    strategy_id: int = Field(..., description="策略ID")
    params: BacktestParams


class BacktestPreviewCreate(BaseModel):
    """编译运行预览请求"""
    strategy_id: Optional[int] = Field(None, description="策略ID (新建时为空)")
    code: str = Field(..., description="策略代码")
    params: BacktestParams


class BacktestProgress(BaseModel):
    """回测进度"""
    backtest_id: int
    status: BacktestStatus
    progress: int
    current_date: Optional[str] = None
    message: Optional[str] = None


class BacktestItem(BaseModel):
    """回测记录项"""
    id: int
    strategy_id: int
    strategy_name: Optional[str] = None
    status: BacktestStatus
    start_date: str
    end_date: str
    total_return: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    progress: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class BacktestResult(BaseModel):
    """回测结果"""
    final_equity: Optional[float] = None
    total_return: Optional[float] = None
    benchmark_return: Optional[float] = None
    annual_return: Optional[float] = None
    max_drawdown: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    win_rate: Optional[float] = None
    profit_loss_ratio: Optional[float] = None


class BacktestDetailResponse(ApiResponse):
    """回测详情响应"""
    data: Optional[Dict[str, Any]] = None


class BacktestListResponse(ApiResponse):
    """回测列表响应"""
    data: Dict[str, Any] = {
        "total": 0,
        "page": 1,
        "page_size": 10,
        "items": []
    }


class BacktestCancelRequest(BaseModel):
    """取消回测请求"""
    backtest_id: int


class BacktestProgressResponse(ApiResponse):
    """回测进度响应"""
    data: Optional[BacktestProgress] = None


class BacktestPerformanceResponse(ApiResponse):
    """回测性能指标响应"""
    data: Optional[Dict[str, Any]] = None


class BacktestTradesResponse(ApiResponse):
    """回测交易明细响应"""
    data: Dict[str, Any] = {
        "total": 0,
        "page": 1,
        "page_size": 50,
        "items": []
    }


class BacktestLogsResponse(ApiResponse):
    """回测日志响应"""
    data: Dict[str, Any] = {
        "error_count": 0,
        "warning_count": 0,
        "logs": []
    }


class BacktestEquityResponse(ApiResponse):
    """回测净值曲线响应"""
    data: Dict[str, Any] = {
        "backtest_id": 0,
        "benchmark": "CSI300",
        "frequency": "1d",
        "data_points": []
    }


# ============ Trade Schemas ============

class TradeItem(BaseModel):
    """交易明细项"""
    id: int
    trade_time: str
    symbol: str
    name: Optional[str]
    direction: TradeDirection
    price: float
    quantity: int
    amount: float
    commission: float
    profit: Optional[float]

    class Config:
        from_attributes = True


class TradeListResponse(ApiResponse):
    """交易明细响应"""
    data: Dict[str, Any] = {
        "total": 0,
        "page": 1,
        "page_size": 50,
        "items": []
    }


# ============ Log Schemas ============

class LogItem(BaseModel):
    """日志项"""
    id: int
    log_time: str
    level: LogLevel
    message: str

    class Config:
        from_attributes = True


class LogListResponse(ApiResponse):
    """日志列表响应"""
    data: Dict[str, Any] = {
        "error_count": 0,
        "warning_count": 0,
        "logs": []
    }


# ============ Equity Curve Schemas ============

class EquityPoint(BaseModel):
    """净值曲线数据点"""
    date: str
    equity: float
    benchmark: float
    returns: float


class EquityCurveResponse(ApiResponse):
    """净值曲线响应"""
    data: Dict[str, Any] = {
        "backtest_id": 0,
        "benchmark": "CSI300",
        "frequency": "1d",
        "data_points": []
    }


# ============ Performance Schemas ============

class PerformanceSummary(BaseModel):
    """性能摘要"""
    total_return: Optional[float] = None
    annual_return: Optional[float] = None
    max_drawdown: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    win_rate: Optional[float] = None
    profit_loss_ratio: Optional[float] = None
    initial_value: Optional[float] = None
    final_equity: Optional[float] = None
    benchmark_return: Optional[float] = None
    total_trades: Optional[int] = None


class PerformanceMetrics(BaseModel):
    """扩展性能指标"""
    calmar_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    volatility: Optional[float] = None
    beta: Optional[float] = None
    alpha: Optional[float] = None
    information_ratio: Optional[float] = None
    max_consecutive_wins: Optional[int] = None
    max_consecutive_losses: Optional[int] = None
    avg_holding_days: Optional[float] = None
    total_trades: Optional[int] = None
    avg_profit_per_trade: Optional[float] = None


class PerformanceResponse(ApiResponse):
    """性能指标响应"""
    data: Dict[str, Any] = {
        "backtest_id": 0,
        "summary": PerformanceSummary(),
        "metrics": PerformanceMetrics()
    }


# ============ Preview Schemas ============

class PreviewResult(BaseModel):
    """预览结果"""
    success: bool
    logs: List[LogItem] = []
    summary: Optional[PerformanceSummary] = None
    equity_curve: List[EquityPoint] = []
    error: Optional[str] = None


class PreviewResponse(ApiResponse):
    """预览响应"""
    data: Optional[PreviewResult] = None


# ============ WebSocket Schemas ============

class WSMessage(BaseModel):
    """WebSocket 消息"""
    type: str
    payload: Dict[str, Any] = {}
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    message_id: Optional[str] = None
