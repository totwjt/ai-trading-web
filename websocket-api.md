# WebSocket 统一服务

## 服务信息

| 项目 | 值 |
|------|-----|
| 地址 | `http://localhost:8766` (本机) / `http://192.168.66.186:8766` (局域网) |
| 协议 | Socket.IO |
| 事件 | `push_from_external` |

## Topic 列表

| Topic | 用途 |
|-------|------|
| `zixuan` | 自选股票行情 |
| `recommendation` | 智能荐股 |
| `trading` | 交易记录 |

## 推送格式

```python
await sio.emit('push_from_external', {
    'topic': 'zixuan',      # 目标 topic
    'data': [...] 或 {...}  # 见下方格式
})
```

## 数据格式

### zixuan

```python
# data: WatchlistItem[]
[
    {
        "ts_code": "600831.SH",
        "name": "广电网络",
        "pre_close": 3.62,
        "open": 3.74,
        "high": 3.85,
        "low": 3.65,
        "close": 3.85,
        "change": 0.23,
        "change_pct": 6.35,
        "vol": 18000000,
        "amount": 68000000,
        "num": null,
        "ask_price1": 3.85,
        "ask_volume1": 100,
        "bid_price1": 3.84,
        "bid_volume1": 200,
        "trade_time": "2026-03-25 14:30:00"
    }
]
```

### recommendation

```python
# data: RecommendationData
{
    "news": {
        "source": "新浪财经",
        "title": "电力板块盘初拉升",
        "content": "拓日新能、湖南发展双双涨停...",
        "publish_time": "2026-03-25 10:05",
        "url": "https://..."
    },
    "analysis": {
        "利好版块": ["电力", "绿电"],
        "利好股票": [
            {"stock_code": "002218", "stock_name": "拓日新能", "score": "100"},
            {"stock_code": "000900", "stock_name": "湖南发展", "score": "95"}
        ],
        "分析因素": ["板块涨停", "政策利好"],
        "详细分析": "电力板块今日表现强势..."
    }
}
```

### trading

```python
# data: TradeRecord[]
[
    {
        "id": 1,
        "ts_code": "600519",
        "name": "贵州茅台",
        "direction": "buy",
        "price": 1850.00,
        "quantity": 100,
        "amount": 185000.00,
        "time": "2024-01-15 10:30:25",
        "status": "success"
    }
]
```
