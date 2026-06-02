"""安全规则——所有部署操作必须经过安全检查。

核心原则（不可违反）：
1. 任何冲突必须提问用户，禁止 AI 自行修改、覆盖或删除
2. 禁止在生产环境卸载软件
3. 禁止在生产环境覆盖文件（配置文件除外，且需确认）
4. 禁止运行 rm -rf /、curl | bash 等危险命令
"""

import re
from typing import Optional

# 禁止在生产服务器执行的命令模式
_FORBIDDEN_COMMAND_PATTERNS: list[re.Pattern] = [
    re.compile(r"\brm\s+(-rf?)\s+/", re.IGNORECASE),
    re.compile(r"\bmkfs\b", re.IGNORECASE),
    re.compile(r"\bdd\s+if=", re.IGNORECASE),
    re.compile(r"\buninstall\b", re.IGNORECASE),
    re.compile(r"\bapt-get\s+remove\b", re.IGNORECASE),
    re.compile(r"\byum\s+remove\b", re.IGNORECASE),
    re.compile(r"\bpacman\s+-R", re.IGNORECASE),
    re.compile(r"\bcurl\s+.*\|\s*(ba)?sh", re.IGNORECASE),
    re.compile(r"\bwget\s+.*-O-\s*\|\s*(ba)?sh", re.IGNORECASE),
    re.compile(r"\bchmod\s+-?R?\s*777\b", re.IGNORECASE),
    re.compile(r"\bpasswd\b", re.IGNORECASE),
    re.compile(r"\busermod\b", re.IGNORECASE),
    re.compile(r"\bdpkg\s+--purge\b", re.IGNORECASE),
    re.compile(r"\brpm\s+-e\b", re.IGNORECASE),
    re.compile(r"\bkillall\b", re.IGNORECASE),
    re.compile(r"\bpkill\b", re.IGNORECASE),
]

# 需要用户确认的高风险操作
_HIGH_RISK_PATTERNS: list[re.Pattern] = [
    re.compile(r"\bdocker\s+(rm|rmi|system\s+prune)", re.IGNORECASE),
    re.compile(r"\bdocker\s+stop\b", re.IGNORECASE),
    re.compile(r"\bdocker\s+kill\b", re.IGNORECASE),
    re.compile(r"\brm\s+-rf", re.IGNORECASE),
    re.compile(r"\bmv\s+", re.IGNORECASE),
    re.compile(r"\bcp\s+", re.IGNORECASE),
    re.compile(r"\boverwrite\b", re.IGNORECASE),
    re.compile(r"\b>\s*/", re.IGNORECASE),  # 重定向到根目录
    re.compile(r"\breboot\b", re.IGNORECASE),
    re.compile(r"\bshutdown\b", re.IGNORECASE),
    re.compile(r"\bsystemctl\s+(restart|stop|disable)", re.IGNORECASE),
    re.compile(r"\bservice\s+\w+\s+(restart|stop)", re.IGNORECASE),
    re.compile(r"\bscp\s+", re.IGNORECASE),
    re.compile(r"\brsync\b", re.IGNORECASE),
    re.compile(r"\bgit\s+reset\b", re.IGNORECASE),
    re.compile(r"\bgit\s+checkout\s+--\b", re.IGNORECASE),
    re.compile(r"\bsed\s+-i", re.IGNORECASE),
]

# 白名单命令——低风险、只读操作
_READONLY_COMMANDS: list[str] = [
    "docker ps",
    "docker compose ps",
    "docker images",
    "docker info",
    "docker version",
    "curl",
    "ping",
    "ls",
    "pwd",
    "whoami",
    "uname",
    "df",
    "free",
    "uptime",
    "cat",
    "head",
    "tail",
    "grep",
    "find",
    "which",
    "docker compose -f docker-compose.prod.yml config",
    "docker compose -f docker-compose.prod.yml images",
    "docker compose -f docker-compose.prod.yml logs",
]


class SafetyError(Exception):
    """安全规则违规异常。"""


class SafetyCheckResult:
    """安全检查结果。"""

    def __init__(self, passed: bool, reason: str = "", risk_level: str = "ok"):
        self.passed = passed
        self.reason = reason
        self.risk_level = risk_level  # "ok", "ask", "blocked"

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "reason": self.reason,
            "risk_level": self.risk_level,
            "action_required": self.risk_level == "ask",
        }


def is_readonly_command(command: str) -> bool:
    """判断是否为只读命令，无需确认。"""
    cmd_trimmed = command.strip().rstrip(";").strip()
    for readonly in _READONLY_COMMANDS:
        if cmd_trimmed.startswith(readonly):
            return True
    return False


def check_command_safety(command: str) -> SafetyCheckResult:
    """检查命令是否安全。返回检查结果。"""
    # 1. 检查禁止命令
    for pattern in _FORBIDDEN_COMMAND_PATTERNS:
        if pattern.search(command):
            return SafetyCheckResult(
                passed=False,
                reason=f"禁止执行危险命令（匹配模式: {pattern.pattern}）",
                risk_level="blocked",
            )

    # 2. 检查高风险操作
    for pattern in _HIGH_RISK_PATTERNS:
        if pattern.search(command):
            return SafetyCheckResult(
                passed=False,
                reason=f"高风险操作，需要您确认（匹配模式: {pattern.pattern}）",
                risk_level="ask",
            )

    return SafetyCheckResult(passed=True, risk_level="ok")


def check_docker_compose_conflict(
    existing_containers: list[str], target_services: list[str]
) -> Optional[str]:
    """检查容器冲突。发现有同名容器时返回提示信息。"""
    conflicts = []
    for container in existing_containers:
        for service in target_services:
            if service in container or container in service:
                conflicts.append(container)

    if conflicts:
        return (
            f"发现可能存在冲突的容器: {', '.join(conflicts)}\n"
            "mcp-deploy 不会自动停止、删除或覆盖任何容器。\n"
            "请先确认是否需要手动处理冲突容器，再继续部署。"
        )
    return None


def check_port_conflict(
    existing_ports: list[dict], required_ports: list[int]
) -> Optional[str]:
    """检查端口冲突。"""
    conflicts = []
    for port_info in existing_ports:
        for req_port in required_ports:
            exposed = port_info.get("ports", [])
            if str(req_port) in str(exposed):
                conflicts.append(f"端口 {req_port} 已被占用: {port_info}")

    if conflicts:
        return (
            f"发现端口冲突:\n" + "\n".join(conflicts) + "\n"
            "请确认是否继续。mcp-deploy **不会** 自动释放端口。"
        )
    return None
