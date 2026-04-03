"""src.exceptions 单元测试"""
import pytest
from src.exceptions import (
    RocoBaseError,
    GameWindowNotFoundError,
    ImageNotFoundError,
    BattleTimeoutError,
    ConfigError,
    ElfNotFoundError,
)


class TestExceptions:
    """异常类测试"""

    def test_roco_base_error(self):
        """测试基础异常"""
        with pytest.raises(RocoBaseError):
            raise RocoBaseError("test")

    def test_game_window_not_found_error(self):
        """测试游戏窗口未找到异常"""
        with pytest.raises(GameWindowNotFoundError):
            raise GameWindowNotFoundError("窗口未找到")

    def test_image_not_found_error(self):
        """测试图像未找到异常"""
        with pytest.raises(ImageNotFoundError):
            raise ImageNotFoundError("图像未找到")

    def test_battle_timeout_error(self):
        """测试战斗超时异常"""
        with pytest.raises(BattleTimeoutError):
            raise BattleTimeoutError("战斗超时")

    def test_config_error(self):
        """测试配置错误异常"""
        with pytest.raises(ConfigError):
            raise ConfigError("配置错误")

    def test_elf_not_found_error(self):
        """测试精灵未找到异常"""
        with pytest.raises(ElfNotFoundError):
            raise ElfNotFoundError("精灵未找到")

    def test_exception_inheritance(self):
        """测试异常继承关系"""
        assert issubclass(GameWindowNotFoundError, RocoBaseError)
        assert issubclass(ImageNotFoundError, RocoBaseError)
        assert issubclass(BattleTimeoutError, RocoBaseError)
        assert issubclass(ConfigError, RocoBaseError)
        assert issubclass(ElfNotFoundError, RocoBaseError)
