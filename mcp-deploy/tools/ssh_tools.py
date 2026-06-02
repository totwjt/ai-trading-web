"""SSH 工具——带安全守卫的远程服务器操作。

安全设计：
1. 所有命令执行前经过 safety.check_command_safety 检查
2. 禁止命令直接拒绝，高风险操作返回 "需要确认" 状态
3. SSH 连接信息从 .env.deploy 读取，不硬编码
"""

import io
import os
import subprocess
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP

from config import DeployConfig
from safety import (
    check_command_safety,
    check_docker_compose_conflict,
)


def register_ssh_tools(mcp: FastMCP) -> None:
    """注册 SSH 相关的 MCP 工具。"""

    @mcp.tool(
        name="deploy__ssh_test_connection",
        description="[部署-安全] 测试 SSH 到生产服务器的连接是否正常。不执行任何操作，仅检查可达性和认证。",
    )
    def ssh_test_connection() -> list[dict]:
        """测试 SSH 连接生产服务器。"""
        config = DeployConfig()
        result = _run_ssh_command(config, "echo 'SSH_OK' && whoami && hostname", readonly=True)

        if result["status"] == "success":
            return [{
                "type": "text",
                "text": f"✓ SSH 连接成功\n  服务器: {config.ssh_user}@{config.ssh_host}:{config.ssh_port}\n  响应: {result['stdout']}",
            }]
        else:
            return [{
                "type": "text",
                "text": f"✗ SSH 连接失败: {result.get('error', '连接超时或被拒绝')}\n"
                        f"请确认:\n"
                        f"1. 生产服务器 {config.ssh_host} 是否可达\n"
                        f"2. 用户 {config.ssh_user} 是否存在\n"
                        f"3. SSH 密钥是否正确 (ssh_key_path={config.ssh_key_path})\n"
                        f"4. 生产服务器是否已添加本机公钥",
            }]

    @mcp.tool(
        name="deploy__ssh_execute",
        description="[部署-安全] 在生产服务器执行指定命令。**SSH 命令经过安全检查**：危险命令会被阻止，高风险命令需要先获得您确认。AI 不能替您决定执行高风险命令。",
    )
    def ssh_execute(command: str, reason: str = "") -> list[dict]:
        """在生产服务器安全地执行命令。

        Args:
            command: 要执行的命令
            reason: 执行此命令的原因说明（便于安全审计）
        """
        config = DeployConfig()

        # 安全检查
        safety = check_command_safety(command)
        if safety.risk_level == "blocked":
            return [{
                "type": "text",
                "text": f"⛔ 安全限制: {safety.reason}\n该命令被 mcp-deploy 禁止执行。",
            }]
        elif safety.risk_level == "ask":
            return [{
                "type": "text",
                "text": f"⚠️ 需要您确认: {safety.reason}\n\n"
                        f"命令: `{command}`\n"
                        f"原因: {reason or '未说明'}\n\n"
                        f"mcp-deploy **不会** 自动执行此命令。请确认是否继续。",
            }]

        result = _run_ssh_command(config, command, readonly=False)
        if result["status"] == "success":
            return [{
                "type": "text",
                "text": f"✓ 命令执行成功\nstdout:\n{result['stdout'][:2000]}",
            }]
        else:
            return [{
                "type": "text",
                "text": f"✗ 命令执行失败:\n{result.get('error', '未知错误')}",
            }]

    @mcp.tool(
        name="deploy__ssh_check_docker",
        description="[部署] 检查生产服务器上的 Docker 环境（docker 版本、compose 版本、运行中的容器）。只读操作。",
    )
    def ssh_check_docker() -> list[dict]:
        """检查生产服务器 Docker 环境。"""
        config = DeployConfig()

        commands = [
            "docker --version",
            "docker compose version",
            "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'",
            "docker compose -f docker-compose.prod.yml config --services 2>/dev/null || echo 'compose file not found'",
        ]

        combined_cmd = " && ".join(commands)
        result = _run_ssh_command(config, combined_cmd, readonly=True)

        if result["status"] == "success":
            return [{
                "type": "text",
                "text": f"--- 生产服务器 Docker 状态 ---\n{result['stdout']}",
            }]
        else:
            return [{
                "type": "text",
                "text": f"查询失败: {result.get('error', '无法连接')}",
            }]

    @mcp.tool(
        name="deploy__ssh_check_conflicts",
        description="[部署-安全] 检查生产服务器是否存在容器/端口冲突。此工具仅检测，**不会** 修改任何内容。如果发现冲突，mcp-deploy 会向您报告，但 **不会自动解决**。",
    )
    def ssh_check_conflicts() -> list[dict]:
        """检查生产环境冲突（容器名、端口等）。"""
        config = DeployConfig()

        # 获取现有容器列表
        ps_result = _run_ssh_command(
            config,
            "docker ps --format '{{.Names}}|{{.Ports}}'",
            readonly=True,
        )

        if ps_result["status"] != "success":
            return [{
                "type": "text",
                "text": f"无法获取容器列表: {ps_result.get('error', 'SSH 连接失败')}",
            }]

        containers = []
        ports = []
        for line in ps_result["stdout"].strip().splitlines():
            if "|" in line:
                name, port_str = line.split("|", 1)
                containers.append(name.strip())
                ports.append({"name": name.strip(), "ports": port_str.strip()})

        # 目标服务
        target_services = ["ai-trading-web", "ai-trading-backend", "ai-trading-postgres"]

        container_conflict = check_docker_compose_conflict(containers, target_services)

        result = {
            "running_containers": containers,
            "target_services": target_services,
            "potential_conflicts": container_conflict is not None,
            "conflict_detail": container_conflict,
            "action_taken": "none",
            "message": "mcp-deploy 不会自动修改任何运行中的容器。如有冲突，请确认如何处理。",
        }

        return [{"type": "text", "text": str(result)}]

    @mcp.tool(
        name="deploy__ssh_pull_images",
        description="[部署] 在生产服务器上拉取最新镜像（docker compose pull）。建议先调用 deploy__ssh_check_docker 确认环境正常。",
    )
    def ssh_pull_images(
        services: str = "all",
        image_tag: str = "",
    ) -> list[dict]:
        """在生产服务器拉取最新镜像。

        Args:
            services: 拉取范围 "web", "backend", "all"（默认 "all"）
            image_tag: 镜像标签（默认 "latest"）
        """
        config = DeployConfig()
        tag = image_tag or config.image_tag

        if tag != "latest":
            pull_cmd = (
                f"cd /root/ai-trading-web && "
                f"IMAGE_TAG={tag} docker compose -f docker-compose.prod.yml --env-file .env.deploy pull"
            )
        else:
            pull_cmd = (
                "cd /root/ai-trading-web && "
                "docker compose -f docker-compose.prod.yml --env-file .env.deploy pull"
            )

        result = _run_ssh_command(config, pull_cmd, readonly=False)
        if result["status"] == "success":
            return [{
                "type": "text",
                "text": f"✓ 镜像拉取成功 (tag: {tag})",
            }]
        else:
            return [{
                "type": "text",
                "text": f"✗ 镜像拉取失败:\n{result.get('error', '超时或连接断开')}",
            }]

    @mcp.tool(
        name="deploy__ssh_compose_up",
        description="[部署-安全] 在生产服务器启动服务（docker compose up -d）。**此操作会重启容器**。将先检查冲突并汇报，需要您确认后才能执行。",
    )
    def ssh_compose_up(
        image_tag: str = "",
        force_confirmed: bool = False,
    ) -> list[dict]:
        """在生产服务器启动服务。

        Args:
            image_tag: 镜像标签（默认 "latest"）
            force_confirmed: 是否已确认风险。mcp-deploy 要求必须确认才能执行。
        """
        if not force_confirmed:
            return [{
                "type": "text",
                "text": "⚠️ 请先确认:\n"
                        "1. 已调用 deploy__ssh_check_conflicts 检查冲突\n"
                        "2. 已确认当前生产环境状态\n"
                        "3. 已准备好启动服务\n\n"
                        "如果确认无误，请设置 force_confirmed=true 再调用此工具。",
            }]

        config = DeployConfig()
        tag = image_tag or config.image_tag

        if tag != "latest":
            cmd = (
                f"cd /root/ai-trading-web && "
                f"IMAGE_TAG={tag} docker compose -f docker-compose.prod.yml --env-file .env.deploy up -d"
            )
        else:
            cmd = (
                "cd /root/ai-trading-web && "
                "docker compose -f docker-compose.prod.yml --env-file .env.deploy up -d"
            )

        result = _run_ssh_command(config, cmd, readonly=False)
        if result["status"] == "success":
            return [{
                "type": "text",
                "text": f"✓ docker compose up -d 执行成功\n请调用 deploy__verify_services 验证服务状态。",
            }]
        else:
            return [{
                "type": "text",
                "text": f"✗ 启动失败:\n{result.get('error', '超时或连接断开')}",
            }]

    @mcp.tool(
        name="deploy__ssh_compose_down",
        description="[部署-安全] 在生产服务器停止服务（docker compose down）。**高风险操作**，需要您明确确认。此工具只检查并报告，不会自动执行。",
    )
    def ssh_compose_down(confirmed: bool = False) -> list[dict]:
        """停止生产服务。

        Args:
            confirmed: 必须设为 true 才会执行
        """
        if not confirmed:
            return [{
                "type": "text",
                "text": "⚠️ 停止服务将导致生产环境不可用。请确认后设置 confirmed=true。",
            }]

        config = DeployConfig()
        cmd = (
            "cd /root/ai-trading-web && "
            "docker compose -f docker-compose.prod.yml --env-file .env.deploy down"
        )

        result = _run_ssh_command(config, cmd, readonly=False)
        if result["status"] == "success":
            return [{"type": "text", "text": "✓ 服务已停止"}]
        else:
            return [{"type": "text", "text": f"✗ 停止失败: {result.get('error', '')}"}]


def _run_ssh_command(
    config: DeployConfig,
    command: str,
    readonly: bool = False,
) -> dict:
    """通过 SSH 在生产服务器执行命令。

    优先使用 subprocess ssh 命令（支持 SSH 密钥、ssh-agent）。
    """
    # 再次安全检查（非 readonly 命令）
    if not readonly:
        safety = check_command_safety(command)
        if safety.risk_level == "blocked":
            return {"status": "failed", "error": f"安全限制: {safety.reason}"}

    # 构建 SSH 命令
    ssh_cmd = ["ssh"]

    if config.ssh_port and config.ssh_port != 22:
        ssh_cmd.extend(["-p", str(config.ssh_port)])

    if config.ssh_key_path:
        key_path = Path(config.ssh_key_path).expanduser()
        if key_path.exists():
            ssh_cmd.extend(["-i", str(key_path)])

    # 禁用主机密钥检查（内网环境）
    ssh_cmd.extend([
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "ConnectTimeout=10",
    ])

    ssh_cmd.append(f"{config.ssh_user}@{config.ssh_host}")
    ssh_cmd.append(command)

    try:
        result = subprocess.run(
            ssh_cmd,
            capture_output=True,
            text=True,
            timeout=config.ssh_timeout,
        )
        if result.returncode == 0:
            return {
                "status": "success",
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        else:
            return {
                "status": "failed",
                "error": result.stderr or result.stdout or f"退出码: {result.returncode}",
            }
    except subprocess.TimeoutExpired:
        return {"status": "failed", "error": "SSH 命令执行超时"}
    except FileNotFoundError:
        return {"status": "failed", "error": "未找到 ssh 命令"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}
