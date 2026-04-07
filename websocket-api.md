# WebSocket API（统一 Socket.IO 服务）

> 更新时间：2026-04-03
> 面向对象：Web 前端、外部终端客户端、推送服务

## 1. 服务基础信息

- 服务地址：`http://192.168.66.186:8766`
- 协议：`Socket.IO`
- 命名空间：默认 `/`
- 连接路径：`/socket.io`

## 2. Topic 约定

### 2.1 历史通道（兼容）

- `zixuan`：自选股票行情
- `recommendation`：智能荐股
- `trading`：历史交易广播（旧）
- `risk`：风控消息
- `backtest.{id}`：回测主题

### 2.2 新增 trading-terminal 协议通道

- `trading-terminal.control.{userId}`：终端控制通道（新增/上线/离线/移除）
- `trading-terminal.{userId}.{terminalId}`：终端业务通道（实时交易记录/订单状态）

说明：
- `terminalId` 是动态值（例如 `terminal-node-1`、`desktop-a001`）。
- 一个用户可有多个终端，每个终端单独通道。
- `terminalId` 可选：若终端未传 `terminalId`，服务端会用 `macAddress` 生成稳定终端ID（格式：`mac-aa-bb-cc-dd-ee-ff`）。

## 3. 通用消息格式（trading-terminal）

`trading-terminal` 协议事件统一使用以下消息壳：

```json
{
  "v": "1.0",
  "msgId": "4b8c33bb-9fc9-41dd-a9cb-6ab0f3f80931",
  "ts": "2026-04-03T15:12:33.102345",
  "userId": "u_1001",
  "terminalId": "terminal-node-1",
  "eventType": "trade.record.append",
  "seq": 10231,
  "data": {}
}
```

字段说明：
- `v`：协议版本，当前 `1.0`
- `msgId`：消息唯一 ID
- `ts`：服务端时间（ISO8601）
- `userId`：用户 ID
- `terminalId`：终端 ID
- `eventType`：业务事件名
- `seq`：可选，终端内递增序号
- `data`：业务载荷

## 4. 事件协议

## 4.1 终端客户端 -> 服务端

### 4.1.1 `terminal_register`

用途：终端上线注册。

请求：

```json
{
  "userId": "u_1001",
  "terminalId": "terminal-node-1",
  "macAddress": "AA:BB:CC:DD:EE:FF",
  "terminalName": "柜台A",
  "accountName": "trader01",
  "status": "online"
}
```

服务端响应（发给当前连接）：`terminal_registered`

```json
{
  "userId": "u_1001",
  "terminalId": "terminal-node-1",
  "terminalName": "柜台A",
  "topic": "trading-terminal.u_1001.terminal-node-1",
  "controlTopic": "trading-terminal.control.u_1001",
  "status": "ok"
}
```

并在控制通道广播：
- `eventType=terminal.added`

说明：
- 在线/离线状态由终端 Python 服务通过 `terminal_status_update` 主动上报。
- `terminal_register` 不再默认代表“终端在线”。
- 若 `terminal_register` 请求中显式携带 `status=online`，服务端会立即标记在线并广播 `terminal.online`。
- 若未传 `terminalId`，必须传 `macAddress`，服务端将自动生成 `terminalId`。
- `terminalName`、`accountName` 均为可选；不传时服务端会使用默认值（或空字符串）。

---

### 4.1.2 `terminal_heartbeat`

用途：终端心跳保活。

请求：

```json
{
  "userId": "u_1001",
  "terminalId": "terminal-node-1",
  "ts": "2026-04-03T15:12:40.000Z"
}
```

服务端响应：`terminal_heartbeat_ack`

```json
{
  "status": "ok",
  "serverTime": "2026-04-03T15:12:40.210123"
}
```

---

### 4.1.3 `terminal_status_update`

用途：终端 Python 服务主动上报终端业务状态。

请求：

```json
{
  "userId": "u_1001",
  "terminalId": "terminal-node-1",
  "macAddress": "AA:BB:CC:DD:EE:FF",
  "status": "online",
  "reason": "terminal_connected"
}
```

说明：
- `status` 仅允许 `online` 或 `offline`
- `terminalId` 可选；不传时可用 `macAddress` 定位终端
- 服务端会在控制通道广播：
  - `eventType=terminal.online` 或 `eventType=terminal.offline`
  - `data.statusSource=terminal_service`

---

### 4.1.4 `terminal_unregister`

用途：终端主动下线并移除。

请求：

```json
{
  "userId": "u_1001",
  "terminalId": "terminal-node-1",
  "macAddress": "AA:BB:CC:DD:EE:FF"
}
```

服务端响应：`terminal_unregistered`

```json
{
  "userId": "u_1001",
  "terminalId": "terminal-node-1",
  "status": "ok"
}
```

并在控制通道广播 `eventType=terminal.removed`。

---

### 4.1.5 `push_trading_terminal`

用途：向终端业务通道推送交易事件（推荐入口）。

请求：

```json
{
  "userId": "u_1001",
  "terminalId": "terminal-node-1",
  "eventType": "trade.record.append",
  "seq": 10231,
  "data": {
    "tradeId": "t_9001",
    "time": "10:42:15",
    "symbol": "600519",
    "name": "贵州茅台",
    "side": "buy",
    "price": 1723.4,
    "qty": 500
  }
}
```

服务端行为：
- 转发到 `trading-terminal.{userId}.{terminalId}`
- 回 `push_ack`

---

## 4.2 Web 客户端 -> 服务端

### 4.2.1 `subscribe`

用于订阅 topic（通用机制）。

示例：

```json
{
  "topics": [
    "trading-terminal.control.u_1001",
    "trading-terminal.u_1001.terminal-node-1",
    "trading-terminal.u_1001.terminal-node-2"
  ]
}
```

---

### 4.2.2 `unsubscribe`

用于取消订阅 topic（通用机制）。

---

### 4.2.3 `terminal_snapshot_request`

用途：请求当前用户终端快照（首次进页面建议调用）。

请求：

```json
{
  "userId": "u_1001"
}
```

服务端响应：`terminal_snapshot`

```json
{
  "v": "1.0",
  "userId": "u_1001",
  "ts": "2026-04-03T15:20:00.100200",
  "terminals": [
    {
      "userId": "u_1001",
      "terminalId": "terminal-node-1",
      "terminalName": "柜台A",
      "online": true,
      "lastHeartbeatAt": "2026-04-03T15:19:59.900100",
      "connectedAt": "2026-04-03T14:00:00.000000",
      "updatedAt": "2026-04-03T15:19:59.900100"
    }
  ]
}
```

## 5. 服务端控制事件（Web 监听重点）

Web 端监听：`trading-terminal.control.{userId}`。

`eventType` 定义：
- `terminal.added`：新终端被注册
- `terminal.online`：终端在线
- `terminal.offline`：终端离线（断开/心跳超时）
- `terminal.removed`：终端被移除

离线原因（`data.reason`）：
- `terminal_status_update` 业务上报的自定义原因（推荐）
- `service_disconnect`：终端 Python 服务连接断开
- `service_heartbeat_timeout`：终端 Python 服务心跳超时

## 6. 心跳与离线策略

服务端配置：
- 心跳超时阈值：`30s`
- 检查周期：`5s`

建议终端客户端：
- 每 `10s` 发送一次 `terminal_heartbeat`

## 7. 兼容推送入口（保留）

仍支持旧事件 `push_from_external`：

```json
{
  "topic": "trading-terminal.u_1001.terminal-node-1",
  "data": {"any": "payload"}
}
```

说明：
- `push_from_external` 适合通用 topic 转发。
- `push_trading_terminal` 适合标准化 terminal 协议。

## 8. 推荐接入流程（给 Web 页面）

1. 连接后订阅 `trading-terminal.control.{userId}`。
2. 调用 `terminal_snapshot_request` 获取终端列表。
3. 对每个终端订阅 `trading-terminal.{userId}.{terminalId}`。
4. 收到 `terminal.added` 时动态新增终端卡片并订阅对应 topic。
5. 收到 `terminal.offline` 时更新终端状态为离线（保留历史记录）。
6. 收到 `terminal.removed` 时退订并从 UI 移除终端。

## 9. 错误事件

服务端错误事件：`terminal_error`

示例：

```json
{
  "message": "userId and terminalId are required"
}
```
