import pytest
from abc import ABC


class MockDispatcher:
    """模拟 EventDispatcher"""
    def __init__(self):
        self.controller = None
        self.elf_manager = None
        self.skill_executor = None


class TestBaseHandler:
    """Handler 基类测试"""

    def test_handler_init(self):
        """验证 Handler 初始化"""
        from src.handlers.base_handler import Handler

        class ConcreteHandler(Handler):
            def handle(self, ctx):
                pass

        dispatcher = MockDispatcher()
        handler = ConcreteHandler(dispatcher)

        assert handler.dispatcher == dispatcher
        assert handler.ctrl == dispatcher.controller
        assert handler.elf_mgr == dispatcher.elf_manager
        assert handler.skill == dispatcher.skill_executor

    def test_handler_is_abc(self):
        """验证 Handler 继承自 ABC"""
        from src.handlers.base_handler import Handler

        assert issubclass(Handler, ABC)

    def test_handle_method_is_abstract(self):
        """验证 handle 方法是抽象的"""
        from src.handlers.base_handler import Handler

        with pytest.raises(TypeError):
            Handler(MockDispatcher())