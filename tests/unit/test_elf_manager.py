"""src.elf_manager 单元测试"""
import pytest
from unittest.mock import Mock, MagicMock
from src.elf_manager import ElfManager, ElfRole


class TestElfRole:
    """精灵角色常量测试"""

    def test_role_constants(self):
        """测试角色常量定义"""
        assert ElfRole.SACRIFICE == "sacrifice"
        assert ElfRole.FINAL == "final"
        assert ElfRole.RESERVE == "reserve"


class TestElfManager:
    """精灵管理器测试"""

    @pytest.fixture
    def mock_config(self):
        """模拟精灵配置"""
        return {
            "elves": [
                {"name": "精灵A", "template": "elves/elf_1.png", "role": "sacrifice"},
                {"name": "精灵B", "template": "elves/elf_2.png", "role": "sacrifice"},
                {"name": "精灵C", "template": "elves/elf_3.png", "role": "final"},
                {"name": "精灵D", "template": "elves/elf_4.png", "role": "reserve"}
            ]
        }

    @pytest.fixture
    def elf_manager(self, mock_config):
        """创建精灵管理器实例"""
        mock_controller = Mock()
        return ElfManager(config=mock_config, controller=mock_controller)

    def test_initialization(self, elf_manager, mock_config):
        """测试初始化"""
        assert elf_manager.config == mock_config

    def test_final_elf_property(self, elf_manager):
        """测试 final_elf 属性"""
        final_elf = elf_manager.final_elf
        assert final_elf["name"] == "精灵C"
        assert final_elf["role"] == "final"

    def test_reserve_elf_property(self, elf_manager):
        """测试 reserve_elf 属性"""
        reserve_elf = elf_manager.reserve_elf
        assert reserve_elf["name"] == "精灵D"
        assert reserve_elf["role"] == "reserve"

    def test_sacrifice_elves_property(self, elf_manager):
        """测试 sacrifice_elves 属性"""
        sacrifice_elves = elf_manager.sacrifice_elves
        assert len(sacrifice_elves) == 2
        assert all(elf["role"] == "sacrifice" for elf in sacrifice_elves)

    def test_get_sacrifice_order_faster(self, elf_manager):
        """测试送死顺序 - 我方先手"""
        order = elf_manager.get_sacrifice_order(faster=True)
        # 我方先手: final -> sacrifice -> sacrifice -> reserve
        assert order[0]["role"] == "final"
        assert order[-1]["role"] == "reserve"
        assert order.count(elf_manager.final_elf) == 1

    def test_get_sacrifice_order_slower(self, elf_manager):
        """测试送死顺序 - 对方先手"""
        order = elf_manager.get_sacrifice_order(faster=False)
        # 对方先手: reserve -> sacrifice -> sacrifice -> final
        assert order[0]["role"] == "reserve"
        assert order[-1]["role"] == "final"

    def test_missing_final_elf_raises(self, mock_config):
        """测试缺少 final 精灵时抛出异常"""
        mock_config["elves"] = [
            {"name": "精灵A", "template": "elves/elf_1.png", "role": "sacrifice"},
        ]
        mock_controller = Mock()
        manager = ElfManager(config=mock_config, controller=mock_controller)

        with pytest.raises(ValueError, match="配置中未找到 final 精灵"):
            _ = manager.final_elf
