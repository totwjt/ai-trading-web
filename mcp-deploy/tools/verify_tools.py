"""验证工具——部署后验证、健康检查。"""

from mcp.server.fastmcp import FastMCP

from config import DeployConfig
from tools.ssh_tools import _compose_cmd, _image_tag_prefix, _run_ssh_command, _with_remote_dir


def register_verify_tools(mcp: FastMCP) -> None:
    """注册验证相关的 MCP 工具。"""

    @mcp.tool(
        name="deploy__verify_services",
        description="[部署] 验证生产服务器上的服务是否已正常启动。检查所有容器运行状态，只读操作。",
    )
    def verify_services() -> list[dict]:
        """验证生产服务运行状态。"""
        config = DeployConfig()

        result = _run_ssh_command(
            config,
            (
                "echo '=== 容器状态 ===' && "
                f"{_compose_cmd(config)} ps && "
                "echo '' && "
                "echo '=== 所有容器(含已停止) ===' && "
                "docker ps -a --format 'table {{.Names}}\t{{.Status}}'"
            ),
            readonly=True,
        )

        if result["status"] == "success":
            return [{
                "type": "text",
                "text": (
                    f"--- 服务状态 ---\n远端路径: {config.remote_deploy_dir}\n"
                    f"{result['stdout']}"
                ),
            }]
        else:
            return [{
                "type": "text",
                "text": f"无法获取服务状态: {result.get('error', 'SSH 连接失败')}",
            }]

    @mcp.tool(
        name="deploy__verify_health",
        description="[部署] 验证生产服务健康状态。检查前端 80 端口和后端 /health 端点是否正常响应。只读操作。",
    )
    def verify_health() -> list[dict]:
        """验证服务健康状态。"""
        config = DeployConfig()

        health_checks = [
            ("后端 /health", "curl -sS -o /dev/null -w '%{http_code}' http://localhost:8766/health"),
            ("前端 80 端口", "curl -sS -o /dev/null -w '%{http_code}' http://localhost:80/"),
            ("SPA 路由", "curl -sS -o /dev/null -w '%{http_code}' http://localhost:80/recommendation"),
        ]

        results = []
        for name, cmd in health_checks:
            check_result = _run_ssh_command(config, cmd, readonly=True)
            if check_result["status"] == "success":
                status_code = check_result["stdout"].strip()
                is_healthy = status_code in ("200", "301", "302")
                results.append({
                    "endpoint": name,
                    "status_code": status_code,
                    "healthy": is_healthy,
                })
            else:
                results.append({
                    "endpoint": name,
                    "status_code": "N/A",
                    "healthy": False,
                    "error": check_result.get("error", ""),
                })

        all_healthy = all(r["healthy"] for r in results)

        return [{
            "type": "text",
            "text": str({
                "results": results,
                "all_healthy": all_healthy,
                "deployment_status": "✅ 部署成功" if all_healthy else "❌ 部分服务异常",
            }),
        }]

    @mcp.tool(
        name="deploy__verify_logs",
        description="[部署] 查看生产服务日志，用于排查问题。默认查看最近 50 行。只读操作。",
    )
    def verify_logs(
        service: str = "web",
        lines: int = 50,
        follow: bool = False,
    ) -> list[dict]:
        """查看生产服务日志。

        Args:
            service: 服务名 "web", "backend", "postgres"
            lines: 查看行数（默认 50）
            follow: 是否持续跟踪（默认 false）
        """
        config = DeployConfig()
        container_map = {
            "web": "ai-trading-web",
            "backend": "ai-trading-backend",
            "postgres": "ai-trading-postgres",
        }
        container = container_map.get(service, service)

        tail_flag = "+&" if follow else f"--tail {lines}"
        cmd = f"docker logs {tail_flag} {container} 2>&1 | head -{lines + 20}"
        # Ensure we bound the output even for follow mode
        if follow:
            cmd = f"docker logs --tail {lines} {container} 2>&1"

        result = _run_ssh_command(config, cmd, readonly=True)
        if result["status"] == "success":
            return [{
                "type": "text",
                "text": f"--- {service} 日志 (最近 {lines} 行) ---\n{result['stdout'][:3000]}",
            }]
        else:
            return [{
                "type": "text",
                "text": f"获取日志失败: {result.get('error', '')}",
            }]

    @mcp.tool(
        name="deploy__verify_rollback",
        description="[部署] 回滚到指定版本。设置 IMAGE_TAG 环境变量后重启服务。**高风险操作**，需要您明确确认。",
    )
    def verify_rollback(
        image_tag: str,
        confirmed: bool = False,
    ) -> list[dict]:
        """回滚到指定版本。

        Args:
            image_tag: 目标版本标签（必填）
            confirmed: 必须设为 true 才会执行
        """
        if not confirmed:
            return [{
                "type": "text",
                "text": (
                    f"⚠️ 回滚到 {image_tag} 将替换当前生产版本。\n"
                    "请确认:\n"
                    f"1. 镜像 {image_tag} 已在 Harbor 中存在\n"
                    "2. 您已确认需要回滚\n\n"
                    "设置 confirmed=true 执行回滚。"
                ),
            }]

        config = DeployConfig()

        # 拉取指定版本镜像
        pull_cmd = _with_remote_dir(
            config,
            f"{_image_tag_prefix(image_tag)}{_compose_cmd(config)} pull",
        )
        pull_result = _run_ssh_command(config, pull_cmd, readonly=False)

        if pull_result["status"] != "success":
            return [{
                "type": "text",
                "text": f"✗ 回滚失败: 无法拉取镜像 {image_tag}\n{pull_result.get('error', '')}",
            }]

        up_cmd = _with_remote_dir(
            config,
            f"{_image_tag_prefix(image_tag)}{_compose_cmd(config)} up -d",
        )
        up_result = _run_ssh_command(config, up_cmd, readonly=False)

        if up_result["status"] == "success":
            return [{
                "type": "text",
                "text": f"✓ 回滚到 {image_tag} 完成。请调用 deploy__verify_health 确认服务正常。",
            }]
        else:
            return [{
                "type": "text",
                "text": f"✗ 回滚启动失败: {up_result.get('error', '')}",
            }]
