# AI 智能荐股服务

WebSocket 实时荐股推送服务

## 快速开始

### 1. 创建虚拟环境

```bash
cd backend/ai
python -m venv venv
```

### 2. 激活虚拟环境

```bash
# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 启动 WebSocket 服务器

```bash
python websocket_server.py
```

服务将在 `ws://localhost:8765` 运行

## 目录结构

```
ai/
├── __init__.py          # Python 包标识
├── models.py            # 数据模型定义
├── websocket_server.py  # WebSocket 服务器
├── websocket_client.py  # 客户端示例（供其他项目接入）
├── requirements.txt     # Python 依赖
├── message.json         # 示例数据
└── src/                 # 源码目录（预留）
```

## 其他项目接入

参考 `websocket_client.py` 中的示例代码：

```python
import asyncio
from websocket_client import RecommendationWebSocketClient

async def main():
    client = RecommendationWebSocketClient(
        uri="ws://localhost:8765",
        client_type="your_project_name",
        on_message=lambda data: print("收到:", data)
    )
    await client.run()

asyncio.run(main())
```
