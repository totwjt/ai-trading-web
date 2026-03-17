# Backend Services

后端服务采用微服务架构，使用 Python 开发。

## 服务架构

```
backend/
├── gateway/           # API 网关服务
├── data_sync/         # 股票数据同步服务
├── strategy/          # 策略管理服务
├── backtest/          # 回测服务
├── trading/           # 交易服务 & 模拟盘
└── ai/                # AI 分析服务
```

## 技术栈

- Python 3.9+
- FastAPI (API 框架)
- SQLAlchemy (ORM)
- Redis (缓存)
- PostgreSQL (数据库)

## 各服务说明

### gateway (API 网关)
- 统一 API 入口
- 认证授权
- 请求路由
- 限流熔断

### data_sync (数据同步)
- 股票行情数据同步
- 实时数据推送
- 历史数据归档

### strategy (策略管理)
- 策略创建与编辑
- 策略回测配置
- 策略参数管理

### backtest (回测服务)
- 策略回测引擎
- 收益分析
- 风险指标计算

### trading (交易服务)
- 模拟交易引擎
- 订单管理
- 持仓管理

### ai (AI 分析)
- 智能选股
- 市场分析
- 预测模型

## 开发环境

### 安装依赖
```bash
cd gateway
pip install -r requirements.txt
```

### 运行服务
```bash
uvicorn main:app --reload --port 8000
```

### 测试
```bash
pytest
```
