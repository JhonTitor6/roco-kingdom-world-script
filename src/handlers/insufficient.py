from src.handlers.base_handler import Handler
from src.context import GameContext
from src.events import Events
from src.registry import EventRegistry


class StartChallengeHandler(Handler):
    """开始挑战处理器"""

    def handle(self, ctx: GameContext) -> None:
        self.ctrl.find_and_click("popup/confirm.png")


EventRegistry.register(
    event=Events.START_CHALLENGE,
    handler_cls=StartChallengeHandler,
    template="popup/insufficient.png",
    region=(0, 0, 2560, 1440),
    similarity=0.8
)
