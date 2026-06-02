# 环境变量 IP / 端口映射关系

> 本文档记录开发环境和生产环境的完整地址配置映射关系。

---

## 一、环境拓扑

### ① 开发环境（Mac 本地运行）

```
开发机 192.168.66.186
├── 前端 Vite Dev Server          :3000
├── 后端 FastAPI (server.py)      :8766
├── PostgreSQL (本地)             :5432
│
│  后端代理转发到各上游服务：
│  ├── MARKET_API       → 192.168.66.143:8099   (行情数据)
│  ├── TRADING_EXTERNAL → 192.168.66.143:8000   (策略/交易)
│  ├── TRADING_TRADER   → 192.168.66.155:8003   (Trader)
│  ├── TRADING_ORDER    → 192.168.66.135:8000   (订单)
│  ├── TRADING_RECORD   → 192.168.66.135:8001   (交易记录)
│  └── USER_API         → 192.168.66.198:8001   (用户)
```

### ② 生产环境（Docker Compose 部署在 192.168.66.26）

```
生产宿主机 192.168.66.26
│
├── Docker 内部
│   ├── postgres 容器          :5432     (仅内部)
│   ├── backend 容器           :8766     (暴露端口)
│   └── web (Nginx) 容器       :8880     (暴露端口，80被占用)
│
│  Docker 容器通过 host.docker.internal 访问宿主机上各服务：
│  host.docker.internal:8882   ← 行情数据 + 策略/交易 (合并)
│  host.docker.internal:8003   ← Trader
│  host.docker.internal:8881   ← 订单 + 交易记录 (合并)
│  host.docker.internal:8001   ← 用户
│
│  Nginx 反代规则：
│  /api/*       → backend:8766
│  /socket.io/* → backend:8766/socket.io/
```

---

## 二、前端环境变量

### 开发环境（`web-client/.env` + `web-client/.env.development`）

| 变量 | 值 | 说明 |
|---|---|---|
| `VITE_API_URL` | `http://192.168.66.186:8766` | 后端地址（开发机自身） |
| `VITE_WS_HOST` | `192.168.66.186` | WebSocket 主机 |
| `VITE_WS_PORT` | `8766` | WebSocket 端口 |
| `VITE_WS_PATH` | `/pubsub`（代码 fallback） | WebSocket 路径 |

### 生产环境（`web-client/.env.production` + Dockerfile build args）

| 变量 | 值 | 说明 |
|---|---|---|
| `VITE_API_URL` | `/` | 同域，Nginx 反代 |
| `VITE_WS_URL` | `/` | 同域，Nginx 反代 |

---

## 三、后端环境变量

### 开发环境

来源：`backend/.env`（python-dotenv 加载）覆盖 `os.getenv` 代码默认值

| 变量 | 实际值（env 文件） | 代码 fallback 默认值 |
|---|---|---|
| `MARKET_API` | `http://192.168.66.143:8099` | `http://127.0.0.1:8882` |
| `TRADING_EXTERNAL_API` | `http://192.168.66.143:8000` | `http://127.0.0.1:8882` |
| `TRADING_TRADER_API` | `http://192.168.66.155:8003` | `http://127.0.0.1:8003` |
| `TRADING_ORDER_API` | `http://192.168.66.135:8000` | `http://127.0.0.1:8881` |
| `TRADING_RECORD_API` | `http://192.168.66.135:8001` | `http://127.0.0.1:8881` |
| `USER_API` | `http://192.168.66.198:8001` | `http://127.0.0.1:8001` |
| `DATABASE_URL` | 未在 env 中设置 | `postgresql+asyncpg://wangjiangtao:123456@localhost:5432/tushare_sync` |

### 生产环境

来源：`.env.deploy`（Docker Compose `env_file` 注入容器）

| 变量 | 实际值 | 对应宿主机 |
|---|---|---|
| `MARKET_API` | `http://host.docker.internal:8882` | `192.168.66.26:8882` |
| `TRADING_EXTERNAL_API` | `http://host.docker.internal:8882` | `192.168.66.26:8882` |
| `TRADING_TRADER_API` | `http://host.docker.internal:8003` | `192.168.66.26:8003` |
| `TRADING_ORDER_API` | `http://host.docker.internal:8881` | `192.168.66.26:8881` |
| `TRADING_RECORD_API` | `http://host.docker.internal:8881` | `192.168.66.26:8881` |
| `USER_API` | `http://host.docker.internal:8001` | `192.168.66.26:8001` |
| `DATABASE_URL` | `postgresql+asyncpg://wangjiangtao:123456@postgres:5432/tushare_sync` | Docker 内部 postgres 容器 |
| `MARKET_DATA_DATABASE_URL` | `postgresql+asyncpg://<user>:<password>@host.docker.internal:5432/z_strategies` | 宿主机行情库，仅用于 `stock_daily` / `stock_adj_factor` / `index_daily` / `stock_basic` |

---

## 四、IP 与端口映射总表

| 服务 | 开发环境 | 生产环境（Docker → 宿主机 192.168.66.26） |
|---|---|---|
| 前端开发服务器 | `192.168.66.186:3000` | — |
| 后端 FastAPI | `192.168.66.186:8766` | Docker `backend:8766` → 暴露 `:8766` |
| Nginx 入口 | — | Docker `web:80` → 暴露 `:8880`（80被占用） |
| 主业务 PostgreSQL | 宿主机 `localhost:5432` | Docker 内部 `postgres:5432` |
| 行情 PostgreSQL | — | 宿主机 `host.docker.internal:5432/z_strategies` |
| **行情数据 (MARKET)** | `192.168.66.143:8099` | `192.168.66.26:8882` |
| **策略/交易外部 (EXTERNAL)** | `192.168.66.143:8000` | `192.168.66.26:8882`（合并到 8882） |
| **Trader** | `192.168.66.155:8003` | `192.168.66.26:8003` |
| **订单 (ORDER)** | `192.168.66.135:8000` | `192.168.66.26:8881` |
| **交易记录 (RECORD)** | `192.168.66.135:8001` | `192.168.66.26:8881`（合并到 8881） |
| **用户 (USER)** | `192.168.66.198:8001` | `192.168.66.26:8001` |

---

## 五、关键差异总结

### IP 差异
| 服务 | 开发 IP | 生产 IP | 备注 |
|---|---|---|---|
| 所有上游服务 | 多个分散 IP | 统一 `192.168.66.26` | 生产环境将服务集中部署到一台宿主机 |

### 端口差异
| 变量 | 开发端口 | 生产端口 | 说明 |
|---|---|---|---|
| `MARKET_API` | `8099` | `8882` | 开发和生产端口不同 |
| `TRADING_EXTERNAL_API` | `8000` | `8882` | 生产合并到 8882 |
| `TRADING_ORDER_API` | `8000` | `8881` | 端口不同 |
| `TRADING_RECORD_API` | `8001` | `8881` | 生产与 ORDER 合并到 8881 |

### 访问方式差异
| 项目 | 开发环境 | 生产环境 |
|---|---|---|
| 前端→后端 | 跨域 HTTP → `192.168.66.186:8766` | 同域 Nginx 反代 |
| 后端→上游 | 直连各机器 IP | via `host.docker.internal` |
| 主业务数据库 | `localhost:5432`（本地） | `postgres:5432`（Docker 内部） |
| 行情数据库 | `MARKET_DATA_DATABASE_URL` | `host.docker.internal:5432/z_strategies` |

---

## 六、配置来源文件

| 文件 | 属于 | 作用 |
|---|---|---|
| `web-client/.env` | 开发 | 前端默认变量 |
| `web-client/.env.development` | 开发 | 前端开发环境覆盖 |
| `web-client/.env.production` | 生产 | 前端生产构建变量 |
| `backend/.env` | 开发 | 后端开发环境上游地址 |
| `.env.deploy` | 生产 | Docker Compose 环境变量 |
| `docker-compose.yml` | 生产 | 服务编排，引用 `.env.deploy` |
| `web-client/Dockerfile` | 生产 | 构建时注入 `VITE_API_URL=/` `VITE_WS_URL=/` |

---

> 更新记录：2026-05-28 — 根据实际环境配置整理
