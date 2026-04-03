"""共享 fixtures"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import cv2
import numpy as np
from PIL import Image


@pytest.fixture
def project_root():
    """项目根目录"""
    return Path(__file__).parent.parent


@pytest.fixture
def templates_dir(project_root):
    """模板目录"""
    return project_root / "assets" / "templates"


@pytest.fixture
def images_dir(project_root):
    """截图目录"""
    return project_root / "images"


@pytest.fixture
def screenshots(project_root):
    """获取所有截图"""
    img_dir = project_root / "images"
    if not img_dir.exists():
        return []
    return sorted(img_dir.glob("*.png"), key=lambda p: p.stat().st_mtime)


def imread_unicode(path: Path) -> np.ndarray:
    """解决中文路径问题"""
    img = Image.open(path)
    img = img.convert('RGB')
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


@pytest.fixture
def load_screenshot(screenshots):
    """加载截图的辅助函数"""
    def _load(path: Path):
        return imread_unicode(path)
    return _load


@pytest.fixture
def load_template():
    """加载模板的辅助函数"""
    def _load(path: Path):
        return cv2.imread(str(path))
    return _load
