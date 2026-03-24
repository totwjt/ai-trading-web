# 模拟交易服务 API

## 路由与页面映射

| 前端路由 | 组件 | 说明 |
|----------|------|------|
| `/simulation` | SimulationList.vue | 模拟交易列表页 |
| `/simulation/detail/{id}` | SimulationDetail.vue | 模拟交易详情页 |

---

## 页面功能

### 1. 模拟交易列表页 (`/simulation`)

**功能列表：**
- 显示所有模拟交易记录（名称、状态、资金、收益、持仓、胜率等）
- 搜索筛选：按名称/策略搜索，按状态筛选（全部/运行中/已暂停/已完成）
- 统计卡片：运行中数量、累计收益率、今日盈亏、策略库数量
- 新建模拟：弹框选择策略创建新模拟
- 暂停/恢复：控制模拟状态
- 查看详情：跳转到详情页

### 2. 模拟交易详情页 (`/simulation/detail/{id}`)

**功能列表：**
- 显示模拟信息（名称、状态、策略名称）
- 持仓股票列表：股票名称、代码、数量、成本、现价、市值、盈亏
- 账户信息：初始/可用/持仓/冻结资金，累计/今日收益，胜率，交易次数
- 交易记录：时间、股票、方向、价格、数量、金额、状态
- 控制操作：订单状态

---

## API 接口需求

### 模拟交易管理

#### 获取模拟交易列表

```
GET /api/simulations
```

**Query 参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码，默认 1 |
| page_size | int | 否 | 每页数量，默认 10 |
| status | string | 否 | 状态筛选 (running/paused/completed) |
| search | string | 否 | 搜索关键词 |

**响应示例：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total": 4,
    "page": 1,
    "page_size": 10,
    "items": [
      {
        "id": 1,
        "name": "趋势先行A模拟",
        "strategyName": "趋势先行A (大盘股)",
        "status": "running",
        "initialCapital": 1000000,
        "currentCapital": 1124800,
        "totalReturn": 12.48,
        "todayReturn": 1.24,
        "todayPL": 13840,
        "holdingsValue": 824500,
        "holdingsCount": 3,
        "winRate": 68.5,
        "tradeCount": 142,
        "startDate": "2024-01-15",
        "lastTradeDateTime": "2024-01-15 10:32:15"
      }
    ]
  }
}
```

---

#### 获取统计信息

```
GET /api/simulations/stats
```

**响应示例：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "runningCount": 2,
    "totalSimulations": 4,
    "totalReturn": 50.68,
    "totalTodayPL": 12160,
    "strategyCount": 4
  }
}
```

**返回字段说明：**
| 字段 | 类型 | 说明 |
|------|------|------|
| runningCount | int | 运行中模拟数量 |
| totalSimulations | int | 模拟总数 |
| totalReturn | float | 累计收益率 (%) |
| totalTodayPL | float | 今日盈亏金额 |

---

#### 创建模拟交易

```
POST /api/simulations
```

**请求体：**
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| strategy_id | int | 是 | 策略ID |
| initial_capital | float | 否 | 初始资金，默认 1000000 |

**响应：**
```json
{
  "code": 0,
  "message": "模拟创建成功",
  "data": {
    "id": 1
  }
}
```

---

#### 获取模拟详情

```
GET /api/simulations/{id}
```

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "name": "趋势先行A模拟",
    "strategyName": "趋势先行A (大盘股)",
    "status": "running",
    "statusText": "运行中",
    "initialCapital": 1000000,
    "currentCapital": 1124800,
    "totalReturn": 12.48,
    "todayReturn": 1.24,
    "todayPL": 13840,
    "holdingsValue": 824500,
    "holdingsCount": 3,
    "winRate": 68.5,
    "tradeCount": 142,
    "startDate": "2024-01-15",
    "lastTradeDateTime": "10:32:15",
    "availableCapital": 300300,
    "frozenCapital": 0
  }
}
```

---

### 持仓管理

#### 获取持仓股票列表

```
GET /api/simulations/{id}/holdings
```

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": 1,
      "name": "贵州茅台",
      "code": "600519.SH",
      "quantity": 100,
      "avgCost": 1850.00,
      "currentPrice": 1880.50,
      "marketValue": 188050.00,
      "pl": 3050.00,
      "plPercent": 1.65,
      "weight": 22.8
    }
  ]
}
```

---

### 交易记录

#### 获取交易记录

```
GET /api/simulations/{id}/trades
```

**Query 参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码，默认 1 |
| page_size | int | 否 | 每页数量，默认 20 |

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total": 142,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        "id": 1,
        "time": "10:32:15",
        "stockName": "中国平安",
        "stockCode": "601318.SH",
        "direction": "buy",
        "directionText": "买入",
        "price": 41.20,
        "quantity": 1000,
        "amount": 41200.00,
        "status": "已成交"
      }
    ]
  }
}
```

---

### 控制操作

#### 暂停模拟

```
POST /api/simulations/{id}/pause
```

**响应：**
```json
{
  "code": 0,
  "message": "模拟已暂停",
  "data": {
    "id": 1,
    "status": "paused"
  }
}
```

---

#### 恢复模拟

```
POST /api/simulations/{id}/resume
```

**响应：**
```json
{
  "code": 0,
  "message": "模拟已恢复",
  "data": {
    "id": 1,
    "status": "running"
  }
}
```

---

#### 结束模拟

```
POST /api/simulations/{id}/stop
```

**响应：**
```json
{
  "code": 0,
  "message": "模拟已结束",
  "data": {
    "id": 1,
    "status": "completed"
  }
}
```

---

## API 汇总

| 功能 | Method | Path |
|------|--------|------|
| 获取模拟列表 | GET | `/api/simulations` |
| 获取统计信息 | GET | `/api/simulations/stats` |
| 创建模拟 | POST | `/api/simulations` |
| 获取模拟详情 | GET | `/api/simulations/{id}` |
| 获取持仓列表 | GET | `/api/simulations/{id}/holdings` |
| 获取交易记录 | GET | `/api/simulations/{id}/trades` |
| 暂停模拟 | POST | `/api/simulations/{id}/pause` |
| 恢复模拟 | POST | `/api/simulations/{id}/resume` |
| 结束模拟 | POST | `/api/simulations/{id}/stop` |

---

## 备注

- 当前前端页面使用 mock 静态数据，未对接后端 API
- 需要后端实现 simulation 服务相关接口
- 策略列表可复用已有 `/api/strategies` 接口

---

## WebSocket 即时通讯

**WebSocket 地址：** `ws://localhost:8765`

**消息格式：**
```json
{
  "type": "message_type",
  "payload": {},
  "timestamp": "2024-01-15T10:30:00",
  "message_id": "msg_1705312200.123"
}
```

### 消息类型

#### 1. 连接

**客户端发送：**
```json
{
  "type": "connect",
  "payload": {
    "client_type": "web",
    "client_id": "simulation_detail_2"
  },
  "timestamp": "2024-01-15T10:30:00",
  "message_id": "msg_1705312200.123"
}
```

**服务端响应：**
```json
{
  "type": "system",
  "payload": {
    "status": "connected",
    "client_id": "simulation_detail_2",
    "client_type": "web",
    "server_time": "2024-01-15T10:30:00"
  },
  "timestamp": "2024-01-15T10:30:00",
  "message_id": "msg_1705312200.456"
}
```

---

#### 2. 订阅模拟详情

**客户端发送：**
```json
{
  "type": "subscribe",
  "payload": {
    "action": "simulation_detail",
    "topics": ["simulation_2_holdings", "simulation_2_trades"],
    "client_id": "simulation_detail_2"
  },
  "timestamp": "2024-01-15T10:30:00",
  "message_id": "msg_1705312200.789"
}
```

**服务端响应：**
```json
{
  "type": "system",
  "payload": {
    "status": "subscribed",
    "topics": ["simulation_2_holdings", "simulation_2_trades"]
  },
  "timestamp": "2024-01-15T10:30:00",
  "message_id": "msg_1705312200.abc"
}
```

---

#### 3. 推送模拟数据

**服务端推送：**
```json
{
  "type": "simulation",
  "payload": {
    "simulation_id": 2,
    "event": "holdings_update",
    "data": {
      "currentCapital": 1124800,
      "todayPL": 13840,
      "holdings": [
        {
          "id": 1,
          "name": "贵州茅台",
          "code": "600519.SH",
          "quantity": 100,
          "currentPrice": 1880.50,
          "marketValue": 188050.00,
          "pl": 3050.00
        }
      ]
    }
  },
  "timestamp": "2024-01-15T10:30:00",
  "message_id": "msg_1705312200.def"
}
```

---

#### 4. 心跳

**客户端发送：**
```json
{
  "type": "heartbeat",
  "payload": {},
  "timestamp": "2024-01-15T10:30:00",
  "message_id": "msg_1705312200.ghi"
}
```

**服务端响应：**
```json
{
  "type": "heartbeat",
  "payload": {
    "status": "pong",
    "server_time": "2024-01-15T10:30:00"
  },
  "timestamp": "2024-01-15T10:30:00",
  "message_id": "msg_1705312200.jkl"
}
```

---

### 模拟详情页 WebSocket 事件

| 事件 | 说明 | payload |
|------|------|---------|
| `holdings_update` | 持仓更新 | 持仓列表、持仓市值 |
| `trades_update` | 交易记录更新 | 新增交易记录 |
| `simulation_update` | 模拟状态更新 | 当前资金、今日盈亏、状态 |
| `trade_executed` | 新交易成交 | 交易详情 |
