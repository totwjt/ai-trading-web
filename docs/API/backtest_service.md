# 策略与回测服务 API 文档

> 本文档基于 `http://localhost:3000/backtest` 前端页面分析，定义策略管理和回测系统所需的后端接口。

## 基础信息

| 项目 | 值 |
|------|-----|
| 服务端口 | `8766` (HTTP) / `8765` (WebSocket) |
| API 前缀 | `/api` |
| 数据格式 | JSON |
| 认证方式 | 待定 (预留 `Authorization` Header) |

## 目录

- [1. 策略管理 API](#1-策略管理-api)
  - [1.1 获取策略列表](#11-获取策略列表)
  - [1.2 获取策略详情](#12-获取策略详情)
  - [1.3 创建策略](#13-创建策略)
  - [1.4 更新策略](#14-更新策略)
  - [1.5 删除策略](#15-删除策略)
  - [1.6 策略启停控制](#16-策略启停控制)
- [2. 策略模板 API](#2-策略模板-api)
  - [2.1 获取策略模板列表](#21-获取策略模板列表)
  - [2.2 获取模板详情](#22-获取模板详情)
- [3. 回测管理 API](#3-回测管理-api)
  - [3.1 运行回测](#31-运行回测)
  - [3.2 获取回测结果](#32-获取回测结果)
  - [3.3 获取回测进度](#33-获取回测进度)
  - [3.4 取消回测](#34-取消回测)
  - [3.5 获取回测交易明细](#35-获取回测交易明细)
  - [3.6 获取回测系统日志](#36-获取回测系统日志)
  - [3.7 获取净值曲线数据](#37-获取净值曲线数据)
- [4. 回测性能指标 API](#4-回测性能指标-api)
- [5. WebSocket 实时推送](#5-websocket-实时推送)

---

## 1. 策略管理 API

### 1.1 获取策略列表

获取用户的所有策略列表。

```
GET /api/strategies
```

**Query 参数:**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| page | int | 否 | 1 | 页码 |
| page_size | int | 否 | 10 | 每页数量 (最大100) |
| status | string | 否 | - | 筛选状态: `running` / `paused` |

**响应示例:**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total": 3,
    "page": 1,
    "page_size": 10,
    "items": [
      {
        "id": 1,
        "name": "趋势先行A (大盘股)",
        "type": "MA交叉策略",
        "status": "running",
        "holdings": ["贵州茅台", "招商银行"],
        "returns": "+12.4%",
        "win_rate": "68.2%",
        "trade_count": 142,
        "risk_level": "中风险",
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-03-20T14:22:00Z"
      }
    ]
  },
  "timestamp": "2024-03-21T10:00:00Z"
}
```

---

### 1.2 获取策略详情

获取单个策略的详细信息。

```
GET /api/strategies/{strategy_id}
```

**路径参数:**

| 参数 | 类型 | 说明 |
|------|------|------|
| strategy_id | int | 策略ID |

**响应示例:**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "name": "趋势先行A (大盘股)",
    "type": "MA交叉策略",
    "status": "running",
    "code": "import pandas as pd\nfrom gzt_api import Strategy, Order\n\nclass ValueStrategy(Strategy):\n    def on_init(self):\n        self.universe = ['000001.SH', '600519.SH']\n        self.set_benchmark('000300.SH')\n    \n    def on_bar(self, bar):\n        ma5 = bar.close.rolling(5).mean()\n        ma20 = bar.close.rolling(20).mean()\n        # ...\n",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-03-20T14:22:00Z"
  },
  "timestamp": "2024-03-21T10:00:00Z"
}
```

---

### 1.3 创建策略

创建新的策略。

```
POST /api/strategies
```

**请求体:**

```json
{
  "name": "新策略名称",
  "type": "MA交叉策略",
  "code": "import pandas as pd\n...",
  "config": {
    "initial_capital": 1000000,
    "commission": 0.0003,
    "slippage": 0.0001
  }
}
```

**字段说明:**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 策略名称 (最大50字符) |
| type | string | 否 | 策略类型 |
| code | string | 是 | Python策略代码 |
| config | object | 否 | 策略配置参数 |

**响应示例:**

```json
{
  "code": 0,
  "message": "策略创建成功",
  "data": {
    "id": 4,
    "name": "新策略名称"
  },
  "timestamp": "2024-03-21T10:00:00Z"
}
```

---

### 1.4 更新策略

更新策略代码或配置。

```
PUT /api/strategies/{strategy_id}
```

**请求体:**

```json
{
  "name": "更新后的策略名称",
  "code": "import pandas as pd\n...",
  "config": {
    "initial_capital": 1000000,
    "commission": 0.0003
  }
}
```

**响应示例:**

```json
{
  "code": 0,
  "message": "策略更新成功",
  "data": {
    "id": 1,
    "updated_at": "2024-03-21T10:05:00Z"
  },
  "timestamp": "2024-03-21T10:00:00Z"
}
```

---

### 1.5 删除策略

删除指定的策略。

```
DELETE /api/strategies/{strategy_id}
```

**响应示例:**

```json
{
  "code": 0,
  "message": "策略删除成功",
  "data": null,
  "timestamp": "2024-03-21T10:00:00Z"
}
```

---

### 1.6 策略启停控制

启动或暂停策略运行。

```
POST /api/strategies/{strategy_id}/action
```

**请求体:**

```json
{
  "action": "start"   // 或 "stop" / "pause"
}
```

**响应示例:**

```json
{
  "code": 0,
  "message": "策略已启动",
  "data": {
    "id": 1,
    "status": "running"
  },
  "timestamp": "2024-03-21T10:00:00Z"
}
```

---

## 2. 策略模板 API

### 2.1 获取策略模板列表

获取预置的策略模板列表，供用户引用或参考。

```
GET /api/strategy-templates
```

**Query 参数:**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| category | string | 否 | - | 模板分类: `stock` / `etf` / `futures` |

**响应示例:**

```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": 1,
      "name": "风格轮动",
      "category": "stock",
      "description": "基于价值、成长、质量等多因子，自动捕捉当前市场强势风格并进行行业均衡配置。",
      "annual_return": "24.8%",
      "sharpe_ratio": null,
      "max_drawdown": null,
      "win_rate": null,
      "tags": ["多因子", "风格轮动"]
    },
    {
      "id": 2,
      "name": "日内回转交易 (T+0)",
      "category": "stock",
      "description": "针对高波动性标的，通过高频价格监控实现日内低买高卖，不留底仓风险。",
      "annual_return": null,
      "sharpe_ratio": null,
      "max_drawdown": null,
      "win_rate": "62.1%",
      "tags": ["T+0", "高频"]
    },
    {
      "id": 3,
      "name": "小市值因子策略",
      "category": "stock",
      "description": "筛选低估值、高成长潜力的小市值标的，利用市场非对称信息获取长期超额回报。",
      "annual_return": null,
      "sharpe_ratio": "2.1",
      "max_drawdown": null,
      "win_rate": null,
      "tags": ["小市值", "价值投资"]
    },
    {
      "id": 4,
      "name": "行业轮动ETF",
      "category": "etf",
      "description": "基于行业景气度轮动，配置不同行业ETF，实现行业alpha收益。",
      "annual_return": null,
      "sharpe_ratio": null,
      "max_drawdown": "8.5%",
      "win_rate": null,
      "tags": ["ETF", "行业轮动"]
    }
  ],
  "timestamp": "2024-03-21T10:00:00Z"
}
```

---

### 2.2 获取模板详情

获取策略模板的完整代码和配置。

```
GET /api/strategy-templates/{template_id}
```

**响应示例:**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "name": "风格轮动",
    "category": "stock",
    "description": "...",
    "code": "import pandas as pd\nfrom gzt_api import Strategy\n\nclass StyleRotationStrategy(Strategy):\n    def on_init(self):\n        # 初始化多因子权重\n        pass\n    \n    def on_bar(self, bar):\n        # 风格轮动逻辑\n        pass\n",
    "config": {
      "initial_capital": 1000000,
      "commission": 0.0003
    },
    "performance": {
      "annual_return": "24.8%",
      "sharpe_ratio": 1.85,
      "max_drawdown": "-12.3%",
      "win_rate": "65.2%"
    }
  },
  "timestamp": "2024-03-21T10:00:00Z"
}
```

---

## 3. 回测管理 API

### 3.1 运行回测

启动策略回测任务。

```
POST /api/backtests
```

**请求体:**

```json
{
  "strategy_id": 1,
  "params": {
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "frequency": "1d",      // "1d"=日线, "1w"=周线, "1m"=1分钟, "5m"=5分钟, "15m"=15分钟
    "initial_capital": 1000000
  }
}
```

**字段说明:**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| strategy_id | int | 是 | 策略ID |
| params.start_date | string | 是 | 开始日期 (YYYY-MM-DD) |
| params.end_date | string | 是 | 结束日期 (YYYY-MM-DD) |
| params.frequency | string | 否 | 数据频率，默认 "1d" |
| params.initial_capital | number | 否 | 初始资金，默认 1000000 |

**响应示例:**

```json
{
  "code": 0,
  "message": "回测任务已创建",
  "data": {
    "backtest_id": "bt_20240321_001",
    "strategy_id": 1,
    "status": "running",
    "progress": 0,
    "created_at": "2024-03-21T10:00:00Z"
  },
  "timestamp": "2024-03-21T10:00:00Z"
}
```

---

### 3.2 获取回测结果

获取已完成回测的详细结果。

```
GET /api/backtests/{backtest_id}
```

**响应示例:**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "backtest_id": "bt_20240321_001",
    "strategy_id": 1,
    "strategy_name": "DualMovingAverageCross_V2",
    "status": "completed",
    "params": {
      "start_date": "2023-01-01",
      "end_date": "2023-12-31",
      "frequency": "1d",
      "initial_capital": 1000000
    },
    "results": {
      "final_equity": 1324412.00,
      "total_return": "+32.44%",
      "benchmark_return": "+15.20%",
      "excess_return": "+17.24%",
      "benchmark": "跑赢基准"
    },
    "created_at": "2024-03-21T10:00:00Z",
    "completed_at": "2024-03-21T10:00:15Z"
  },
  "timestamp": "2024-03-21T10:00:00Z"
}
```

---

### 3.3 获取回测进度

获取正在运行中的回测任务进度。

```
GET /api/backtests/{backtest_id}/progress
```

**响应示例:**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "backtest_id": "bt_20240321_001",
    "status": "running",
    "progress": 45,
    "current_date": "2023-06-15",
    "message": "正在回测 2023-06-15..."
  },
  "timestamp": "2024-03-21T10:00:00Z"
}
```

---

### 3.4 取消回测

取消正在运行的回测任务。

```
POST /api/backtests/{backtest_id}/cancel
```

**响应示例:**

```json
{
  "code": 0,
  "message": "回测任务已取消",
  "data": {
    "backtest_id": "bt_20240321_001",
    "status": "cancelled"
  },
  "timestamp": "2024-03-21T10:00:00Z"
}
```

---

### 3.5 获取回测交易明细

获取回测产生的交易记录列表。

```
GET /api/backtests/{backtest_id}/trades
```

**Query 参数:**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| page | int | 否 | 1 | 页码 |
| page_size | int | 否 | 50 | 每页数量 |

**响应示例:**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total": 1284,
    "page": 1,
    "page_size": 50,
    "items": [
      {
        "time": "2023-12-28 14:35",
        "code": "600519.SH",
        "name": "贵州茅台",
        "type": "SELL",
        "price": 1728.50,
        "quantity": -200,
        "amount": -345700.00,
        "profit": 12227.15,
        "commission": 103.71
      },
      {
        "time": "2023-12-27 10:15",
        "code": "300750.SZ",
        "name": "宁德时代",
        "type": "BUY",
        "price": 163.20,
        "quantity": 1000,
        "amount": 163200.00,
        "profit": null,
        "commission": 48.96
      }
    ]
  },
  "timestamp": "2024-03-21T10:00:00Z"
}
```

---

### 3.6 获取回测系统日志

获取回测执行过程中的系统日志。

```
GET /api/backtests/{backtest_id}/logs
```

**响应示例:**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "backtest_id": "bt_20240321_001",
    "error_count": 0,
    "warning_count": 2,
    "logs": [
      {
        "time": "2023-12-31 23:59:59",
        "level": "INFO",
        "message": "Cerebro engine initialized."
      },
      {
        "time": "2023-12-31 23:59:59",
        "level": "INFO",
        "message": "Loading data feeds for 15 assets..."
      },
      {
        "time": "2024-01-01 00:00:01",
        "level": "INFO",
        "message": "Adding Strategy 'DualMovingAverageCross_V2' to Brain."
      },
      {
        "time": "2024-01-01 00:00:02",
        "level": "INFO",
        "message": "Starting backtest loop..."
      },
      {
        "time": "2024-01-01 00:00:05",
        "level": "WARN",
        "message": "Missing data points for 002371.SZ on 2021-05-12. Interpolating."
      },
      {
        "time": "2024-01-01 00:00:12",
        "level": "WARN",
        "message": "Margin call threshold reached on 2022-04-15. No action taken."
      },
      {
        "time": "2024-01-01 00:00:15",
        "level": "SUCCESS",
        "message": "Backtest completed in 14.2s."
      },
      {
        "time": "2024-01-01 00:00:15",
        "level": "INFO",
        "message": "Final Value: 1,324,412.00 (Cash: 245,820.45)"
      }
    ]
  },
  "timestamp": "2024-03-21T10:00:00Z"
}
```

---

### 3.7 获取净值曲线数据

获取回测的权益曲线数据，用于绑制图表。

```
GET /api/backtests/{backtest_id}/equity-curve
```

**Query 参数:**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| frequency | string | 否 | "1d" | 数据频率: `1d` / `1w` |

**响应示例:**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "backtest_id": "bt_20240321_001",
    "benchmark": "CSI300",
    "frequency": "1d",
    "data_points": [
      {
        "date": "2023-01-03",
        "equity": 1000000.00,
        "benchmark": 1000.00,
        "returns": 0.00
      },
      {
        "date": "2023-01-04",
        "equity": 1005230.50,
        "benchmark": 995.80,
        "returns": 0.52
      }
    ]
  },
  "timestamp": "2024-03-21T10:00:00Z"
}
```

---

## 4. 回测性能指标 API

获取回测的综合性能分析指标。

```
GET /api/backtests/{backtest_id}/performance
```

**响应示例:**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "backtest_id": "bt_20240321_001",
    "summary": {
      "total_return": "+32.44%",
      "annual_return": "+18.20%",
      "max_drawdown": "-5.12%",
      "sharpe_ratio": 2.14,
      "win_rate": "62.5%",
      "profit_loss_ratio": 1.85
    },
    "metrics": {
      "calmar_ratio": 3.56,
      "sortino_ratio": 2.89,
      "volatility": "12.3%",
      "beta": 0.85,
      "alpha": "8.2%",
      "information_ratio": 1.23,
      "max_consecutive_wins": 8,
      "max_consecutive_losses": 3,
      "avg_holding_days": 15.2,
      "total_trades": 1284,
      "avg_profit_per_trade": 252.30
    }
  },
  "timestamp": "2024-03-21T10:00:00Z"
}
```

**指标说明:**

| 指标 | 说明 |
|------|------|
| total_return | 总收益率 |
| annual_return | 年化收益率 |
| max_drawdown | 最大回撤 |
| sharpe_ratio | 夏普比率 |
| win_rate | 胜率 |
| profit_loss_ratio | 盈亏比 |
| calmar_ratio | 卡玛比率 |
| sortino_ratio | 索提诺比率 |
| volatility | 波动率 |
| beta | Beta 系数 |
| alpha | Alpha 收益 |
| information_ratio | 信息比率 |

---

## 5. WebSocket 实时推送

连接 WebSocket 服务，接收回测进度和结果的实时推送。

### 连接地址

```
ws://localhost:8765/ws
```

### 连接握手

连接成功后服务端会发送欢迎消息：

```json
{
  "type": "system",
  "payload": {
    "status": "connected",
    "server_time": "2024-03-21T10:00:00Z"
  },
  "timestamp": "2024-03-21T10:00:00Z",
  "message_id": "msg_1711000800"
}
```

### 订阅回测进度

发送订阅消息以接收特定回测任务的进度更新：

```json
{
  "type": "subscribe",
  "payload": {
    "client_type": "web",
    "client_id": "user_001",
    "topics": ["backtest.bt_20240321_001"]
  }
}
```

### 接收回测进度更新

服务端推送的进度消息：

```json
{
  "type": "backtest_progress",
  "payload": {
    "backtest_id": "bt_20240321_001",
    "progress": 45,
    "current_date": "2023-06-15",
    "equity": 1150000.00
  },
  "timestamp": "2024-03-21T10:00:00Z",
  "message_id": "msg_1711000801"
}
```

### 接收回测完成消息

```json
{
  "type": "backtest_completed",
  "payload": {
    "backtest_id": "bt_20240321_001",
    "status": "completed",
    "results": {
      "total_return": "+32.44%",
      "final_equity": 1324412.00
    }
  },
  "timestamp": "2024-03-21T10:00:15Z",
  "message_id": "msg_1711000815"
}
```

### 心跳消息

客户端应定期发送心跳以保持连接：

```json
{
  "type": "heartbeat",
  "payload": {}
}
```

服务端响应：

```json
{
  "type": "heartbeat",
  "payload": {
    "status": "pong",
    "server_time": "2024-03-21T10:00:00Z"
  }
}
```

---

## 通用响应格式

所有 API 统一使用以下响应格式：

```json
{
  "code": 0,           // 0=成功, 非0=失败
  "message": "success", // 状态描述
  "data": {},          // 响应数据
  "timestamp": ""      // 服务器时间戳
}
```

### 错误响应

```json
{
  "code": 404,
  "message": "策略不存在",
  "data": null,
  "timestamp": "2024-03-21T10:00:00Z"
}
```

### HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## 附录：前端页面路由

| 路由 | 页面 | 说明 |
|------|------|------|
| `/backtest` | 策略中心 | 显示策略列表和模板 |
| `/backtest/edit/:id?` | 编辑策略 | Python 代码编辑器 |
| `/backtest/detail/:id` | 回测详情 | 净值曲线、交易明细 |

---

## 更新日志

| 日期 | 版本 | 更新内容 |
|------|------|----------|
| 2024-03-21 | v1.0 | 初始版本 |
