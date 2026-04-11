from dataclasses import dataclass
from typing import Union, List, Optional

@dataclass
class EventConfig:
    """事件配置数据类

    Args:
        template: 模板路径（支持单字符串或字符串列表）
        region: 检测区域 (x0, y0, x1, y1)
        similarity: 相似度阈值
        priority: 优先级，数值越小越先处理，默认 None（最低优先级）
    """
    template: Union[str, List[str]]
    region: tuple[int, int, int, int]
    similarity: float = 0.8
    priority: Optional[int] = None