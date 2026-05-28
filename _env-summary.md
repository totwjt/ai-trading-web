# 环境配置说明（开发 / 生产分离）

> 本文档记录项目的开发环境和生产发布配置，确保两者互不干扰。

---

## 一、架构概览

```
┌── 开发环境（宿主机直接运行）─────────────────────────────┐
│                                                          │
│  Vite Dev Server          python server.py               │
│  :3000 ──── http ────►   :8766                           │
│                                │                         │
│                                ├── 外部 API (127.0.0.1)   │
│                                ├── PostgreSQL (localhost) │
│                                └── Socket.IO 推送         │
│                                                          │
├── 生产环境（Docker Compose）─────────────────────────────┤
│                                                          │
│  Nginx (容器)               FastAPI (容器)                │
│  :80 ──── 反代 ────►        :8766                        │
│   │                            │                         │
│   │ 同域                      ├── 外部 API (host.docker.i)
│   │ /api/*                    ├── PostgreSQL (容器内)     │
│   │ /socket.io/*              └── Socket.IO               │
│   │                            │                         │
│  └── 静态文件 (dist)      PostgreSQL (容器)               │
│                                                     :5432 │
└──────────────────────────────────────────────────────────┘
```

---

## 二、技术栈

### 前端 (web-client)
| 类别 | 技术 | 版本 |
|------|------|------|
| 框架 | Vue 3 (Composition API) | 3.4.21 |
| 构建工具 | Vite | 5.2.10 |
| 语言 | TypeScript | 5.4.5 |
| CSS 框架 | Tailwind CSS | 3.4.4 |
| UI 组件库 | Ant Design Vue | 4.1.2 |
| 状态管理 | Pinia | 2.1.7 |
| 路由 | Vue Router | 4.3.2 |
| HTTP 客户端 | Axios | 1.6.8 |
| WebSocket 客户端 | Socket.IO Client | 4.7.4 |

### 后端 (backend)
| 类别 | 技术 | 版本 |
|------|------|------|
| 语言 | Python | 3.9+ (容器用 3.10-slim) |
| API 框架 | FastAPI | ≥0.109.0 |
| ASGI 服务器 | Uvicorn | ≥0.27.0 |
| ORM | SQLAlchemy | ≥2.0.25 |
| 数据库 | PostgreSQL | 开发: 宿主机 / 生产: Docker 容器 |
| 回测引擎 | Backtrader | ≥1.9.78.123 |

> Redis / Celery：`requirements.txt` 中有依赖但代码未使用，可移除。

---

## 三、开发环境配置（宿主机直接运行）

### 前端
| 文件 | 端口 | 后端地址 | 说明 |
|------|------|---------|------|
| `web-client/.env` | 3000 | `localhost:8766` | 默认配置，本地全栈开发 |
| `web-client/.env.development` | 3000 | `192.168.66.186:8766` | 远程后端开发 |

启动方式：
```bash
cd web-client
npm install
npm run dev             # 加载 .env + .env.development
```

### 后端
| 配置来源 | 默认值 | 说明 |
|---------|--------|------|
| `server.py` 代码中 `os.getenv` | `127.0.0.1:8882/8001` 等 | 代码内联 fallback |
| `common/database.py` | `localhost:5432` (本地 PostgreSQL) | 代码内联 fallback |

启动方式：
```bash
cd backend
source .venv/bin/activate
python server.py        # 启动在 0.0.0.0:8766
```

> 开发环境无需 `.env.deploy` 文件，所有配置由代码内 `os.getenv` 的默认值提供。
> 如需覆盖，在终端 `export VAR=value` 或创建 `backend/.env`（需配合 python-dotenv）。

### 开发环境前提条件
- **PostgreSQL**：宿主机本地运行，数据库 `tushare_sync`
- **外部 API**：策略/交易/用户服务必须在 `127.0.0.1` 对应端口可访问

---

## 四、生产环境配置（Docker Compose）

### 配置文件清单

| 文件 | 用途 |
|------|------|
| `docker-compose.yml` | 服务编排（3 容器） |
| `.env.deploy` | 生产环境变量（**开发和发布共用此配置**） |
| `web-client/Dockerfile` | 前端构建 + Nginx 镜像 |
| `backend/Dockerfile` | 后端 Python 镜像 |
| `deploy/nginx.conf` | Nginx 反代配置 |

### 服务组成 (`docker-compose.yml`)

| 容器 | 镜像 | 端口 | 依赖 |
|------|------|------|------|
| `ai-trading-postgres` | `postgres:15-alpine` | 仅内部 `expose:5432` | — |
| `ai-trading-backend` | `python:3.10-slim` | `8766:8766` | postgres (健康检查) |
| `ai-trading-web` | `nginx:1.27-alpine` | `80:80` | backend |

### 配置参数 (`web-client/Dockerfile` 构建时)

```dockerfile
ARG VITE_API_URL=/       # 构建时传入，生产用 "/"（同域）
ARG VITE_WS_URL=/        # 构建时传入，生产用 "/"（同域）
```

### Nginx 反代规则 (`deploy/nginx.conf`)

| 路径 | 目标 | 说明 |
|------|------|------|
| `/` | `index.html` + 静态文件 | SPA 单页入口 |
| `/api/*` | `http://backend:8766` | API 请求转发 |
| `/socket.io/*` | `http://backend:8766/socket.io/` | WebSocket（含 Upgrade） |
| `/health` | `http://backend:8766/health` | 健康检查 |

---

## 五、生产部署操作流程

### 前置条件
- Docker 24+
- Docker Compose v2+
- 宿主机上已运行外部服务（策略 8882、交易 8881、用户 8001、Trader 8003）
- 宿主机 PostgreSQL：如果用到 `recommendation/db.py` 的 `stock_strategy` 库，需确保 `192.168.66.26:5432` 可达

### 步骤

```bash
# 1. 克隆代码
git clone <repo> && cd ai-trading-web

# 2. 检查 .env.deploy 配置
#    确认外部 API 地址、数据库密码等是否正确
cat .env.deploy

# 3. 构建并启动所有服务
docker compose --env-file .env.deploy up -d --build

# 4. 验证服务
curl -s http://localhost:8766/health          # 后端健康检查
curl -s http://localhost/                      # 前端（应返回 index.html）

# 5. 查看日志
docker compose logs -f backend
docker compose logs -f web
docker compose logs -f postgres
```

### 常用管理命令

```bash
# 查看状态
docker compose ps

# 停止
docker compose down

# 更新（重新构建并启动）
docker compose --env-file .env.deploy up -d --build

# 数据持久化（PostgreSQL）
# 数据存储在 Docker 卷 pgdata 中，down 不会丢失
docker volume inspect ai-trading-web_pgdata

# 如需重置数据库
docker compose down -v && docker compose --env-file .env.deploy up -d --build
```

---

## 六、端口占用总表

| 端口 | 开发环境 | 生产环境（Docker） | 说明 |
|------|---------|-------------------|------|
| 80 | — | `web` 容器 Nginx | 前端入口 |
| 3000 | Vite Dev Server | — | 前端开发服务器 |
| 5432 | 宿主机 PostgreSQL | postgres 容器（仅内部） | 开发连宿主机，生产连容器 |
| 8001 | 外部用户服务 API | 同（宿主机） | 端口不变 |
| 8003 | 外部 Trader API | 同（宿主机） | 端口不变 |
| 8766 | python server.py | `backend` 容器 | 后端统一服务 |
| 8881 | 外部交易 API | 同（宿主机） | Order + Record |
| 8882 | 外部策略 API | 同（宿主机） | 策略信息/操作 |

---

## 七、外部 API 地址配置

| 环境变量 | 开发环境（代码默认值） | 生产环境（.env.deploy） |
|----------|----------------------|------------------------|
| `DATABASE_URL` | `localhost:5432` | `postgres:5432`（Docker 内部） |
| `TRADING_EXTERNAL_API` | `http://127.0.0.1:8882` | `http://host.docker.internal:8882` |
| `TRADING_TRADER_API` | `http://127.0.0.1:8003` | `http://host.docker.internal:8003` |
| `TRADING_ORDER_API` | `http://127.0.0.1:8881` | `http://host.docker.internal:8881` |
| `TRADING_RECORD_API` | `http://127.0.0.1:8881` | `http://host.docker.internal:8881` |
| `USER_API` | `http://127.0.0.1:8001` | `http://host.docker.internal:8001` |

---

## 八、内部模块

| 模块 | 路径 | 说明 |
|------|------|------|
| API 网关 | `backend/gateway/` | 认证、路由 |
| 数据同步 | `backend/data_sync/` | 股票行情数据同步 |
| 策略管理 | `backend/strategy/` | 策略 CRUD |
| 回测服务 | `backend/backtest/` | 回测引擎 |
| 交易服务 | `backend/trading/` | 模拟交易引擎 |
| 智能荐股 | `backend/recommendation/` | AI 选股（直连 192.168.66.26 外部 DB） |
| 公共模块 | `backend/common/` | 数据库、工具函数 |

---

## 九、WebSocket 主题

| 主题 | 说明 |
|------|------|
| `recommendation` | 荐股推送 |
| `zixuan` | 自选股推送 |
| `backtest.*` | 回测结果推送 |
| `trading` | 交易推送 |
| `risk` | 风控推送 |
| `trading-terminal.*` | 交易终端事件 |
| `order.*` | 下单事件 |

---

## 十、关键文件清单

| 文件 | 属于 | 作用 |
|------|------|------|
| `web-client/.env` | 开发 | 前端默认环境变量 |
| `web-client/.env.development` | 开发 | 前端开发环境覆盖 |
| `.env.deploy` | 生产 | 后端生产环境变量（Docker 加载） |
| `docker-compose.yml` | 生产 | Docker 服务编排 |
| `web-client/Dockerfile` | 生产 | 前端多阶段构建 |
| `backend/Dockerfile` | 生产 | 后端 Python 构建 |
| `deploy/nginx.conf` | 生产 | Nginx 反代配置 |
| `backend/common/database.py` | 共用 | 数据库连接（os.getenv 读取） |
| `backend/server.py` | 共用 | 后端入口（os.getenv 读取） |
| `backend/trading/routers.py` | 共用 | 交易路由（os.getenv 读取） |

---

## 十一、待办/注意项

| # | 事项 | 状态 |
|---|------|------|
| 1 | Redis / Celery 在 requirements.txt 但未使用 | 🔧 可清理 |
| 2 | 前端 `market.ts` / `trading.ts` 硬编码 `192.168.66.143:8099` 直连 | 🔧 业务问题暂不处理 |
| 3 | CORS 当前为 `allow_origins=["*"]` | ⏸️ 暂不处理 |
| 4 | HTTPS 缺失 | ⏸️ 暂不处理 |
