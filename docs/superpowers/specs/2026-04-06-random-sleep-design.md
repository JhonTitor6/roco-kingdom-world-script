# 随机延迟方法设计

## 背景

游戏中固定时间的 `time.sleep` 容易被检测为自动化脚本，需要在核心代码中将所有固定延迟改为随机延迟，防止封号。

## 方案

### 核心函数

在 `src/utils.py`（新建）中创建 `random_sleep(base: float)` 函数：

```python
import time
import random

def random_sleep(base: float) -> None:
    """随机休眠，基于中心值 ±0.5s 浮动，最小 0.05s"""
    offset = random.uniform(-0.5, 0.5)
    sleep_time = max(0.05, base + offset)
    time.sleep(sleep_time)
```

**关键点：**
- 最小休眠 0.05s，防止负值或零
- `random.uniform` 保证均匀分布
- 固定 ±0.5s 浮动范围，无需额外配置

### 涉及的修改文件

| 文件 | 修改内容 |
|------|---------|
| `src/utils.py` | 新建，存放 `random_sleep` 函数 |
| `src/controller.py` | `time.sleep(0.3)` → `random_sleep(0.3)` |
| `src/skill_executor.py` | 7 处 `time.sleep` → `random_sleep` |
| `src/state_machine.py` | `time.sleep(2)` → `random_sleep(2)` |
| `src/battle_flow.py` | 9 处 `time.sleep` → `random_sleep` |

### 导入方式

在需要使用的文件顶部添加：
```python
from src.utils import random_sleep
```

## 具体修改对照表

### src/controller.py
| 行号 | 原代码 | 修改后 |
|-----|-------|-------|
| 132 | `time.sleep(0.3)` | `random_sleep(0.3)` |
| 144 | `time.sleep(0.3)` | `random_sleep(0.3)` |

### src/skill_executor.py
| 行号 | 原代码 | 修改后 |
|-----|-------|-------|
| 39 | `time.sleep(3)` | `random_sleep(3)` |
| 44 | `time.sleep(1)` | `random_sleep(1)` |
| 48 | `time.sleep(wait_time)` | `random_sleep(wait_time)` |
| 50 | `time.sleep(1)` | `random_sleep(1)` |
| 58 | `time.sleep(1)` | `random_sleep(1)` |
| 64 | `time.sleep(wait_time)` | `random_sleep(wait_time)` |
| 73 | `time.sleep(8)` | `random_sleep(8)` |
| 96 | `time.sleep(2)` | `random_sleep(2)` |
| 105 | `time.sleep(2)` | `random_sleep(2)` |
| 117 | `time.sleep(0.5)` | `random_sleep(0.5)` |
| 119 | `time.sleep(0.05)` | `random_sleep(0.05)` |
| 123 | `time.sleep(switch_sleep)` | `random_sleep(switch_sleep)` |
| 143 | `time.sleep(0.3)` | `random_sleep(0.3)` |
| 189 | `time.sleep(0.2)` | `random_sleep(0.2)` |

### src/state_machine.py
| 行号 | 原代码 | 修改后 |
|-----|-------|-------|
| 53 | `time.sleep(2)` | `random_sleep(2)` |

### src/battle_flow.py
| 行号 | 原代码 | 修改后 |
|-----|-------|-------|
| 43 | `time.sleep(1)` | `random_sleep(1)` |
| 49 | `time.sleep(5)` | `random_sleep(5)` |
| 56 | `time.sleep(1)` | `random_sleep(1)` |
| 63 | `time.sleep(10)` | `random_sleep(10)` |
| 93 | `time.sleep(1)` | `random_sleep(1)` |
| 125 | `time.sleep(1)` | `random_sleep(1)` |
| 153 | `time.sleep(3)` | `random_sleep(3)` |
| 179 | `time.sleep(1)` | `random_sleep(1)` |
| 239 | `time.sleep(10)` | `random_sleep(10)` |

## 注意事项

- 保留 `import time` 以备其他用途（如性能测量）
- `time` 模块在 `random_sleep` 内部仍需要使用
- 不修改 `win_util` 库中的 sleep 调用，只修改 `src/` 下的业务代码
