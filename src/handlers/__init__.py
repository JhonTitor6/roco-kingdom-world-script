"""事件处理器包 - 自动发现并注册所有处理器

只要在 handlers/ 目录下创建继承 Handler 的类，
并调用 EventRegistry.register()，就会自动被注册。
"""
import importlib
from pathlib import Path

from src.handlers.base_handler import Handler

# 需要排除的模块（不是 Handler 子类或不需要注册的模块）
_EXCLUDE = {
    "__init__",    # 本模块
    "base_handler", # 基类
    "error",       # 旧架构
    "battle",      # 旧架构
    "insufficient", # 旧架构
}

# 自动发现并导入所有 handler 模块，触发自注册
for py_file in Path(__file__).parent.glob("*.py"):
    name = py_file.stem
    if name in _EXCLUDE or name.startswith("_"):
        continue
    importlib.import_module(f"src.handlers.{name}")

__all__ = ["Handler"]
