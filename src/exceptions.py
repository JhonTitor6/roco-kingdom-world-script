"""自定义异常"""


class RocoBaseError(Exception):
    """项目基础异常"""
    pass


class GameWindowNotFoundError(RocoBaseError):
    """游戏窗口未找到"""
    pass


class ImageNotFoundError(RocoBaseError):
    """图像识别失败"""
    pass


class BattleTimeoutError(RocoBaseError):
    """战斗超时"""
    pass


class ConfigError(RocoBaseError):
    """配置错误"""
    pass


class ElfNotFoundError(RocoBaseError):
    """精灵未找到"""
    pass
