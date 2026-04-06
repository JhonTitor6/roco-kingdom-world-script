from dataclasses import dataclass
from typing import Union, List

@dataclass
class EventConfig:
    """事件配置数据类

    Args:
        template: 模板路径（支持单字符串或字符串列表）
        region: 检测区域 (x0, y0, x1, y1)
        similarity: 相似度阈值
    """
    template: Union[str, List[str]]
    region: tuple[int, int, int, int]
    similarity: float = 0.8