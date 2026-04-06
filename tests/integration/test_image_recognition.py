"""图像识别集成测试

使用真实游戏截图测试模板匹配功能
"""
import pytest
import cv2
import numpy as np
from PIL import Image
from pathlib import Path


def imread_unicode(path: Path) -> np.ndarray:
    """解决中文路径问题"""
    img = Image.open(path)
    img = img.convert('RGB')
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def find_template(screenshot: np.ndarray, template_path: Path, similarity: float = 0.8) -> tuple:
    """在截图中查找模板"""
    template = cv2.imread(str(template_path))
    if template is None:
        return (-1, -1), 0.0

    result = cv2.matchTemplate(screenshot, template, cv2.TM_CCORR_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    if max_val >= similarity:
        h, w = template.shape[:2]
        center_x = max_loc[0] + w // 2
        center_y = max_loc[1] + h // 2
        return (center_x, center_y), max_val

    return (-1, -1), 0.0


@pytest.fixture
def project_root():
    """项目根目录"""
    return Path(__file__).parent.parent.parent


@pytest.fixture
def images_dir(project_root):
    """截图目录"""
    return project_root / "images"


@pytest.fixture
def templates_dir(project_root):
    """模板目录"""
    return project_root / "assets" / "templates"


@pytest.fixture
def screenshots(images_dir):
    """获取所有截图"""
    if not images_dir.exists():
        pytest.skip("截图目录不存在")
    return sorted(images_dir.glob("*.png"), key=lambda p: p.stat().st_mtime)


@pytest.fixture
def battle_templates(templates_dir):
    """获取战斗相关模板"""
    return {
        "start_challenge": templates_dir / "battle" / "start_challenge.png",
        "battle_end": templates_dir / "battle" / "battle_end.png",
        "retry": templates_dir / "battle" / "retry.png",
        "quit": templates_dir / "battle" / "quit.png",
    }


@pytest.fixture
def elf_templates(templates_dir):
    """获取精灵模板"""
    elves_dir = templates_dir / "elves"
    if not elves_dir.exists():
        return {}
    return {p.stem: p for p in elves_dir.glob("*.png")}


@pytest.fixture
def skill_templates(templates_dir):
    """获取技能模板"""
    skills_dir = templates_dir / "skills"
    if not skills_dir.exists():
        return {}
    return {p.stem: p for p in skills_dir.glob("*.png")}


class TestScreenshotsAndTemplates:
    """基础测试"""

    def test_screenshots_exist(self, screenshots):
        """测试截图是否存在"""
        assert len(screenshots) > 0, "没有找到截图文件"

    def test_templates_exist(self, templates_dir):
        """测试模板是否存在"""
        templates = list(templates_dir.rglob("*.png"))
        assert len(templates) > 0, "没有找到模板文件"


class TestBattleTemplates:
    """战斗相关模板测试"""

    def test_start_challenge_recognition(self, screenshots, battle_templates):
        """测试开始挑战按钮识别"""
        template = battle_templates.get("start_challenge")
        if not template or not template.exists():
            pytest.skip("start_challenge 模板不存在")

        found = False
        for screenshot in screenshots:
            sc_img = imread_unicode(screenshot)
            (x, y), sim = find_template(sc_img, template, similarity=0.8)
            if x != -1:
                assert 0 <= x <= 3000, f"x坐标异常: {x}"
                assert 0 <= y <= 2000, f"y坐标异常: {y}"
                found = True
                break

        assert found, "start_challenge 在所有截图中都未匹配"

    def test_retry_button_recognition(self, screenshots, battle_templates):
        """测试再次切磋按钮识别"""
        template = battle_templates.get("retry")
        if not template or not template.exists():
            pytest.skip("retry 模板不存在")

        found_count = 0
        for screenshot in screenshots:
            sc_img = imread_unicode(screenshot)
            (x, y), sim = find_template(sc_img, template, similarity=0.8)
            if x != -1:
                found_count += 1

        assert found_count > 0, "retry 在所有截图中都未匹配"


class TestElfTemplates:
    """精灵相关模板测试"""

    def test_elf_templates_exist(self, elf_templates):
        """测试精灵模板是否存在"""
        assert len(elf_templates) > 0, "没有找到精灵模板"

    def test_elf_templates_recognition(self, screenshots, elf_templates):
        """测试精灵模板识别"""
        for name, template in elf_templates.items():
            found = False
            for screenshot in screenshots:
                sc_img = imread_unicode(screenshot)
                (x, y), sim = find_template(sc_img, template, similarity=0.8)
                if x != -1:
                    found = True
                    break
            assert found, f"{name} 模板在所有截图中都未匹配"


class TestSkillTemplates:
    """技能相关模板测试"""

    def test_skill_templates_exist(self, skill_templates):
        """测试技能模板是否存在"""
        assert len(skill_templates) > 0, "没有找到技能模板"

    def test_comet_skill_recognition(self, screenshots, skill_templates):
        """测试彗星技能识别"""
        template = skill_templates.get("comet")
        if not template:
            pytest.skip("comet 模板不存在")

        found = False
        for screenshot in screenshots:
            sc_img = imread_unicode(screenshot)
            (x, y), sim = find_template(sc_img, template, similarity=0.8)
            if x != -1:
                found = True
                break

        assert found, "comet 在所有截图中都未匹配"

    def test_defense_skill_recognition(self, screenshots, skill_templates):
        """测试防御技能识别"""
        template = skill_templates.get("defense")
        if not template:
            pytest.skip("defense 模板不存在")

        found = False
        for screenshot in screenshots:
            sc_img = imread_unicode(screenshot)
            (x, y), sim = find_template(sc_img, template, similarity=0.8)
            if x != -1:
                found = True
                break

        assert found, "defense 在所有截图中都未匹配"


class TestBattleEndTemplate:
    """battle_end 模板测试"""

    def test_battle_end_recognition(self, project_root, templates_dir):
        """测试 battle_end 模板在指定截图中的识别效果"""
        screenshot_path = project_root / "images" / "洛克王国：世界   2026_4_6 14_43_05.png"
        if not screenshot_path.exists():
            pytest.skip(f"截图不存在: {screenshot_path}")

        template_path = templates_dir / "battle" / "battle_end.png"
        if not template_path.exists():
            pytest.skip(f"battle_end 模板不存在: {template_path}")

        # 加载截图和模板
        sc_img = imread_unicode(screenshot_path)
        template = cv2.imread(str(template_path))
        assert template is not None, f"无法加载模板: {template_path}"

        # 执行模板匹配
        result = cv2.matchTemplate(sc_img, template, cv2.TM_CCORR_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        h, w = template.shape[:2]
        center_x = max_loc[0] + w // 2
        center_y = max_loc[1] + h // 2

        print(f"\nbattle_end 识别结果:")
        print(f"  截图: {screenshot_path.name}")
        print(f"  模板尺寸: {w}x{h}")
        print(f"  匹配位置: ({center_x}, {center_y})")
        print(f"  相似度: {max_val:.4f}")

        assert max_val >= 0.6, f"相似度 {max_val:.4f} 低于阈值 0.6"
        assert 0 <= center_x <= sc_img.shape[1], f"x坐标异常: {center_x}"
        assert 0 <= center_y <= sc_img.shape[0], f"y坐标异常: {center_y}"


class TestPopupTemplates:
    """弹窗相关模板测试"""

    @pytest.fixture
    def popup_templates(self, templates_dir):
        """获取弹窗模板"""
        popup_dir = templates_dir / "popup"
        if not popup_dir.exists():
            return {}
        return {p.stem: p for p in popup_dir.glob("*.png")}

    def test_confirm_recognition(self, screenshots, popup_templates):
        """测试确认按钮识别"""
        template = popup_templates.get("confirm")
        if not template:
            pytest.skip("confirm 模板不存在")

        found = False
        for screenshot in screenshots:
            sc_img = imread_unicode(screenshot)
            (x, y), sim = find_template(sc_img, template, similarity=0.8)
            if x != -1:
                found = True
                break

        assert found, "confirm 在所有截图中都未匹配"
