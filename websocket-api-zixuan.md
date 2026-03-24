# WebSocket 外部平台接入指南

## 连接格式

### 1. 连接时发送

```json
{
  "type": "connect",
  "payload": {
    "client_id": "唯一标识",
    "client_type": "zixuan",
    "action": "default"
  },
  "timestamp": "2026-03-18T12:00:00.000Z",
  "message_id": "z123456"
}
```

### 2. 推送消息给前端

```json
{
  "type": "push",
  "payload": {
    "target_type": "web",
    "target_action": "zixuan",
    "data": [
      {
        "ts_code": "600831.SH",
        "name": "广电网络",
        "pre_close": 3.62,
        "high": 3.82,
        "open": 3.74,
        "low": 3.65,
        "close": 3.81,
        "vol": 16148702,
        "amount": 60445298,
        "num": 10619,
        "ask_price1": 3.81,
        "ask_volume1": 23300,
        "bid_price1": 3.8,
        "bid_volume1": 78300,
        "trade_time": "2026-03-24 16:29:52"
      }
    ]
  },
  "timestamp": "2026-03-24T16:30:00.000Z",
  "message_id": "msg_1234567890"
}
```

### 3. 响应

服务器返回：

```json
{
  "type": "system",
  "payload": {
    "status": "pushed",
    "target": "web/default"
  }
}
```

## 参数说明

### 连接参数

| 字段 | 说明 | 值 |
|------|------|-----|
| `client_id` | 客户端唯一标识 | 字符串 |
| `client_type` | 客户端类型 | `web` = 前端, `server` = 服务器 |
| `action` | 业务模块 | `zixuan` = 自选股票 |
| `timestamp` | 时间戳 | ISO 格式 |
| `message_id` | 消息唯一ID | 字符串 |

### 推送数据字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `ts_code` | str | 股票代码 |
| `name` | str | 股票名称 |
| `pre_close` | float | 昨收价 |
| `high` | float | 最高价 |
| `open` | float | 开盘价 |
| `low` | float | 最低价 |
| `close` | float | 收盘价（最新价） |
| `vol` | int | 成交量（股） |
| `amount` | int | 成交金额（元） |
| `num` | int | 开盘以来成交笔数 |
| `ask_price1` | float | 委托卖盘（元） |
| `ask_volume1` | int | 委托卖盘（股） |
| `bid_price1` | float | 委托买盘（元） |
| `bid_volume1` | int | 委托买盘（股） |
| `trade_time` | str | 交易时间 |

## WebSocket 地址

```
ws://localhost:8765
```

局域网访问时替换为服务器 IP：
```
ws://192.168.66.186:8765
```
