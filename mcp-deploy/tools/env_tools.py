"""环境检查工具——读取和验证部署配置。"""

from mcp.server.fastmcp import FastMCP

from config import DeployConfig


def register_env_tools(mcp: FastMCP) -> None:
    """注册环境检查相关的 MCP 工具。"""

    @mcp.tool(
        name="deploy__check_env",
        description="[部署] 检查当前部署环境配置（无需任何参数）。读取 .env.deploy 并验证必要字段是否完整。AI 应在执行任何部署操作前首先调用此工具。",
    )
    def check_deploy_env() -> list[dict]:
        """检查部署环境配置，返回配置摘要和环境状态。"""
        config = DeployConfig()
        summary = config.summarize()
        env_file = config.get_deploy_env_path()

        result = {
            "status": "ok",
            "summary": summary,
            "env_file_exists": env_file is not None,
            "env_file_path": str(env_file) if env_file else None,
        }

        # 检查关键配置是否缺失
        warnings = []
        if not config.harbor_url:
            warnings.append("HARBOR_URL 未配置")
        if not config.ssh_host:
            warnings.append("SSH_HOST 未配置（如在开发环境仅构建，可忽略）")
        if not config.ssh_user:
            warnings.append("SSH_USER 未配置（如在开发环境仅构建，可忽略）")

        if warnings:
            result["status"] = "warning"
            result["warnings"] = warnings

        return [{"type": "text", "text": str(result)}]

    @mcp.tool(
        name="deploy__validate_env",
        description="[部署] 验证 .env.deploy 文件完整性。检查所有必需的部署变量是否已填写（不仅仅是占位符值）。",
    )
    async def validate_deploy_env(
        env_file_path: str = "",
    ) -> list[dict]:
        """验证部署环境变量文件。

        Args:
            env_file_path: .env.deploy 路径（可选，默认自动查找）
        """
        config = DeployConfig()
        env_file = config.get_deploy_env_path() if not env_file_path else env_file_path

        if not env_file or not env_file.exists():
            return [{"type": "text", "text": "错误: 未找到 .env.deploy 文件。请先创建（可从 .env.deploy.example 复制）。"}]

        with open(env_file, "r", encoding="utf-8") as f:
            content = f.read()

        placeholders = ["your-", "your_", "<your", "<YOUR"]
        has_placeholder = any(ph in content for ph in placeholders)

        empty_vars = []
        for line in content.splitlines():
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                key, val = line.split("=", 1)
                if not val or val.strip() == "":
                    empty_vars.append(key.strip())

        required_vars = [
            "HARBOR_URL",
            "HARBOR_PROJECT",
            "POSTGRES_USER",
            "POSTGRES_PASSWORD",
            "POSTGRES_DB",
        ]

        missing = [v for v in required_vars if v not in content]

        result = {
            "file_exists": True,
            "file_path": str(env_file),
            "has_placeholder_values": has_placeholder,
            "empty_variables": empty_vars,
            "missing_required_vars": missing,
            "is_valid": not has_placeholder and not empty_vars and not missing,
        }

        return [{"type": "text", "text": str(result)}]

    @mcp.tool(
        name="deploy__read_env_summary",
        description="[部署] 读取 .env.deploy 的非敏感配置摘要（脱敏密码和敏感字段）。用于了解当前部署目标的 Harbor 地址、SSH 主机等信息。",
    )
    def read_env_summary() -> list[dict]:
        """读取部署环境配置的非敏感摘要。"""
        config = DeployConfig()
        summary = config.summarize()
        return [{"type": "text", "text": str(summary)}]
