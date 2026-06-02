#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# 构建 & 推送脚本 —— 开发环境构建，推送到 Harbor
# 用法:
#   ./deploy/build.sh                    # 构建并推送全部 (latest 标签)
#   ./deploy/build.sh v1.2.3            # 构建并推送指定版本标签
#   ./deploy/build.sh --skip-push       # 仅构建，不推送
#   ./deploy/build.sh --service web     # 只构建 web 服务
# ============================================================

HARBOR_URL="${HARBOR_URL:-192.168.66.26:8000}"
HARBOR_PROJECT="${HARBOR_PROJECT:-library}"
IMAGE_TAG="${1:-latest}"
SKIP_PUSH=false
SERVICE_FILTER=""

for arg in "$@"; do
  case "$arg" in
    --skip-push) SKIP_PUSH=true ;;
    --service=*) SERVICE_FILTER="${arg#--service=}" ;;
    --service) SERVICE_FILTER="$2"; shift ;;
  esac
done

# 如果不是语义化版本标签，当作 latest
if [[ "$IMAGE_TAG" =~ ^-- ]]; then
  IMAGE_TAG="latest"
fi

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$SCRIPT_DIR"

# 加载 .env.deploy（gitignored，含 Harbor 密码等敏感信息）
if [ -f .env.deploy ]; then
  set -a
  # shellcheck source=/dev/null
  source .env.deploy
  set +a
fi

echo "========================================"
echo " Harbor: $HARBOR_URL/$HARBOR_PROJECT"
echo " Tag:    $IMAGE_TAG"
echo " Skip push: $SKIP_PUSH"
echo " Filter: ${SERVICE_FILTER:-全部}"
echo "========================================"

# 登录 Harbor（优先使用 .env.deploy 中的 HARBOR_USERNAME / HARBOR_PASSWORD）
if [ "$SKIP_PUSH" = false ]; then
  if docker inspect "$HARBOR_URL" &>/dev/null; then
    echo "Harbor 已登录"
  elif [ -n "${HARBOR_USERNAME:-}" ] && [ -n "${HARBOR_PASSWORD:-}" ]; then
    echo "$HARBOR_PASSWORD" | docker login "$HARBOR_URL" --username "$HARBOR_USERNAME" --password-stdin
  else
    docker login "$HARBOR_URL"
  fi
fi

# ---------- 1. Web 前端 ----------
if [ -z "$SERVICE_FILTER" ] || [ "$SERVICE_FILTER" = "web" ]; then
  echo ""
  echo ">>> [web] 构建前端镜像 ..."
  docker build \
    -f web-client/Dockerfile \
    -t "$HARBOR_URL/$HARBOR_PROJECT/web:$IMAGE_TAG" \
    --build-arg VITE_API_URL=/ \
    --build-arg VITE_WS_URL=/ \
    .

  # 额外打 latest 标签
  if [ "$IMAGE_TAG" != "latest" ]; then
    docker tag "$HARBOR_URL/$HARBOR_PROJECT/web:$IMAGE_TAG" \
           "$HARBOR_URL/$HARBOR_PROJECT/web:latest"
  fi

  if [ "$SKIP_PUSH" = false ]; then
    docker push "$HARBOR_URL/$HARBOR_PROJECT/web:$IMAGE_TAG"
    echo "  ✓ web 已推送"
  fi
fi

# ---------- 2. Backend ----------
if [ -z "$SERVICE_FILTER" ] || [ "$SERVICE_FILTER" = "backend" ]; then
  echo ""
  echo ">>> [backend] 构建后端镜像 ..."
  docker build \
    -f backend/Dockerfile \
    -t "$HARBOR_URL/$HARBOR_PROJECT/backend:$IMAGE_TAG" \
    ./backend

  if [ "$IMAGE_TAG" != "latest" ]; then
    docker tag "$HARBOR_URL/$HARBOR_PROJECT/backend:$IMAGE_TAG" \
           "$HARBOR_URL/$HARBOR_PROJECT/backend:latest"
  fi

  if [ "$SKIP_PUSH" = false ]; then
    docker push "$HARBOR_URL/$HARBOR_PROJECT/backend:$IMAGE_TAG"
    echo "  ✓ backend 已推送"
  fi
fi

# ---------- 3. PostgreSQL（基础镜像，推送到 Harbor 避免生产拉 Docker Hub）----------
if [ -z "$SERVICE_FILTER" ] || [ "$SERVICE_FILTER" = "postgres" ]; then
  echo ""
  echo ">>> [postgres] 拉取并推送 postgres:15-alpine ..."
  docker pull postgres:15-alpine
  docker tag postgres:15-alpine "$HARBOR_URL/$HARBOR_PROJECT/postgres:15-alpine"

  if [ "$SKIP_PUSH" = false ]; then
    docker push "$HARBOR_URL/$HARBOR_PROJECT/postgres:15-alpine"
    echo "  ✓ postgres 已推送"
  fi
fi

echo ""
echo "========================================"
echo " 完成！"
echo "========================================"
