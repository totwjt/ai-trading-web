# mcp-deploy

AI 生产部署 MCP 服务器。引导 AI 安全、规范地完成生产环境发布。

## 设计原则

1. **原子操作**：每个工具只做一件事，AI 必须逐步调用
2. **安全第一**：所有 SSH 命令经安全检查，禁止命令直接拦截
3. **拒绝自动覆盖**：冲突、高风险操作一律要求用户确认
4. **规范流程**：引导 AI 按标准部署流程执行（检查→构建→推送→SSH→部署→验证）

## 安全规则

mcp-deploy 强制执行以下安全约束：

| 级别 | 行为 | 处理方式 |
|------|------|----------|
| 🚫 禁止 | rm -rf /、uninstall、curl \| bash | 直接拒绝 |
| ⚠️ 高风险 | docker stop/rm、端口冲突、文件覆盖 | 必须用户确认 |
| ✅ 只读 | docker ps、curl、ls、whoami | 自动放行 |

## 工具清单

| 工具 | 用途 | 安全等级 |
|------|------|----------|
| `deploy__check_env` | 检查部署环境配置 | ✅ 只读 |
| `deploy__validate_env` | 验证 .env.deploy 完整性 | ✅ 只读 |
| `deploy__read_env_summary` | 读取非敏感配置摘要 | ✅ 只读 |
| `deploy__build_status` | 检查本地 Docker 环境 | ✅ 只读 |
| `deploy__build_images` | 构建 Docker 镜像 | ✅ 本地 |
| `deploy__login_harbor` | 登录 Harbor 仓库 | ✅ 本地 |
| `deploy__push_images` | 推送镜像到 Harbor | ✅ 本地 |
| `deploy__ssh_test_connection` | 测试 SSH 连接 | ✅ 只读 |
| `deploy__ssh_check_docker` | 检查生产 Docker 状态 | ✅ 只读 |
| `deploy__ssh_check_conflicts` | 检查容器/端口冲突 | ✅ 只读 |
| `deploy__ssh_execute` | 执行 SSH 命令 | ⚠️ 安全检查 |
| `deploy__ssh_pull_images` | 生产拉取镜像 | ⚠️ 高风险 |
| `deploy__ssh_compose_up` | 生产启动服务 | ⚠️ 需确认 |
| `deploy__ssh_compose_down` | 生产停止服务 | ⚠️ 需确认 |
| `deploy__verify_services` | 验证服务状态 | ✅ 只读 |
| `deploy__verify_health` | 验证健康检查 | ✅ 只读 |
| `deploy__verify_logs` | 查看服务日志 | ✅ 只读 |
| `deploy__verify_rollback` | 回滚版本 | ⚠️ 需确认 |
| `deploy__get_deploy_guide` | 获取部署流程指南 | ✅ 只读 |
| `deploy__whats_next` | 获取下一步建议 | ✅ 只读 |

## 标准部署流程

AI 应引导用户按以下步骤执行：

```
1.  deploy__check_env          → 检查本地配置
2.  deploy__validate_env       → 验证 .env.deploy 
3.  deploy__build_status       → 检查 Docker 环境
4.  deploy__build_images       → 构建镜像
5.  deploy__push_images        → 推送 Harbor
6.  deploy__ssh_test_connection → 测试 SSH
7.  deploy__ssh_check_docker   → 检查生产状态
8.  deploy__ssh_check_conflicts → 冲突检测
9.  deploy__ssh_pull_images    → 生产拉取
10. deploy__ssh_compose_up     → 启动服务
11. deploy__verify_services    → 验证状态
12. deploy__verify_health      → 健康检查
```

## 启动方式

```bash
# 安装依赖
cd mcp-deploy && pip install -r requirements.txt

# 启动 MCP 服务器（stdio 模式）
python mcp-deploy/server.py

# 设置项目根目录环境变量
export PROJECT_ROOT=/path/to/ai-trading-web
```

## 集成到 opencode

在 opencode.json 或 MCP 配置中添加：

```json
{
  "mcpServers": {
    "mcp-deploy": {
      "command": "python",
      "args": ["/absolute/path/to/mcp-deploy/server.py"],
      "env": {
        "PROJECT_ROOT": "/absolute/path/to/ai-trading-web"
      }
    }
  }
}
```

## 配置优先级

`constructor 参数 > mcp-deploy/.env > 项目 .env.deploy > 默认值`
