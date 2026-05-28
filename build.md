# Docker Hub 国内超时 + Harbor 私有仓库完整流程

## 目标

实现：

text 开发机/CI
     ↓
构建 Docker 镜像
     ↓
推送 Harbor
     ↓
生产服务器只从 Harbor 拉取

最终：

text 生产环境不依赖 Docker Hub

---

# 一、问题原因

构建时报错：

text ERROR: failed to solve: DeadlineExceeded: node:22-alpine: failed to resolve source metadata

原因：

dockerfile FROM node:22-alpine FROM nginx:1.27-alpine

Docker 默认访问：

text docker.io/library/node docker.io/library/nginx

国内网络容易超时。

---

# 二、临时解决方案（推荐先用）

使用 DaoCloud 镜像加速。

## Dockerfile 修改

原始：

dockerfile FROM node:22-alpine AS builder

改成：

dockerfile FROM m.daocloud.io/docker.io/library/node:22-alpine AS builder

第二阶段：

dockerfile FROM m.daocloud.io/docker.io/library/nginx:1.27-alpine

完整示例：

dockerfile FROM m.daocloud.io/docker.io/library/node:22-alpine AS builder  WORKDIR /app  COPY package*.json ./  RUN npm install  COPY . .  RUN npm run build   FROM m.daocloud.io/docker.io/library/nginx:1.27-alpine  COPY --from=builder /app/dist /usr/share/nginx/html  EXPOSE 80  CMD ["nginx", "-g", "daemon off;"]

---

# 三、Docker Desktop 配置镜像加速

Docker Desktop：

text Settings   -> Docker Engine

加入：

json {   "registry-mirrors": [     "https://docker.m.daocloud.io"   ] }

然后：

text Apply & Restart

验证：

bash docker info

查看：

text Registry Mirrors

---

# 四、构建业务镜像

## 构建

bash docker build -t web:latest .

## 查看镜像

bash docker images

---

# 五、登录 Harbor

Harbor 地址：

text http://192.168.66.26:8000

登录：

bash docker login 192.168.66.26:8000

---

# 六、推送业务镜像到 Harbor

项目：

text wangjiangtao

## 打标签

bash docker tag web:latest 192.168.66.26:8000/wangjiangtao/web:latest

## 推送

bash docker push 192.168.66.26:8000/wangjiangtao/web:latest

---

# 七、推送基础镜像到 Harbor（推荐）

目标：

text 以后完全不依赖 Docker Hub

## 拉取基础镜像

bash docker pull m.daocloud.io/docker.io/library/node:22-alpine  docker pull m.daocloud.io/docker.io/library/nginx:1.27-alpine

---

## 打 Harbor 标签

bash docker tag \ m.daocloud.io/docker.io/library/node:22-alpine \ 192.168.66.26:8000/wangjiangtao/node:22-alpine

bash docker tag \ m.daocloud.io/docker.io/library/nginx:1.27-alpine \ 192.168.66.26:8000/wangjiangtao/nginx:1.27-alpine

---

## 推送基础镜像

bash docker push 192.168.66.26:8000/wangjiangtao/node:22-alpine

bash docker push 192.168.66.26:8000/wangjiangtao/nginx:1.27-alpine

---

# 八、最终 Dockerfile（推荐）

dockerfile FROM 192.168.66.26:8000/wangjiangtao/node:22-alpine AS builder  WORKDIR /app  COPY package*.json ./  RUN npm install  COPY . .  RUN npm run build   FROM 192.168.66.26:8000/wangjiangtao/nginx:1.27-alpine  COPY --from=builder /app/dist /usr/share/nginx/html  EXPOSE 80  CMD ["nginx", "-g", "daemon off;"]

---

# 九、重新构建

bash docker build -t web:latest .

此时：

text 不会访问 Docker Hub 只访问 Harbor

---

# 十、生产服务器部署

生产服务器：

## 登录 Harbor

bash docker login 192.168.66.26:8000

## 拉取镜像

bash docker pull 192.168.66.26:8000/wangjiangtao/web:latest

## 启动

bash docker run -d \   --name web \   -p 80:80 \   192.168.66.26:8000/wangjiangtao/web:latest

---

# 十一、HTTP Harbor 问题

如果 Harbor 是 HTTP：

text http://192.168.66.26:8000

Docker 默认会报：

text server gave HTTP response to HTTPS client

需要配置：

## Linux

编辑：

bash /etc/docker/daemon.json

加入：

json {   "insecure-registries": [     "192.168.66.26:8000"   ] }

重启：

bash sudo systemctl restart docker

---

## Docker Desktop

text Settings   -> Docker Engine

加入：

json {   "insecure-registries": [     "192.168.66.26:8000"   ] }

然后：

text Apply & Restart

---

# 十二、推荐最终结构

text Harbor └── wangjiangtao     ├── web:latest     ├── node:22-alpine     └── nginx:1.27-alpine

后续：

text 所有镜像： - 全部来源 Harbor - CI 不访问 Docker Hub - 生产不访问 Docker Hub

---