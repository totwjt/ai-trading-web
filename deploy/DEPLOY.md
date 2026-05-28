# 部署说明

## 架构

```
开发环境 (有 VPN)                   生产环境 (无 VPN)
    │                                     │
    ├─ docker build                       ├─ docker compose -f docker-compose.prod.yml
    ├─ docker push → Harbor ←─────────────┘
    │                                     │
    └─ Harbor (192.168.66.26:8000)        └─ 从 Harbor pull 预构建镜像
```

## 1. 前置条件

- Docker 24+
- Docker Compose v2+
- Harbor 仓库可访问（开发环境推送，生产环境拉取）
- 生产环境需先通过 `docker login 192.168.66.26:8000` 登录 Harbor

## 2. 构建并推送到 Harbor（在开发环境执行）

```bash
# 构建并推送全部服务（latest 标签）
./deploy/build.sh

# 构建并推送指定版本
./deploy/build.sh v1.2.3

# 只构建不推送
./deploy/build.sh --skip-push

# 只构建某个服务
./deploy/build.sh --service web
./deploy/build.sh --service backend
```

脚本会自动：
1. 构建 `web-client/Dockerfile` → `library/ai-trading-web`
2. 构建 `backend/Dockerfile` → `library/ai-trading-backend`
3. 拉取并推送 `postgres:15-alpine` → `library/postgres:15-alpine`

## 3. 生产部署

```bash
# 1. 登录 Harbor
docker login 192.168.66.26:8000

# 2. 复制环境配置
cp .env.deploy.example .env.deploy
# 编辑 .env.deploy 修改数据库连接等配置

# 3. 启动（使用预构建镜像）
docker compose -f docker-compose.prod.yml --env-file .env.deploy up -d

# 4. 指定版本启动
IMAGE_TAG=v1.2.3 docker compose -f docker-compose.prod.yml --env-file .env.deploy up -d

# 5. 查看日志
docker compose -f docker-compose.prod.yml logs -f
```

## 4. 服务端口

| 服务 | 端口 | 说明 |
|---|---|---|
| 前端 (Nginx) | 80 | Web UI |
| 后端 (API) | 8766 | API 网关 + WebSocket |
| PostgreSQL | 5432 | 仅内部可达，不暴露到宿主机 |

## 5. 验证

```bash
# 前端
curl -sS http://localhost:80/
curl -sS http://localhost:80/recommendation  # SPA 路由验证

# 后端
curl -sS http://localhost:8766/health
```

## 6. 回滚

```bash
# 回滚到上一个版本
IMAGE_TAG=v1.2.2 docker compose -f docker-compose.prod.yml --env-file .env.deploy up -d
```

## 7. 开发环境 vs 生产环境

| | 开发环境 | 生产环境 |
|---|---|---|
| Compose 文件 | `docker-compose.yml` | `docker-compose.prod.yml` |
| 镜像来源 | 本地构建 | Harbor 预构建 |
| Docker Hub | 需要 VPN 访问 | 无需访问 |
| Harbor | 推送镜像 | 拉取镜像 |
