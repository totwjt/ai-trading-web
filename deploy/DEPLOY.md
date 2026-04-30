# 发布说明（Docker Compose）

## 1. 前置条件

- Docker 24+
- Docker Compose v2+
- 可访问后端依赖（PostgreSQL、外部行情/交易 API）

## 2. 配置

1. 在项目根目录复制环境文件：

```bash
cp .env.deploy.example .env.deploy
```

2. 按实际环境修改 `.env.deploy`：

- `DATABASE_URL`
- `TRADING_EXTERNAL_API`
- `TRADING_TRADER_API`
- `TRADING_ORDER_API`
- `TRADING_RECORD_API`
- `USER_API`

默认推荐保持：

- `VITE_API_URL=/`
- `VITE_WS_URL=/`

## 3. 构建与启动

在项目根目录执行：

```bash
docker compose --env-file .env.deploy up -d --build
```

服务端口：

- 前端：http://localhost:3000
- 后端：http://localhost:8766

## 4. 验证

```bash
curl -sS http://localhost:3000/health
curl -sS http://localhost:8766/health
```

打开浏览器验证：

- `http://localhost:3000/`
- `http://localhost:3000/trading-terminal`

## 5. 停止与重启

```bash
docker compose down
docker compose --env-file .env.deploy up -d
```

## 6. 回滚

建议用镜像 tag 管理版本。回滚时把 `docker-compose.yml` 中镜像/构建版本切回上一个可用版本，然后：

```bash
docker compose down
docker compose up -d
```
