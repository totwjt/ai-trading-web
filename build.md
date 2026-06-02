# Docker Hub 国内超时 + Harbor 私有仓库完整流程

## 目标

实现：

```
开发机/CI
     ↓
构建 Docker 镜像（前端 web + 后端 backend）
     ↓
推送 Harbor
     ↓
生产服务器只从 Harbor 拉取
```

最终：

```
生产环境不依赖 Docker Hub
```

---

# 一、问题原因

构建时报错：

```
ERROR: failed to solve: DeadlineExceeded: node:22-alpine: failed to resolve source metadata
```

涉及的基础镜像：
- 前端：`node:22-alpine`、`nginx:1.27-alpine`
- 后端：`python:3.10-slim`

Docker 默认访问 `docker.io`，国内网络容易超时。

---

# 二、临时解决方案（推荐先用）

使用 DaoCloud 镜像加速。

## Dockerfile 修改

### 前端 `web-client/Dockerfile`

原始：

```dockerfile
FROM node:22-alpine AS builder
FROM nginx:1.27-alpine
```

改成：

```dockerfile
FROM m.daocloud.io/docker.io/library/node:22-alpine AS builder
FROM m.daocloud.io/docker.io/library/nginx:1.27-alpine
```

### 后端 `backend/Dockerfile`

原始：

```dockerfile
FROM python:3.10-slim
```

改成：

```dockerfile
FROM m.daocloud.io/docker.io/library/python:3.10-slim
```

---

# 三、Docker Desktop 配置镜像加速

Docker Desktop：

```
Settings -> Docker Engine
```

加入：

```json
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io"
  ]
}
```

然后 `Apply & Restart`。

验证：

```bash
docker info
# 查看 Registry Mirrors
```

---

# 四、构建业务镜像

## 构建

```bash
# 构建前端
docker build -f web-client/Dockerfile -t web:latest .

# 构建后端
docker build -f backend/Dockerfile -t backend:latest ./backend
```

## 查看镜像

```bash
docker images
```

---

# 五、登录 Harbor

Harbor 地址：

```
http://192.168.66.26:8000
```

登录：

```bash
docker login 192.168.66.26:8000
```

---

# 六、推送业务镜像到 Harbor

项目：`wangjiangtao`

## 前端

```bash
docker tag web:latest 192.168.66.26:8000/wangjiangtao/web:latest
docker push 192.168.66.26:8000/wangjiangtao/web:latest
```

## 后端

```bash
docker tag backend:latest 192.168.66.26:8000/wangjiangtao/backend:latest
docker push 192.168.66.26:8000/wangjiangtao/backend:latest
```

---

# 七、推送基础镜像到 Harbor（推荐）

目标：以后完全不依赖 Docker Hub。

## 拉取基础镜像

```bash
# 前端
docker pull m.daocloud.io/docker.io/library/node:22-alpine
docker pull m.daocloud.io/docker.io/library/nginx:1.27-alpine

# 后端
docker pull m.daocloud.io/docker.io/library/python:3.10-slim
```

## 打 Harbor 标签

```bash
# 前端
docker tag m.daocloud.io/docker.io/library/node:22-alpine 192.168.66.26:8000/wangjiangtao/node:22-alpine
docker tag m.daocloud.io/docker.io/library/nginx:1.27-alpine 192.168.66.26:8000/wangjiangtao/nginx:1.27-alpine

# 后端
docker tag m.daocloud.io/docker.io/library/python:3.10-slim 192.168.66.26:8000/wangjiangtao/python:3.10-slim
```

## 推送基础镜像

```bash
# 前端
docker push 192.168.66.26:8000/wangjiangtao/node:22-alpine
docker push 192.168.66.26:8000/wangjiangtao/nginx:1.27-alpine

# 后端
docker push 192.168.66.26:8000/wangjiangtao/python:3.10-slim
```

---

# 八、最终 Dockerfile（推荐）

基础镜像全部从 Harbor 拉取，完全不依赖 Docker Hub。

## 前端 `web-client/Dockerfile`

```dockerfile
FROM 192.168.66.26:8000/wangjiangtao/node:22-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM 192.168.66.26:8000/wangjiangtao/nginx:1.27-alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## 后端 `backend/Dockerfile`

```dockerfile
FROM 192.168.66.26:8000/wangjiangtao/python:3.10-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8766
CMD ["python", "server.py"]
```

---

# 九、重新构建

```bash
# 构建前端
docker build -f web-client/Dockerfile -t web:latest .

# 构建后端
docker build -f backend/Dockerfile -t backend:latest ./backend
```

此时不会访问 Docker Hub，只访问 Harbor。

---

# 十、生产服务器部署

## 登录 Harbor

```bash
docker login 192.168.66.26:8000
```

## 拉取镜像

```bash
docker pull 192.168.66.26:8000/wangjiangtao/web:latest
docker pull 192.168.66.26:8000/wangjiangtao/backend:latest
```

## 启动

### 手动启动

```bash
# 前端
docker run -d --name web -p 80:80 192.168.66.26:8000/wangjiangtao/web:latest

# 后端
docker run -d --name backend -p 8766:8766 \
  --env-file .env.deploy \
  192.168.66.26:8000/wangjiangtao/backend:latest
```

### 或使用 Docker Compose（推荐）

```bash
docker compose -f docker-compose.prod.yml --env-file .env.deploy up -d
```

---

# 十一、HTTP Harbor 问题

如果 Harbor 是 HTTP：

```
http://192.168.66.26:8000
```

Docker 默认会报：

```
server gave HTTP response to HTTPS client
```

## Linux

编辑 `/etc/docker/daemon.json`：

```json
{
  "insecure-registries": [
    "192.168.66.26:8000"
  ]
}
```

重启：

```bash
sudo systemctl restart docker
```

## Docker Desktop

```
Settings -> Docker Engine
```

加入：

```json
{
  "insecure-registries": [
    "192.168.66.26:8000"
  ]
}
```

然后 `Apply & Restart`。

---

# 十二、推荐最终 Harbor 结构

```
Harbor (192.168.66.26:8000)
└── wangjiangtao
    ├── web:latest              # 前端业务镜像
    ├── backend:latest           # 后端业务镜像
    ├── node:22-alpine           # 前端 Node 基础镜像
    ├── nginx:1.27-alpine        # 前端 Nginx 基础镜像
    └── python:3.10-slim         # 后端 Python 基础镜像
```

后续：
- 所有镜像全部来源 Harbor
- CI 不访问 Docker Hub
- 生产不访问 Docker Hub
- 新增服务按同样模式：基础镜像推到 Harbor → Dockerfile 指向 Harbor

---

# 附录：一键构建脚本

```bash
# 构建并推送全部（latest）
./deploy/build.sh

# 构建并推送指定版本
./deploy/build.sh v1.2.3

# 只构建某个服务
./deploy/build.sh --service web
./deploy/build.sh --service backend
./deploy/build.sh --service postgres

# 仅构建不推送
./deploy/build.sh --skip-push
```
