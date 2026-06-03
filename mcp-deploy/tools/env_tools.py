"""环境检查工具——读取和验证部署配置。"""

from pathlib import Path

import dotenv
from mcp.server.fastmcp import FastMCP

from config import DeployConfig

PLACEHOLDER_MARKERS = (
    "your-",
    "your_",
    "<your",
    "<YOUR",
    "placeholder",
    "changeme",
    "change-me",
    "todo",
    "example.com",
)

REQUIRED_VARS = [
    "HARBOR_URL",
    "HARBOR_PROJECT",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_DB",
    "MARKET_DATA_DATABASE_URL",
]


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
        if not config.market_data_database_url:
            warnings.append("MARKET_DATA_DATABASE_URL 未配置，行情/回测数据读取会失败")

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

        env_file = Path(env_file) if env_file else None

        if not env_file or not env_file.exists():
            return [{"type": "text", "text": "错误: 未找到 .env.deploy 文件。请先创建（可从 .env.deploy.example 复制）。"}]

        validation = validate_env_file(env_file)

        result = {
            "file_exists": True,
            "file_path": str(env_file),
            **validation,
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


def validate_env_file(env_file: Path) -> dict:
    """验证部署环境文件，返回不含敏感值的结果。"""
    values = dotenv.dotenv_values(env_file)

    empty_vars = []
    placeholder_vars = []
    for key, value in values.items():
        if key is None:
            continue
        normalized = (value or "").strip()
        if normalized == "":
            empty_vars.append(key)
            continue
        lower = normalized.lower()
        if any(marker.lower() in lower for marker in PLACEHOLDER_MARKERS):
            placeholder_vars.append(key)

    missing = [key for key in REQUIRED_VARS if key not in values]
    invalid_required_vars = sorted(set(missing + empty_vars + placeholder_vars) & set(REQUIRED_VARS))

    return {
        "has_placeholder_values": bool(placeholder_vars),
        "placeholder_variables": placeholder_vars,
        "empty_variables": empty_vars,
        "missing_required_vars": missing,
        "invalid_required_vars": invalid_required_vars,
        "market_data_database_url_configured": (
            "MARKET_DATA_DATABASE_URL" in values
            and bool((values.get("MARKET_DATA_DATABASE_URL") or "").strip())
            and "MARKET_DATA_DATABASE_URL" not in placeholder_vars
        ),
        "is_valid": not invalid_required_vars,
    }
