#!/usr/bin/env python3
"""
mcp-deploy: AI 生产部署 MCP 服务器。

启动方式:
  cd mcp-deploy && pip install -r requirements.txt && python server.py

MCP 配置集成到 opencode:
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
"""

import sys
from pathlib import Path

# 确保 mcp-deploy 目录在 Python 路径中（使 from config / from tools 导入可用）
MCP_DEPLOY_DIR = Path(__file__).parent.resolve()
if str(MCP_DEPLOY_DIR) not in sys.path:
    sys.path.insert(0, str(MCP_DEPLOY_DIR))

from mcp.server.fastmcp import FastMCP

from tools.env_tools import register_env_tools
from tools.build_tools import register_build_tools
from tools.push_tools import register_push_tools
from tools.ssh_tools import register_ssh_tools
from tools.deploy_tools import register_deploy_tools
from tools.verify_tools import register_verify_tools

# 创建 MCP 服务器实例
mcp = FastMCP(
    "mcp-deploy",
    description="AI 生产部署 MCP 服务器——安全地构建、推送、部署和验证生产环境",
)

# 注册所有工具模块
register_env_tools(mcp)       # 环境检查
register_build_tools(mcp)     # Docker 构建
register_push_tools(mcp)      # Harbor 推送
register_ssh_tools(mcp)       # SSH 操作（带安全守卫）
register_deploy_tools(mcp)    # 部署编排
register_verify_tools(mcp)    # 验证与回滚


def main():
    """启动 MCP 服务器。"""
    mcp.run()


if __name__ == "__main__":
    main()
