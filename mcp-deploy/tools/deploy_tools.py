"""部署编排工具——组合多个操作为完整部署流程。"""

import subprocess
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP

from config import DeployConfig
from tools.env_tools import validate_env_file
from tools.ssh_tools import _compose_cmd, _q, _run_ssh_command


def register_deploy_tools(mcp: FastMCP) -> None:
    """注册部署编排相关的 MCP 工具。"""

    @mcp.tool(
        name="deploy__status",
        description="[部署] 汇总当前部署状态和下一步建议。只返回脱敏状态，正常部署流程应从此工具开始。",
    )
    def deploy_status() -> list[dict]:
        """读取 MCP 管理的配置并执行只读状态检查。"""
        config = DeployConfig()
        env_file = config.get_deploy_env_path()
        env_validation = validate_env_file(env_file) if env_file else None
        docker_available, docker_version = _local_docker_status()

        ssh_auth_mode = config.ssh_auth_mode()
        ssh_ready = ssh_auth_mode == "key" or (
            ssh_auth_mode == "password" and config.sshpass_available()
        )

        remote_preflight = {
            "checked": False,
            "ok": False,
            "remote_deploy_dir": config.remote_deploy_dir,
            "remote_compose_file": config.get_remote_compose_file(),
            "remote_env_file": config.get_remote_env_file(),
        }
        if ssh_ready:
            cmd = (
                f"test -f {_q(config.get_remote_compose_file())} && "
                f"test -f {_q(config.get_remote_env_file())} && "
                f"{_compose_cmd(config)} config >/dev/null && "
                "echo PREFLIGHT_OK"
            )
            preflight_result = _run_ssh_command(config, cmd, readonly=True)
            remote_preflight.update({
                "checked": True,
                "ok": preflight_result["status"] == "success",
            })
            if preflight_result["status"] != "success":
                remote_preflight["error"] = preflight_result.get("error", "远端预检失败")

        recommended_next = _recommend_next(env_file, env_validation, docker_available, ssh_ready, remote_preflight)

        payload = {
            "config_file_found": env_file is not None,
            "config_file_path": str(env_file) if env_file else None,
            "env_validation": env_validation,
            "ssh_auth_mode": ssh_auth_mode,
            "sshpass_available": config.sshpass_available()
            if ssh_auth_mode == "password"
            else None,
            "remote_deploy_dir": config.remote_deploy_dir,
            "remote_compose_file": config.get_remote_compose_file(),
            "remote_env_file": config.get_remote_env_file(),
            "build": {
                "docker_available": docker_available,
                "docker_version": docker_version,
                "build_platform": config.build_platform,
                "image_tag": config.image_tag,
            },
            "remote_preflight": remote_preflight,
            "recommended_next": recommended_next,
        }

        return [{"type": "text", "text": str(payload)}]

    @mcp.tool(
        name="deploy__get_deploy_guide",
        description="[部署] 获取标准生产部署流程指南。AI 应按此流程逐步执行，每步都需要您确认。返回完整的部署步骤清单。",
    )
    def get_deploy_guide() -> list[dict]:
        """获取标准部署流程指南。"""
        guide = {
            "title": "AI Trading Web - 标准生产部署流程",
            "version": "1.1",
            "safety_notice": "正常流程从 deploy__status 开始；mcp-deploy 不会暴露部署密码或自动执行破坏性操作。",
            "prohibited_actions": [
                "禁止在生产环境卸载任何软件",
                "禁止覆盖文件而不确认",
                "禁止自动解决容器/端口冲突——必须提问",
                "禁止运行危险命令（rm -rf /、curl | bash 等）",
                "禁止修改生产环境系统配置",
            ],
            "steps": [
                {
                    "step": 1,
                    "action": "查询部署状态",
                    "tool": "deploy__status",
                    "description": "读取脱敏配置、Docker 状态、SSH 认证模式和远端预检结果",
                },
                {
                    "step": 2,
                    "action": "验证配置文件",
                    "tool": "deploy__validate_env",
                    "description": "检查 .env.deploy 文件完整性和占位符残留",
                },
                {
                    "step": 3,
                    "action": "检查 Docker 构建环境",
                    "tool": "deploy__build_status",
                    "description": "确认本地 Docker 可用",
                },
                {
                    "step": 4,
                    "action": "构建镜像",
                    "tool": "deploy__build_images",
                    "description": "构建 web + backend Docker 镜像",
                },
                {
                    "step": 5,
                    "action": "推送镜像到 Harbor",
                    "tool": "deploy__push_images",
                    "description": "将镜像推送到 Harbor 仓库（需先登录）",
                },
                {
                    "step": 6,
                    "action": "测试 SSH 连接",
                    "tool": "deploy__ssh_test_connection",
                    "description": "确认能连接到生产服务器",
                },
                {
                    "step": 7,
                    "action": "检查生产环境状态",
                    "tool": "deploy__ssh_check_docker",
                    "description": "查看生产服务器 Docker 状态和当前运行容器",
                },
                {
                    "step": 8,
                    "action": "远端路径预检",
                    "tool": "deploy__ssh_preflight",
                    "description": "检查远端 docker-compose.prod.yml、.env.deploy 和 compose config",
                },
                {
                    "step": 9,
                    "action": "冲突检测",
                    "tool": "deploy__ssh_check_conflicts",
                    "description": "检查容器名/端口冲突。如有冲突，需您决定如何处理",
                },
                {
                    "step": 10,
                    "action": "生产拉取新镜像",
                    "tool": "deploy__ssh_pull_images",
                    "description": "在生产服务器拉取最新镜像；支持 services='backend'|'web'|'all'",
                },
                {
                    "step": 11,
                    "action": "启动服务",
                    "tool": "deploy__ssh_compose_up",
                    "description": "在生产服务器执行 docker compose up -d；支持 services='backend'|'web'|'all'",
                },
                {
                    "step": 12,
                    "action": "验证部署",
                    "tool": "deploy__verify_services",
                    "description": "验证服务是否正常运行",
                },
                {
                    "step": 13,
                    "action": "可用性确认",
                    "tool": "deploy__verify_health",
                    "description": "最终确认生产服务可用",
                },
            ],
        }
        return [{"type": "text", "text": str(guide)}]

    @mcp.tool(
        name="deploy__whats_next",
        description="[部署] 根据当前部署状态，告诉您下一步应该做什么。AI 应调用此工具来获取下一步操作建议。",
    )
    def whats_next(current_step: str = "") -> list[dict]:
        """获取下一步操作建议。

        Args:
            current_step: 当前完成的步骤名（如 'check_env', 'build'），留空返回初始建议
        """
        flow = {
            "": "建议先调用 deploy__status 查询脱敏部署状态。",
            "status": "根据 deploy__status 的 recommended_next 执行下一步。",
            "check_env": "下一步: 调用 deploy__validate_env 验证配置文件完整性。",
            "validate_env": "下一步: 调用 deploy__build_status 检查 Docker 构建环境。",
            "build_status": "下一步: 调用 deploy__build_images 构建镜像（参数 services='all'）。",
            "build_images": "下一步: 调用 deploy__login_harbor 登录 Harbor，然后 deploy__push_images 推送镜像。",
            "push_images": "下一步: 调用 deploy__ssh_test_connection 测试生产服务器 SSH 连接。",
            "ssh_test": "下一步: 调用 deploy__ssh_check_docker 查看生产环境状态。",
            "check_docker": "下一步: 调用 deploy__ssh_preflight 检查远端 compose/env 路径。",
            "ssh_preflight": "下一步: 调用 deploy__ssh_check_conflicts 检查冲突。",
            "check_conflicts": "下一步: 调用 deploy__ssh_pull_images 在生产拉取新镜像。",
            "pull_images": "下一步: 调用 deploy__ssh_compose_up 启动服务。需要您确认后才能执行。",
            "compose_up": "下一步: 调用 deploy__verify_services 和 deploy__verify_health 验证部署成功。",
            "verify": "部署完成！建议检查业务功能是否正常。",
        }
        advice = flow.get(current_step, f"未知状态: {current_step}。建议调用 deploy__get_deploy_guide 查看完整流程。")
        return [{"type": "text", "text": advice}]


def _local_docker_status() -> tuple[bool, str]:
    try:
        docker_info = subprocess.run(
            ["docker", "info", "--format", "{{.ServerVersion}}"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if docker_info.returncode == 0:
            return True, docker_info.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return False, "N/A"


def _recommend_next(
    env_file: Optional[Path],
    env_validation: Optional[dict],
    docker_available: bool,
    ssh_ready: bool,
    remote_preflight: dict,
) -> str:
    if env_file is None:
        return "创建 .env.deploy 或确认 PROJECT_ROOT 指向项目根目录"
    if not env_validation or not env_validation.get("is_valid"):
        return "调用 deploy__validate_env 修正缺失、空值或占位符配置"
    if not docker_available:
        return "启动本地 Docker 后调用 deploy__build_status"
    if not ssh_ready:
        return "配置 SSH_KEY_PATH，或配置 SSH_PASSWORD 并安装 sshpass"
    if not remote_preflight.get("checked"):
        return "调用 deploy__ssh_preflight 检查远端 compose/env 路径"
    if not remote_preflight.get("ok"):
        return "修正 REMOTE_DEPLOY_DIR 或远端 docker-compose.prod.yml/.env.deploy"
    return "可以按 deploy__build_images -> deploy__push_images -> deploy__ssh_pull_images -> deploy__ssh_compose_up 继续"
