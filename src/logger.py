"""日志模块"""
import sys
from pathlib import Path
from loguru import logger


def setup_logger(level: str = "DEBUG") -> logger:
    """配置日志

    Args:
        level: 日志级别 DEBUG / INFO / WARNING

    Returns:
        logger 实例
    """
    # 移除默认 handler
    logger.remove()

    # 添加控制台输出
    logger.add(
        sys.stderr,
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        colorize=True
    )

    # 添加文件输出
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    logger.add(
        log_dir / "roco_{time:YYYY-MM-DD}.log",
        level="DEBUG",
        rotation="00:00",
        retention="7 days",
        encoding="utf-8",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}"
    )

    return logger


def get_logger():
    """获取 logger 实例（方便导入）"""
    return logger
