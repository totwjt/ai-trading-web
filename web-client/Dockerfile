FROM 192.168.66.26:8000/wangjiangtao/node:22-alpine AS builder

ARG TARGETPLATFORM=linux/arm64
WORKDIR /app

COPY web-client/package*.json ./
RUN ROLLUP_PKG=$(case "$TARGETPLATFORM" in \
      linux/amd64) echo "rollup-linux-x64-musl" ;; \
      linux/arm64) echo "rollup-linux-arm64-musl" ;; \
    esac) \
 && npm ci \
 && ROLLUP_VER=$(node -p "require('rollup/package.json').version") \
 && npm pack "@rollup/$ROLLUP_PKG@$ROLLUP_VER" --pack-destination /tmp \
 && mkdir -p "/app/node_modules/@rollup/$ROLLUP_PKG" \
 && tar -xzf "/tmp/rollup-$ROLLUP_PKG-$ROLLUP_VER.tgz" -C /tmp \
 && cp -r /tmp/package/* "/app/node_modules/@rollup/$ROLLUP_PKG/" \
 && rm -rf /tmp/package /tmp/*.tgz

COPY web-client/ .

ARG VITE_API_URL=/
ARG VITE_WS_URL=/
ENV VITE_API_URL=${VITE_API_URL}
ENV VITE_WS_URL=${VITE_WS_URL}

RUN npm run build

FROM 192.168.66.26:8000/wangjiangtao/nginx:1.27-alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
