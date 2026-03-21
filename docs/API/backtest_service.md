# 回测与预览服务 API

本文档以当前仓库下列实现为准:

- `backend/backtest/src/routers/backtest.py`
- `backend/backtest/src/routers/preview.py`

## 基础信息

- 服务前缀: `/api`
- 回测路由前缀: `/backtests`
- 预览路由前缀: `/preview`

## 状态枚举

- `pending`
- `running`
- `completed`
- `failed`
- `cancelled`

## 回测参数

```json
{
  "start_date": "2025-01-01",
  "end_date": "2025-01-31",
  "frequency": "1d",
  "initial_capital": 1000000
}
```

说明:

- `frequency` 当前 schema 允许 `1d`、`1w`、`1m`、`5m`、`15m`
- 当前后端 `POST /api/backtests` 只创建任务，不会自动执行
- 实际执行要再调用 `POST /api/backtests/{id}/run`
- 预览与最终回测都已切到本地 PostgreSQL `tushare_sync` 数据源，不再使用随机样本

## 1. 获取回测列表

`GET /api/backtests`

Query 参数:

- `page`: 默认 `1`
- `page_size`: 默认 `10`，最大 `100`
- `strategy_id`: 可选
- `status`: 可选

响应 `data`:

```json
{
  "total": 3,
  "page": 1,
  "page_size": 5,
  "items": [
    {
      "id": 3,
      "strategy_id": 1,
      "strategy_name": "测试均线策略",
      "status": "completed",
      "start_date": "2025-03-21",
      "end_date": "2026-03-21",
      "total_return": -0.0035,
      "sharpe_ratio": null,
      "progress": 100,
      "created_at": "2026-03-21T18:21:54.400560"
    }
  ]
}
```

## 2. 创建回测任务

`POST /api/backtests`

请求体:

```json
{
  "strategy_id": 1,
  "params": {
    "start_date": "2025-01-01",
    "end_date": "2025-01-31",
    "frequency": "1d",
    "initial_capital": 1000000
  }
}
```

成功响应 `data`:

```json
{
  "backtest_id": 4,
  "strategy_id": 1,
  "status": "pending",
  "progress": 0,
  "created_at": "2026-03-21T18:20:00"
}
```

## 3. 获取回测详情

`GET /api/backtests/{backtest_id}`

响应 `data`:

```json
{
  "backtest_id": 3,
  "strategy_id": 1,
  "strategy_name": "测试均线策略",
  "status": "completed",
  "params": {
    "start_date": "2025-03-21",
    "end_date": "2026-03-21",
    "frequency": "1d",
    "initial_capital": 1000000
  },
  "results": {
    "final_equity": 999964.99,
    "total_return": -0.0035,
    "benchmark_return": null,
    "annual_return": null,
    "max_drawdown": null,
    "sharpe_ratio": null,
    "win_rate": null,
    "profit_loss_ratio": null
  },
  "progress": 100,
  "error_message": null,
  "execution_time": 0,
  "created_at": "2026-03-21T18:21:54.400560",
  "completed_at": "2026-03-21T18:21:55.000000"
}
```

## 4. 获取回测进度

`GET /api/backtests/{backtest_id}/progress`

响应 `data`:

```json
{
  "backtest_id": 3,
  "status": "running",
  "progress": 30,
  "current_date": null,
  "message": null
}
```

说明:

- 当前后端只返回 `status` 和 `progress` 的核心进度
- `current_date`、`message` 已预留，但当前实现固定为 `null`

## 5. 启动回测

`POST /api/backtests/{backtest_id}/run`

说明:

- 仅 `pending`、`running` 状态允许调用
- 后端会把状态先切为 `running`，再异步执行引擎

成功响应 `data`:

```json
{
  "backtest_id": 4,
  "status": "running"
}
```

## 6. 取消回测

`POST /api/backtests/{backtest_id}/cancel`

成功响应 `data`:

```json
{
  "backtest_id": 4,
  "status": "cancelled"
}
```

## 7. 获取交易明细

`GET /api/backtests/{backtest_id}/trades`

Query 参数:

- `page`: 默认 `1`
- `page_size`: 默认 `50`，最大 `200`

响应 `data`:

```json
{
  "total": 2,
  "page": 1,
  "page_size": 50,
  "items": [
    {
      "id": 10,
      "time": "2025-01-06 10:00:00",
      "code": "000001.SZ",
      "name": "平安银行",
      "type": "BUY",
      "price": 12.34,
      "quantity": 1000,
      "amount": 12340,
      "profit": null,
      "commission": 3.7
    }
  ]
}
```

## 8. 获取系统日志

`GET /api/backtests/{backtest_id}/logs`

响应 `data`:

```json
{
  "backtest_id": 3,
  "error_count": 0,
  "warning_count": 0,
  "logs": [
    {
      "time": "2026-03-21 18:21:54",
      "level": "INFO",
      "message": "Cerebro engine initialized."
    }
  ]
}
```

## 9. 获取净值曲线

`GET /api/backtests/{backtest_id}/equity-curve`

Query 参数:

- `frequency`: 默认 `1d`

响应 `data`:

```json
{
  "backtest_id": 3,
  "benchmark": "CSI300",
  "frequency": "1d",
  "data_points": [
    {
      "date": "2025-01-02",
      "equity": 1000000,
      "benchmark": 1000000,
      "returns": 0
    }
  ]
}
```

说明:

- 当前后端不会按 `frequency` 重新聚合，只是把查询参数原样带回响应

## 10. 获取性能指标

`GET /api/backtests/{backtest_id}/performance`

响应 `data`:

```json
{
  "backtest_id": 3,
  "summary": {
    "total_return": -0.0035,
    "annual_return": null,
    "max_drawdown": null,
    "sharpe_ratio": null,
    "win_rate": null,
    "profit_loss_ratio": null
  },
  "metrics": {}
}
```

说明:

- `summary` 直接来自 `backtests` 表主字段
- `metrics` 来自 `backtests.metrics` JSON 字段，未生成时为空对象

## 11. 预览运行

`POST /api/preview/run`

请求体:

```json
{
  "strategy_id": 1,
  "code": "import backtrader as bt\n...",
  "params": {
    "start_date": "2025-01-01",
    "end_date": "2025-01-31",
    "frequency": "1d",
    "initial_capital": 1000000
  }
}
```

成功响应 `data`:

```json
{
  "success": true,
  "logs": [
    {
      "id": 1,
      "log_time": "2026-03-21T18:10:00",
      "level": "INFO",
      "message": "预览参数: 2025-01-01 ~ 2025-01-31"
    }
  ],
  "summary": {
    "total_return": 1.25,
    "final_equity": 1012500,
    "initial_value": 1000000
  },
  "equity_curve": [],
  "error": null
}
```

失败响应特征:

- HTTP 状态仍为 `200`
- `code` 为 `1`
- `data.success` 为 `false`
- `data.logs` 和 `data.error` 仍可用于前端展示

预览模式语义:

- 只用于快速验证策略代码是否可运行
- 当前固定使用近 365 天、单股票真实行情数据快速返回结果
- 不作为最终回测结果依据

## 当前前端联调注意事项

- 编辑页“运行回测”必须走两步:
  1. `POST /api/backtests`
  2. `POST /api/backtests/{id}/run`
- 详情页应该把 `pending/running` 视为可轮询态，并按需刷新进度、日志、交易、净值、性能。
- 预览接口失败时不要只按异常处理，优先展示 `data.error` 与 `data.logs`。
- 当前最终回测默认使用真实股票 `000001.SZ` 日线数据，适合演示单标的策略；多股票策略与更复杂因子策略仍需继续扩展数据装载层。
