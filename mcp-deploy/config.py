"""mcp-deploy 配置管理——从 .env / .env.deploy 加载环境变量。"""

import os
from pathlib import Path
from typing import Optional

import dotenv


class DeployConfig:
    """部署配置，按优先级：constructor 参数 > .env > .env.deploy > 默认值。"""

    def __init__(self, project_root: Optional[str] = None):
        self._loaded_files: list[str] = []

        # 确定项目根目录
        if project_root:
            self.project_root = Path(project_root).resolve()
        else:
            self.project_root = Path.cwd().resolve()

        self._load_dotenv_files()

        # ----- Harbor -----
        self.harbor_url: str = self._get_env("HARBOR_URL", "192.168.66.26:8000")
        self.harbor_project: str = self._get_env("HARBOR_PROJECT", "wangjiangtao")
        self.harbor_username: Optional[str] = self._get_env("HARBOR_USERNAME", None)
        self.harbor_password: Optional[str] = self._get_env("HARBOR_PASSWORD", None)

        # ----- SSH -----
        self.ssh_host: str = self._get_env("SSH_HOST", "192.168.66.226")
        self.ssh_user: str = self._get_env("SSH_USER", "wangjiangtao")
        self.ssh_port: int = int(self._get_env("SSH_PORT", "22"))
        self.ssh_key_path: Optional[str] = self._get_env("SSH_KEY_PATH", None)
        self.ssh_password: Optional[str] = self._get_env(
            "SSH_PASSWORD", None
        )  # 不推荐，优先密钥

        # ----- Build -----
        self.image_tag: str = self._get_env("IMAGE_TAG", "latest")

        # ----- Runtime data sources -----
        self.market_data_database_url: Optional[str] = self._get_env(
            "MARKET_DATA_DATABASE_URL", None
        )

        # ----- Timeout -----
        self.ssh_timeout: int = int(self._get_env("SSH_TIMEOUT", "30"))
        self.build_timeout: int = int(self._get_env("BUILD_TIMEOUT", "600"))
        self.deploy_timeout: int = int(self._get_env("DEPLOY_TIMEOUT", "300"))

    def _load_dotenv_files(self) -> None:
        """按优先级加载 .env 和 .env.deploy（后者由 gitignore 保护）。"""
        # 1. 尝试 mcp-deploy/.env
        local_env = self.project_root / "mcp-deploy" / ".env"
        if local_env.exists():
            dotenv.load_dotenv(local_env, override=False)
            self._loaded_files.append(str(local_env))

        # 2. 尝试 mcp-deploy/.env.deploy
        local_deploy = self.project_root / "mcp-deploy" / ".env.deploy"
        if local_deploy.exists():
            dotenv.load_dotenv(local_deploy, override=False)
            self._loaded_files.append(str(local_deploy))

        # 3. 尝试项目根目录 .env.deploy（生产配置）
        root_deploy = self.project_root / ".env.deploy"
        if root_deploy.exists():
            dotenv.load_dotenv(root_deploy, override=False)
            self._loaded_files.append(str(root_deploy))

    def _get_env(self, key: str, default: Optional[str]) -> Optional[str]:
        """读取环境变量，优先使用 os.environ（已被 dotenv 填充）。"""
        return os.environ.get(key, default)

    def get_harbor_registry(self) -> str:
        """完整 Harbor 仓库地址：harbor_url/project"""
        return f"{self.harbor_url}/{self.harbor_project}"

    def get_deploy_env_path(self) -> Optional[Path]:
        """返回 .env.deploy 的完整路径（如果存在）。"""
        candidates = [
            self.project_root / ".env.deploy",
            self.project_root / "mcp-deploy" / ".env.deploy",
        ]
        for p in candidates:
            if p.exists():
                return p
        return None

    def summarize(self) -> dict:
        """返回非敏感配置摘要（脱敏密码/token）。"""
        return {
            "project_root": str(self.project_root),
            "loaded_env_files": self._loaded_files,
            "harbor": f"{self.harbor_url}/{self.harbor_project}",
            "ssh": f"{self.ssh_user}@{self.ssh_host}:{self.ssh_port}"
            if self.ssh_host
            else None,
            "image_tag": self.image_tag,
            "market_data_database_url_configured": bool(self.market_data_database_url),
            "timeouts": {
                "ssh": self.ssh_timeout,
                "build": self.build_timeout,
                "deploy": self.deploy_timeout,
            },
        }
