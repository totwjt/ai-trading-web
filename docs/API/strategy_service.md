# 策略服务 API

本文档以当前仓库 `backend/backtest/src/routers/strategy.py` 的实际 FastAPI 路由为准。

## 基础信息

- 服务前缀: `/api`
- 策略路由前缀: `/strategies`
- 通用响应:

```json
{
  "code": 0,
  "message": "success",
  "data": {},
  "timestamp": "2026-03-21T18:00:00"
}
```

## 数据模型

### StrategyConfig

```json
{
  "initial_capital": 1000000,
  "commission": 0.0003,
  "slippage": 0.0001
}
```

### 状态枚举

- `running`
- `paused`
- `stopped`
- `error`

## 1. 获取策略列表

`GET /api/strategies`

Query 参数:

- `page`: 页码，默认 `1`
- `page_size`: 每页数量，默认 `10`，最大 `100`
- `status`: 可选，枚举值同上

响应 `data`:

```json
{
  "total": 1,
  "page": 1,
  "page_size": 10,
  "items": [
    {
      "id": 1,
      "name": "测试均线策略",
      "strategy_type": "trend",
      "status": "paused",
      "created_at": "2026-03-21T17:06:35.954163",
      "updated_at": "2026-03-21T17:06:35.954163"
    }
  ]
}
```

## 2. 获取策略详情

`GET /api/strategies/{strategy_id}`

响应 `data`:

```json
{
  "id": 1,
  "name": "测试均线策略",
  "strategy_type": "trend",
  "status": "paused",
  "code": "import backtrader as bt\n...",
  "config": {
    "initial_capital": 1000000,
    "commission": 0.0003,
    "slippage": 0.0001
  },
  "description": "可选描述",
  "created_at": "2026-03-21T17:06:35.954163",
  "updated_at": "2026-03-21T17:06:35.954163"
}
```

## 3. 创建策略

`POST /api/strategies`

请求体:

```json
{
  "name": "均线交叉策略",
  "strategy_type": "custom",
  "code": "import backtrader as bt\n...",
  "config": {
    "initial_capital": 1000000,
    "commission": 0.0003,
    "slippage": 0.0001
  },
  "description": "可选描述"
}
```

说明:

- `name`、`code` 必填
- `strategy_type`、`config`、`description` 可选
- 后端会把新策略初始状态设为 `paused`

成功响应 `data`:

```json
{
  "id": 4,
  "name": "均线交叉策略"
}
```

## 4. 更新策略

`PUT /api/strategies/{strategy_id}`

请求体支持部分更新:

```json
{
  "name": "更新后的策略名称",
  "strategy_type": "custom",
  "code": "import backtrader as bt\n...",
  "config": {
    "initial_capital": 1000000,
    "commission": 0.0003,
    "slippage": 0.0001
  },
  "description": "更新后的描述"
}
```

成功响应 `data`:

```json
{
  "id": 1,
  "updated_at": "2026-03-21T18:05:00"
}
```

## 5. 删除策略

`DELETE /api/strategies/{strategy_id}`

成功响应 `data` 为 `null`。

## 6. 策略启停控制

`POST /api/strategies/{strategy_id}/action`

请求体:

```json
{
  "action": "start"
}
```

支持值:

- `start`
- `stop`
- `pause`

成功响应 `data`:

```json
{
  "id": 1,
  "status": "running"
}
```

## 当前前端联调注意事项

- 编辑页保存时建议同时提交 `strategy_type` 和 `config`，避免新建策略仅依赖后端默认值。
- 页面若只更新 `name`、`code` 也能成功，因为更新接口支持部分字段提交。
