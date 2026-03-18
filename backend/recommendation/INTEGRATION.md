# 智能荐股 WebSocket 接入文档

## 概述

本文档描述外部咨询项目如何通过 WebSocket 连接到智能荐股服务，推送新闻分析数据，实现与 Vue3 前端实时互动。

## 服务器信息

| 项目 | 值 |
|------|-----|
| 地址 | `ws://192.168.66.186:8765` |
| 协议 | WebSocket (ws) |
| 数据格式 | JSON |

## 消息格式

### 推送数据结构

```json
{
  "news": {
    "title": "新闻标题",
    "content": "新闻内容摘要",
    "publish_time": "2026-03-16 11:38:00",
    "crawl_time": "2026-03-16 11:47:04",
    "source": "新闻来源",
    "url": "https://example.com/news"
  },
  "analysis": {
    "利好版块": ["板块1", "板块2", "板块3"],
    "利好股票": [
      "600000(股票名称85)",
      "000001(股票名称90)"
    ],
    "分析因素": ["因素1", "因素2"],
    "详细分析": "详细分析内容..."
  }
}
```

### 利好股票格式

每只股票格式：`股票代码(股票名称评分)`

示例：
- `600519(贵州茅台91)`
- `000001(平安银行88)`
- `688012(中微公司96)`

## Python 客户端接入

### 1. 安装依赖

```bash
pip install websockets
```

### 2. 快速接入代码

```python
import asyncio
import json
from datetime import datetime
import websockets


async def push_recommendation(news_data: dict, analysis_data: dict):
    """推送荐股数据到服务器"""
    uri = "ws://192.168.66.186:8765"
    
    message = {
        "type": "recommendation",
        "payload": {
            "news": {
                "title": news_data["title"],
                "content": news_data.get("content", ""),
                "publish_time": news_data.get("publish_time", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                "crawl_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "source": news_data.get("source", ""),
                "url": news_data.get("url", "")
            },
            "analysis": {
                "利好版块": analysis_data.get("利好版块", []),
                "利好股票": analysis_data.get("利好股票", []),
                "分析因素": analysis_data.get("分析因素", []),
                "详细分析": analysis_data.get("详细分析", "")
            }
        },
        "timestamp": datetime.now().isoformat(),
        "message_id": f"msg_{datetime.now().timestamp()}"
    }
    
    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps(message, ensure_ascii=False))
        print(f"推送成功: {news_data['title']}")


# 使用示例
if __name__ == "__main__":
    news = {
        "title": "Meta裁员1.6万人 中层成重灾区",
        "content": "Meta裁员1.6万人...",
        "source": "东方财富",
        "publish_time": "2026-03-16 11:38:00",
        "url": "https://example.com"
    }
    
    analysis = {
        "利好版块": ["人力资源服务", "企业管理软件", "云计算"],
        "利好股票": ["603258(电科数字65)", "002261(拓维信息62)", "600588(用友网络60)"],
        "分析因素": ["因素1", "因素2"],
        "详细分析": "详细分析内容..."
    }
    
    asyncio.run(push_recommendation(news, analysis))
```

### 3. 带心跳的持续连接

```python
import asyncio
import json
from datetime import datetime
import websockets


class RecommendationPusher:
    def __init__(self, uri="ws://192.168.66.186:8765", client_type="external_crawler"):
        self.uri = uri
        self.client_type = client_type
        self.websocket = None
    
    async def connect(self):
        self.websocket = await websockets.connect(self.uri)
        
        connect_msg = {
            "type": "connect",
            "payload": {
                "client_id": f"crawler_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "client_type": self.client_type
            },
            "timestamp": datetime.now().isoformat(),
            "message_id": f"msg_{datetime.now().timestamp()}"
        }
        await self.websocket.send(json.dumps(connect_msg))
        print("已连接")
    
    async def push(self, news_data: dict, analysis_data: dict):
        if not self.websocket:
            await self.connect()
        
        message = {
            "type": "recommendation",
            "payload": {
                "news": {
                    "title": news_data["title"],
                    "content": news_data.get("content", ""),
                    "publish_time": news_data.get("publish_time", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                    "crawl_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "source": news_data.get("source", ""),
                    "url": news_data.get("url", "")
                },
                "analysis": {
                    "利好版块": analysis_data.get("利好版块", []),
                    "利好股票": analysis_data.get("利好股票", []),
                    "分析因素": analysis_data.get("分析因素", []),
                    "详细分析": analysis_data.get("详细分析", "")
                }
            },
            "timestamp": datetime.now().isoformat(),
            "message_id": f"msg_{datetime.now().timestamp()}"
        }
        
        await self.websocket.send(json.dumps(message, ensure_ascii=False))
        print(f"推送成功: {news_data['title'][:30]}...")
    
    async def close(self):
        if self.websocket:
            await self.websocket.close()


# 在抓取新闻时调用
async def on_news_crawled(news_item, analysis_result):
    pusher = RecommendationPusher()
    await pusher.push(news_item, analysis_result)
    await pusher.close()
```

## 推送时机

在爬虫/咨询项目抓取到新闻并完成分析后，立即调用推送接口：

```python
# 新闻抓取完成回调
def on_news_crawled(news_data):
    # 1. 进行AI分析（调用你的AI模型）
    analysis = ai_analyze(news_data)
    
    # 2. 推送数据到荐股服务
    asyncio.run(push_recommendation(news_data, analysis))
```

## 响应示例

成功推送后，Vue3 前端会显示：

```
┌─────────────────────────────────────────────────────────────┐
│ ● 实时连接                                                  │
├─────────────────────────────────────────────────────────────┤
│ [实时推送]  来源：东方财富 • 2026-03-16 11:38:00           │
│ Meta裁员1.6万人 中层成重灾区                                │
│                                                             │
│ AI解析逻辑：Meta裁员1.6万人且中层成重灾区...               │
│                                                             │
│ 利好板块: [人力资源服务] [企业管理软件] [云计算]           │
├─────────────────────────────────────────────────────────────┤
│ 利好股票     代码        AI评分    操作                    │
│ 电科数字     603258.SZ   65       [+]                      │
│ 拓维信息     002261.SZ   62       [+]                      │
│ 用友网络     600588.SH   60       [+]                      │
└─────────────────────────────────────────────────────────────┘
```

## 错误处理

| 错误码 | 说明 | 处理 |
|--------|------|------|
| 1006 | 连接异常关闭 | 自动重连 |
| 1011 | 服务器内部错误 | 检查服务器日志 |
| ECONNREFUSED | 连接被拒绝 | 检查服务器是否运行 |

## 完整示例：集成到爬虫

```python
import asyncio
import json
from datetime import datetime
import websockets


class NewsPusher:
    def __init__(self, server_url="ws://192.168.66.186:8765"):
        self.server_url = server_url
        self.connected = False
    
    async def connect(self):
        try:
            self.ws = await websockets.connect(self.server_url)
            
            await self.ws.send(json.dumps({
                "type": "connect",
                "payload": {
                    "client_id": f"crawler_{datetime.now().timestamp()}",
                    "client_type": "news_crawler"
                },
                "timestamp": datetime.now().isoformat(),
                "message_id": f"msg_{datetime.now().timestamp()}"
            }))
            
            self.connected = True
            print("已连接到荐股服务")
        except Exception as e:
            print(f"连接失败: {e}")
            self.connected = False
    
    async def push_news(self, news: dict, analysis: dict):
        if not self.connected:
            await self.connect()
        
        if not self.connected:
            return False
        
        message = {
            "type": "recommendation",
            "payload": {
                "news": {
                    "title": news["title"],
                    "content": news.get("content", ""),
                    "publish_time": news.get("publish_time", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                    "crawl_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "source": news.get("source", ""),
                    "url": news.get("url", "")
                },
                "analysis": analysis
            },
            "timestamp": datetime.now().isoformat(),
            "message_id": f"msg_{datetime.now().timestamp()}"
        }
        
        await self.ws.send(json.dumps(message, ensure_ascii=False))
        return True
    
    async def close(self):
        if self.ws:
            await self.ws.close()


# 使用方式
async def main():
    pusher = NewsPusher()
    
    # 模拟抓取到的新闻
    news = {
        "title": "测试新闻标题",
        "content": "新闻内容...",
        "source": "新闻源",
        "url": "https://example.com"
    }
    
    # 模拟AI分析结果
    analysis = {
        "利好版块": ["板块1", "板块2"],
        "利好股票": ["600000(股票190)", "000001(股票288)"],
        "分析因素": ["因素1"],
        "详细分析": "分析内容..."
    }
    
    await pusher.push_news(news, analysis)
    await pusher.close()


if __name__ == "__main__":
    asyncio.run(main())
```
