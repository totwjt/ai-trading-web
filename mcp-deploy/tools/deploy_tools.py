"""部署编排工具——组合多个操作为完整部署流程。"""

from mcp.server.fastmcp import FastMCP


def register_deploy_tools(mcp: FastMCP) -> None:
    """注册部署编排相关的 MCP 工具。"""

    @mcp.tool(
        name="deploy__get_deploy_guide",
        description="[部署] 获取标准生产部署流程指南。AI 应按此流程逐步执行，每步都需要您确认。返回完整的部署步骤清单。",
    )
    def get_deploy_guide() -> list[dict]:
        """获取标准部署流程指南。"""
        guide = {
            "title": "AI Trading Web - 标准生产部署流程",
            "version": "1.0",
            "safety_notice": "mcp-deploy 不会自动执行任何破坏性操作。每步都需要您确认。",
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
                    "action": "检查本地环境",
                    "tool": "deploy__check_env",
                    "description": "读取 .env.deploy 配置，验证必要字段",
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
                    "action": "冲突检测",
                    "tool": "deploy__ssh_check_conflicts",
                    "description": "检查容器名/端口冲突。如有冲突，需您决定如何处理",
                },
                {
                    "step": 9,
                    "action": "生产拉取新镜像",
                    "tool": "deploy__ssh_pull_images",
                    "description": "在生产服务器拉取最新镜像",
                },
                {
                    "step": 10,
                    "action": "启动服务",
                    "tool": "deploy__ssh_compose_up",
                    "description": "在生产服务器执行 docker compose up -d",
                },
                {
                    "step": 11,
                    "action": "验证部署",
                    "tool": "deploy__verify_services",
                    "description": "验证服务是否正常运行",
                },
                {
                    "step": 12,
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
            "": "建议先调用 deploy__check_env 检查部署环境配置。",
            "check_env": "下一步: 调用 deploy__validate_env 验证配置文件完整性。",
            "validate_env": "下一步: 调用 deploy__build_status 检查 Docker 构建环境。",
            "build_status": "下一步: 调用 deploy__build_images 构建镜像（参数 services='all'）。",
            "build_images": "下一步: 调用 deploy__login_harbor 登录 Harbor，然后 deploy__push_images 推送镜像。",
            "push_images": "下一步: 调用 deploy__ssh_test_connection 测试生产服务器 SSH 连接。",
            "ssh_test": "下一步: 调用 deploy__ssh_check_docker 查看生产环境状态。",
            "check_docker": "下一步: 调用 deploy__ssh_check_conflicts 检查冲突。",
            "check_conflicts": "下一步: 调用 deploy__ssh_pull_images 在生产拉取新镜像。",
            "pull_images": "下一步: 调用 deploy__ssh_compose_up 启动服务。需要您确认后才能执行。",
            "compose_up": "下一步: 调用 deploy__verify_services 和 deploy__verify_health 验证部署成功。",
            "verify": "部署完成！建议检查业务功能是否正常。",
        }
        advice = flow.get(current_step, f"未知状态: {current_step}。建议调用 deploy__get_deploy_guide 查看完整流程。")
        return [{"type": "text", "text": advice}]
