# 服务端口配置
## 前端 3000
## 后端服务 (Backend)

| 服务 | 端口 | 说明 |
|------|------|------|
| HTTP API | 8766 | REST API 服务 |
| WebSocket | 8765 | 实时推送服务 |

启动命令：
```bash
cd backend
source .venv/bin/activate
python server.py
```

## 前端 Web (Web Client)

| 服务 | 端口 | 说明 |
|------|------|------|
| 前端开发服务器 | 3000 | Vite 开发服务器 |

启动命令：
```bash
cd web-client
npm run dev
```

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `http://localhost:8766/api/news/latest?limit=10` | 获取最新资讯 |
| GET | `http://localhost:8766/api/news/{id}` | 获取资讯详情 |
| GET | `http://localhost:8766/health` | 健康检查 |
| WS | `ws://localhost:8765` | WebSocket 实时推送 |

## 数据库连接

| 配置 | 值 |
|------|-----|
| Host | 192.168.66.26 |
| Port | 5432 |
| Database | stock_strategy |
| User | vonstars |
| Password | vonstars123.com |
