# WebSocket 外部平台接入指南

## 连接格式

### 1. 连接时发送

```json
{
  "type": "connect",
  "payload": {
    "client_id": "唯一标识",
    "client_type": "web",
    "action": "default"
  },
  "timestamp": "2026-03-18T12:00:00.000Z",
  "message_id": "msg_123456"
}
```

### 2. 推送消息给前端

```json
{
  "type": "push",
  "payload": {
    "target_type": "web",
    "target_action": "default",
    "data": {
      "news": {
        "source": "新浪财经",
        "title": "节能风电：目前没有算力基地直连供电项目",
        "content": "有投资者问节能风电，公司有给算力基地供电项目吗？...",
        "url": "https://wap.cj.sina.cn/pc/7x24/4753081",
        "publish_time": "2026-03-18 15:36:59",
        "crawl_time": "2026-03-18 15:37:16"
      },
      "analysis": {
        "利好版块": ["风电设备、绿色电力"],
        "利好股票": [
          {"stock_code": "601016", "stock_name": "节能风电", "score": "60"}
        ],
        "分析因素": ["澄清市场传闻、排除算力概念炒作、聚焦主业"],
        "详细分析": "新闻中节能风电明确回应..."
      }
    }
  }
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

| 字段 | 说明 | 值 |
|------|------|-----|
| `client_id` | 客户端唯一标识 | 字符串 |
| `client_type` | 客户端类型 | `web` = 前端 |
| `action` | 业务模块 | `default` = 默认模块 |
| `target_type` | 推送目标类型 | `web` |
| `target_action` | 推送目标模块 | `default` |

## WebSocket 地址

```
ws://localhost:8765
```

局域网访问时替换为服务器 IP：
```
ws://192.168.66.186:8765
```
