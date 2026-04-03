"""
策略编译与安全检查

负责策略代码的语法检查和安全审查
"""

import ast
import logging
from typing import Tuple, List, Optional

logger = logging.getLogger(__name__)

DANGEROUS_PATTERNS = [
    "open(",
    "os.system",
    "subprocess",
    "socket",
    "requests",
    "urllib",
    "http.client",
    "smtplib",
    "poplib",
    "imaplib",
    "ftp",
    "telnet",
    "popen",
    "getattr",
    "setattr",
    "exec(",
    "eval(",
    "__import__",
    "import os",
    "import subprocess",
    "import socket",
    "import sys",
    "sys.exit",
    "sys.path",
    "importlib",
    "reload(",
    "compile(",
    "memoryview",
    "buffer(",
]


class CompilationResult:
    """编译结果"""
    
    def __init__(
        self,
        success: bool,
        errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None
    ):
        self.success = success
        self.errors = errors or []
        self.warnings = warnings or []
    
    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "errors": self.errors,
            "warnings": self.warnings
        }


class SecurityChecker:
    """安全检查器"""
    
    def __init__(self):
        self.violations: List[str] = []
    
    def check(self, code: str) -> Tuple[bool, List[str]]:
        """
        检查代码安全性
        
        Returns:
            (is_safe, violations)
        """
        self.violations = []
        
        code_lower = code.lower()
        
        for pattern in DANGEROUS_PATTERNS:
            if pattern.lower() in code_lower:
                self.violations.append(f"禁止使用: {pattern}")
        
        try:
            tree = ast.parse(code)
            self._check_ast(tree, code)
        except SyntaxError as e:
            self.violations.append(f"语法错误: {e}")
        
        return len(self.violations) == 0, self.violations
    
    def _check_ast(self, tree: ast.AST, code: str):
        """AST 深度检查"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name.startswith("_"):
                    self.violations.append(f"禁止使用私有方法: {node.name}")
            
            if isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name):
                    if node.value.id == "os":
                        self.violations.append(f"禁止访问 os 模块")


def compile_strategy(code: str) -> CompilationResult:
    """
    编译策略代码
    
    Args:
        code: 策略代码字符串
    
    Returns:
        CompilationResult
    """
    errors = []
    warnings = []
    
    if not code or not code.strip():
        errors.append("策略代码不能为空")
        return CompilationResult(success=False, errors=errors)
    
    checker = SecurityChecker()
    is_safe, violations = checker.check(code)
    
    if not is_safe:
        errors.extend(violations)
        return CompilationResult(success=False, errors=errors)
    
    try:
        ast.parse(code)
    except SyntaxError as e:
        errors.append(f"Python 语法错误: {e.msg} (行 {e.lineno})")
        return CompilationResult(success=False, errors=errors)
    
    if "class" not in code:
        warnings.append("警告: 未检测到策略类定义")
    
    if "def" not in code:
        warnings.append("警告: 未检测到函数定义")
    
    return CompilationResult(success=True, warnings=warnings)


def validate_backtrader_strategy(code: str) -> Tuple[bool, List[str]]:
    """
    验证是否为有效的 Backtrader 策略
    
    Args:
        code: 策略代码
    
    Returns:
        (is_valid, errors)
    """
    errors = []
    
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        errors.append(f"语法错误: {e.msg}")
        return False, errors
    
    strategy_classes = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                if isinstance(base, ast.Attribute):
                    if base.attr == "Strategy":
                        strategy_classes.append(node.name)
                elif isinstance(base, ast.Name):
                    if base.id == "Strategy":
                        strategy_classes.append(node.name)
    
    if not strategy_classes:
        errors.append("未找到继承自 bt.Strategy 的策略类")
        return False, errors
    
    return True, []


def quick_preview_params(params: dict) -> dict:
    """
    生成预览参数
    
    将回测参数转换为预览模式参数
    - 保留用户输入的日期和交易参数
    - 预览模式下由引擎决定是否限制股票数量
    
    Args:
        params: 原始回测参数
    
    Returns:
        预览参数
    """
    return {
        "start_date": params.get("start_date"),
        "end_date": params.get("end_date"),
        "frequency": params.get("frequency", "1d"),
        "initial_capital": params.get("initial_capital", 1000000.0),
        "commission": params.get("commission", 0.0003),
        "use_min_commission": params.get("use_min_commission", True),
        "min_commission": params.get("min_commission", 5.0),
        "slippage": params.get("slippage", 0.0001),
        "fill_ratio": params.get("fill_ratio", 1.0),
        "adjust_mode": params.get("adjust_mode", "qfq"),
        "benchmark_code": params.get("benchmark_code", "000300.SH"),
        "symbols": params.get("symbols", []),
        "match_mode": params.get("match_mode", "open"),
        "max_stocks": 3,
    }
