import random
from typing import TYPE_CHECKING, Optional

import win32api
import win32con
from loguru import logger

if TYPE_CHECKING:
    try:
        from tests.common.environment.base import GameEnvironment
    except ImportError:
        GameEnvironment = None  # type: ignore


class MouseController:
    """
    鼠标操作封装类，支持前台点击、后台点击及随机范围点击

    支持两种初始化模式：
    1. GameEnvironment 模式：传入 env 参数，使用环境抽象接口
    2. hwnd 模式（向后兼容）：传入 hwnd 参数，使用原生 win32 调用
    """

    def __init__(self, env: Optional['GameEnvironment'] = None, hwnd: Optional[int] = None):
        """
        初始化鼠标控制器

        :param env: GameEnvironment 实例，用于抽象接口调用
        :param hwnd: 窗口句柄，用于原生 win32 调用（向后兼容）
        """
        self._env = env
        self.hwnd = hwnd

    def bg_left_click(self, *point, x_range=0, y_range=0) -> bool:
        """
        后台模拟鼠标左键点击

        :param point: (x, y) 或 x, y
        :param x_range: x轴随机范围半径
        :param y_range: y轴随机范围半径
        :return: 点击是否成功
        """
        if point is None or (len(point) == 1 and point[0] is None):
            return False

        x, y = -1, -1
        if len(point) == 1 and isinstance(point[0], (tuple, list)):
            x, y = point[0][0], point[0][1]
        elif len(point) == 2:
            x, y = point

        if x < 0 or y < 0:
            return False

        x_pos = max(0, random.randint(x - x_range, x + x_range))
        y_pos = max(0, random.randint(y - y_range, y + y_range))

        if x_range >= 0 or y_range >= 0:
            logger.debug(f"在基准点 {point} 周围随机点击: x={x_pos}, y={y_pos}")

        # 优先使用 GameEnvironment 接口
        if self._env is not None:
            self._env.left_click(x_pos, y_pos)
            return True

        # 向后兼容：使用原生 win32 调用
        if self.hwnd is None:
            raise ValueError("请在初始化时传入 GameEnvironment 或目标窗口句柄用于后台点击")

        long_position = win32api.MAKELONG(x_pos, y_pos)
        win32api.SendMessage(self.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, long_position)
        win32api.SendMessage(self.hwnd, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, long_position)

        return True

    def bg_left_click_with_range(self, point, x_range=20, y_range=20) -> bool:
        """
        在指定点周围随机范围内后台左键点击

        :param point: 基准点坐标 (x, y)
        :param x_range: x轴随机范围半径
        :param y_range: y轴随机范围半径
        :return: 点击是否成功
        """
        return self.bg_left_click(point, x_range=x_range, y_range=y_range)

    def bg_swipe(self, start_x: int, start_y: int, end_x: int, end_y: int,
                 steps: int = 20, duration: float = 0.5,
                 curve_factor: float = 0.3) -> bool:
        """
        后台模拟鼠标滑动操作（贝塞尔曲线防封）

        :param start_x: 起始点 X 坐标
        :param start_y: 起始点 Y 坐标
        :param end_x: 结束点 X 坐标
        :param end_y: 结束点 Y 坐标
        :param steps: 滑动步数（越多越平滑）
        :param duration: 滑动总时长（秒）
        :param curve_factor: 曲线弯曲因子（0-1，越大越弯曲）
        :return: 操作是否成功
        """
        import time

        if self._env is not None:
            # 使用 GameEnvironment 接口的贝塞尔滑动
            points = self._generate_bezier_points(
                start_x, start_y, end_x, end_y,
                steps, curve_factor
            )
            for i, (x, y) in enumerate(points):
                self._env.left_click(int(x), int(y))
                if i < len(points) - 1:
                    # 渐变延迟：开始和结束稍慢，中间稍快
                    t = i / (len(points) - 1)
                    # 使用缓动函数使开始和结束更自然
                    if t < 0.2:
                        delay = duration * 0.08  # 开始稍慢
                    elif t > 0.8:
                        delay = duration * 0.06  # 结束稍慢
                    else:
                        delay = duration * 0.03  # 中间稍快
                    delay *= random.uniform(0.8, 1.2)  # 添加随机因子
                    time.sleep(delay)
            return True

        # 向后兼容：使用原生 win32 调用
        if self.hwnd is None:
            raise ValueError("请在初始化时传入 GameEnvironment 或目标窗口句柄")

        # 生成贝塞尔曲线点
        points = self._generate_bezier_points(
            start_x, start_y, end_x, end_y,
            steps, curve_factor
        )

        # 按下鼠标
        long_start = win32api.MAKELONG(int(points[0][0]), int(points[0][1]))
        win32api.SendMessage(self.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, long_start)

        # 沿贝塞尔曲线移动
        for i in range(1, len(points) - 1):
            x, y = points[i]
            long_current = win32api.MAKELONG(int(x), int(y))
            win32api.SendMessage(self.hwnd, win32con.WM_MOUSEMOVE, 0, long_current)

            # 缓动延迟
            t = i / (len(points) - 1)
            if t < 0.2:
                delay = duration * 0.08
            elif t > 0.8:
                delay = duration * 0.06
            else:
                delay = duration * 0.03
            delay *= random.uniform(0.8, 1.2)
            time.sleep(delay)

        # 释放鼠标
        end_x_final, end_y_final = points[-1]
        long_end = win32api.MAKELONG(int(end_x_final), int(end_y_final))
        win32api.SendMessage(self.hwnd, win32con.WM_LBUTTONUP, 0, long_end)

        return True

    def _generate_bezier_points(self, start_x: int, start_y: int,
                                 end_x: int, end_y: int,
                                 steps: int, curve_factor: float):
        """
        生成贝塞尔曲线路径点

        :param start_x: 起始点 X
        :param start_y: 起始点 Y
        :param end_x: 结束点 X
        :param end_y: 结束点 Y
        :param steps: 步数
        :param curve_factor: 曲线弯曲因子
        :return: [(x, y), ...] 点列表
        """
        # 计算方向向量
        dx = end_x - start_x
        dy = end_y - start_y

        # 生成随机偏移的偏移范围（基于滑动距离）
        offset_range = max(30, int((abs(dx) + abs(dy)) * curve_factor * 0.3))

        # 控制点1：起点 + 随机偏移
        ctrl1_x = start_x + dx * curve_factor + random.randint(-offset_range, offset_range)
        ctrl1_y = start_y + dy * curve_factor * random.uniform(-0.5, 0.5) + random.randint(-offset_range, offset_range)

        # 控制点2：终点 - 随机偏移
        ctrl2_x = end_x - dx * curve_factor + random.randint(-offset_range, offset_range)
        ctrl2_y = end_y - dy * curve_factor * random.uniform(-0.5, 0.5) + random.randint(-offset_range, offset_range)

        # 生成贝塞尔曲线点
        points = []
        for i in range(steps):
            t = i / (steps - 1) if steps > 1 else 1

            # 三次贝塞尔公式
            one_minus_t = 1 - t
            one_minus_t_sq = one_minus_t * one_minus_t
            one_minus_t_cube = one_minus_t_sq * one_minus_t
            t_sq = t * t
            t_cube = t_sq * t

            x = (one_minus_t_cube * start_x +
                 3 * one_minus_t_sq * t * ctrl1_x +
                 3 * one_minus_t * t_sq * ctrl2_x +
                 t_cube * end_x)

            y = (one_minus_t_cube * start_y +
                 3 * one_minus_t_sq * t * ctrl1_y +
                 3 * one_minus_t * t_sq * ctrl2_y +
                 t_cube * end_y)

            points.append((x, y))

        return points


def left_click(*position):
    """
    模拟鼠标左键点击（自动处理浮点数坐标）
    :param x: 点击的x坐标（支持int/float）
    :param y: 点击的y坐标（支持int/float）
    :param delay: 点击后的延迟时间(秒)
    """
    if position is None or (len(position) == 1 and position[0] is None):
        return False

    # 解析坐标参数
    if len(position) == 1 and isinstance(position[0], (tuple, list)):
        # 传入的是元组/列表形式 (x,y)
        x, y = position[0]
    elif len(position) == 2:
        # 传入的是x,y两个参数
        x, y = position
    else:
        raise ValueError("坐标参数格式错误，请使用(x,y)或x,y两种形式")

    # 确保坐标为整数
    x_pos = int(round(x))
    y_pos = int(round(y))

    win32api.SetCursorPos((x_pos, y_pos))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x_pos, y_pos, 0, 0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x_pos, y_pos, 0, 0)

    return True


def bg_left_click(hwnd, *point):
    """
        后台模拟鼠标左键点击

        支持两种传参方式：
        1. 传入x和y坐标：bg_left_click(hwnd, x, y)
        2. 传入坐标元组：bg_left_click(hwnd, (x, y))

        :param hwnd: 窗口句柄
        :param point: 坐标参数，可以是(x, y)或单独的x,y
        :return: 操作是否成功
        """
    if point is None or (len(point) == 1 and point[0] is None):
        return False

    # 解析坐标参数
    if len(point) == 1 and isinstance(point[0], (tuple, list)):
        # 传入的是元组/列表形式 (x,y)
        x, y = point[0]
    elif len(point) == 2:
        # 传入的是x,y两个参数
        x, y = point
    else:
        raise ValueError("坐标参数格式错误，请使用(x,y)或x,y两种形式")

    # 确保坐标为整数
    x_pos = int(round(x))
    y_pos = int(round(y))

    if x_pos < 0 or y_pos < 0:
        return False

    long_position = win32api.MAKELONG(x_pos, y_pos)  # 模拟鼠标指针 传送到指定坐标
    win32api.SendMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, long_position)  # 模拟鼠标按下
    win32api.SendMessage(hwnd, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, long_position)  # 模拟鼠标弹起

    return True


def bg_left_click_with_range(hwnd, point, x_range=20, y_range=20):
    """
    在指定点周围随机范围内左键点击

    参数:
        hwnd: 窗口句柄
        point: 基准点坐标 (x, y)
        range: 随机范围半径（默认10像素）
    """
    if point and point != (-1, -1):
        x = random.randint(point[0] - x_range, point[0] + x_range)
        y = random.randint(point[1] - y_range, point[1] + y_range)
        logger.debug(f"在基准点 {point} 周围随机点击: x={x}, y={y}")
        return bg_left_click(hwnd, x, y)
    return False