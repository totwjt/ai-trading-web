"""推送工具——将镜像推送到 Harbor 仓库。"""

import subprocess

from mcp.server.fastmcp import FastMCP

from config import DeployConfig


def register_push_tools(mcp: FastMCP) -> None:
    """注册 Harbor 推送相关的 MCP 工具。"""

    @mcp.tool(
        name="deploy__login_harbor",
        description="[部署] 登录 Harbor 容器仓库。需要先在 .env.deploy 中配置 HARBOR_USERNAME 和 HARBOR_PASSWORD。",
    )
    def login_harbor() -> list[dict]:
        """登录 Harbor 仓库。"""
        config = DeployConfig()
        registry = config.get_harbor_registry()

        if config.harbor_username and config.harbor_password:
            cmd = [
                "docker", "login", config.harbor_url,
                "--username", config.harbor_username,
                "--password-stdin",
            ]
            try:
                result = subprocess.run(
                    cmd,
                    input=config.harbor_password,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode == 0:
                    return [{"type": "text", "text": f"✓ Harbor 登录成功: {config.harbor_url}"}]
                else:
                    return [{"type": "text", "text": f"✗ Harbor 登录失败: {result.stderr}"}]
            except subprocess.TimeoutExpired:
                return [{"type": "text", "text": "Harbor 登录超时"}]
        else:
            return [{
                "type": "text",
                "text": "未配置 HARBOR_USERNAME/HARBOR_PASSWORD。请确认已手动执行 docker login。",
            }]

    @mcp.tool(
        name="deploy__push_images",
        description="[部署] 将本地构建的 Docker 镜像推送到 Harbor。支持推送 web、backend 或 all。",
    )
    def push_images(
        services: str = "all",
        image_tag: str = "",
    ) -> list[dict]:
        """推送镜像到 Harbor。

        Args:
            services: 要推送的服务 "web", "backend", "all"（默认 "all"）
            image_tag: 镜像标签（默认使用 .env.deploy 配置或 "latest"）
        """
        config = DeployConfig()
        tag = image_tag or config.image_tag
        registry = config.get_harbor_registry()

        results = []
        services_list = ["web", "backend"] if services == "all" else [services]

        for service in services_list:
            image_name = f"{registry}/{service}:{tag}"
            try:
                result = subprocess.run(
                    ["docker", "push", image_name],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                if result.returncode == 0:
                    results.append({
                        "service": service,
                        "status": "success",
                        "image": image_name,
                    })
                else:
                    results.append({
                        "service": service,
                        "status": "failed",
                        "image": image_name,
                        "error": result.stderr[-300:] if result.stderr else "推送失败",
                    })
            except subprocess.TimeoutExpired:
                results.append({
                    "service": service,
                    "status": "failed",
                    "image": image_name,
                    "error": "推送超时",
                })

        return [{"type": "text", "text": str(results)}]
