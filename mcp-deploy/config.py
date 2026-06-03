"""mcp-deploy 配置管理——从 .env / .env.deploy 加载环境变量。"""

import os
import shutil
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
            self.project_root = Path(self._get_env("PROJECT_ROOT", os.getcwd())).resolve()

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
        self.remote_deploy_dir: str = self._get_env("REMOTE_DEPLOY_DIR", "/root") or "/root"

        # ----- Build -----
        self.image_tag: str = self._get_env("IMAGE_TAG", "latest")
        self.build_platform: str = self._get_env("BUILD_PLATFORM", "linux/amd64") or "linux/amd64"

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

    def get_remote_compose_file(self) -> str:
        """生产服务器 docker compose 文件路径。"""
        return f"{self.remote_deploy_dir.rstrip('/')}/docker-compose.prod.yml"

    def get_remote_env_file(self) -> str:
        """生产服务器 .env.deploy 文件路径。"""
        return f"{self.remote_deploy_dir.rstrip('/')}/.env.deploy"

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

    def has_valid_ssh_key(self) -> bool:
        """是否配置了存在的 SSH key。"""
        if not self.ssh_key_path:
            return False
        return Path(self.ssh_key_path).expanduser().exists()

    def ssh_auth_mode(self) -> str:
        """返回当前 SSH 认证模式，不暴露凭据。"""
        if self.has_valid_ssh_key():
            return "key"
        if self.ssh_password:
            return "password"
        return "missing"

    def sshpass_available(self) -> bool:
        """密码 SSH 所需的 sshpass 是否可用。"""
        return shutil.which("sshpass") is not None

    def summarize(self) -> dict:
        """返回非敏感配置摘要（脱敏密码/token）。"""
        return {
            "project_root": str(self.project_root),
            "loaded_env_files": self._loaded_files,
            "harbor": f"{self.harbor_url}/{self.harbor_project}",
            "ssh": f"{self.ssh_user}@{self.ssh_host}:{self.ssh_port}"
            if self.ssh_host
            else None,
            "ssh_auth_mode": self.ssh_auth_mode(),
            "sshpass_available": self.sshpass_available()
            if self.ssh_auth_mode() == "password"
            else None,
            "remote_deploy_dir": self.remote_deploy_dir,
            "remote_compose_file": self.get_remote_compose_file(),
            "remote_env_file": self.get_remote_env_file(),
            "image_tag": self.image_tag,
            "build_platform": self.build_platform,
            "market_data_database_url_configured": bool(self.market_data_database_url),
            "timeouts": {
                "ssh": self.ssh_timeout,
                "build": self.build_timeout,
                "deploy": self.deploy_timeout,
            },
        }
