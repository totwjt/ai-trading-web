"""构建工具——本地 Docker 镜像构建。"""

import subprocess
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from config import DeployConfig


def register_build_tools(mcp: FastMCP) -> None:
    """注册构建相关的 MCP 工具。"""

    @mcp.tool(
        name="deploy__build_images",
        description="[部署] 构建 Docker 镜像。可选择构建 web 前端、backend 后端或 all（全部）。执行构建前建议先调用 deploy__check_env 确认配置。",
    )
    def build_images(
        services: str = "all",
        image_tag: str = "",
        skip_push: bool = False,
    ) -> list[dict]:
        """构建 Docker 镜像。

        Args:
            services: 要构建的服务，可选 "web", "backend", "all"（默认 "all"）
            image_tag: 镜像标签（默认使用 .env.deploy 中的配置或 "latest"）
            skip_push: 仅构建不推送（默认 false，仅标记此参数，推送需调用 deploy__push_images）
        """
        config = DeployConfig()
        tag = image_tag or config.image_tag
        registry = config.get_harbor_registry()
        project_root = config.project_root

        results = []
        services_list = ["web", "backend"] if services == "all" else [services]

        for service in services_list:
            service_result = _build_single_service(service, tag, registry, project_root)
            results.append(service_result)

        return [{"type": "text", "text": str(results)}]

    @mcp.tool(
        name="deploy__build_status",
        description="[部署] 检查本地 Docker 环境和现有镜像状态。",
    )
    def check_build_status() -> list[dict]:
        """检查 Docker 构建环境状态。"""
        try:
            docker_info = subprocess.run(
                ["docker", "info", "--format", "{{.ServerVersion}}"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            docker_ok = docker_info.returncode == 0
            docker_version = docker_info.stdout.strip() if docker_ok else "N/A"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            docker_ok = False
            docker_version = "N/A"

        config = DeployConfig()

        # 检查本地已有镜像
        existing_images = []
        try:
            result = subprocess.run(
                [
                    "docker", "images", "--format",
                    "{{.Repository}}:{{.Tag}}",
                ],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if result.returncode == 0:
                all_images = result.stdout.strip().splitlines()
                registry = config.get_harbor_registry()
                existing_images = [img for img in all_images if registry in img]
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return [{
            "type": "text",
            "text": str({
                "docker_available": docker_ok,
                "docker_version": docker_version,
                "harbor_registry": config.get_harbor_registry(),
                "existing_images": existing_images,
            }),
        }]


def _build_single_service(
    service: str, tag: str, registry: str, project_root: Path
) -> dict:
    """构建单个服务的 Docker 镜像。"""
    if service == "web":
        dockerfile = "web-client/Dockerfile"
        context = "."
        image_name = f"{registry}/web:{tag}"
    elif service == "backend":
        dockerfile = "backend/Dockerfile"
        context = "./backend"
        image_name = f"{registry}/backend:{tag}"
    else:
        return {"service": service, "status": "error", "message": f"未知服务: {service}"}

    cmd = [
        "docker", "build",
        "-f", dockerfile,
        "-t", image_name,
        context,
    ]

    # web 构建时传递 build args
    if service == "web":
        cmd.extend(["--build-arg", "VITE_API_URL=/"])
        cmd.extend(["--build-arg", "VITE_WS_URL=/"])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,
            cwd=str(project_root),
        )
        if result.returncode == 0:
            return {
                "service": service,
                "status": "success",
                "image": image_name,
                "tag": tag,
            }
        else:
            return {
                "service": service,
                "status": "failed",
                "image": image_name,
                "error": result.stderr[-500:] if result.stderr else "未知错误",
            }
    except subprocess.TimeoutExpired:
        return {
            "service": service,
            "status": "failed",
            "image": image_name,
            "error": "构建超时（超过 600 秒）",
        }
    except FileNotFoundError:
        return {
            "service": service,
            "status": "failed",
            "image": image_name,
            "error": "未找到 Docker 命令，请确认 Docker 已安装",
        }
