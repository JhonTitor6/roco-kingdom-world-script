# 彗星技能与防御/聚能交替实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现技能释放后统一步骤、防御/聚能交替逻辑

**Architecture:** SkillExecutor 负责技能执行和等待时间配置；ElfManager 移除 final_action 相关代码；battle_flow 使用新的防御/聚能尝试逻辑

**Tech Stack:** Python 3.x / win_util / JSON 配置

---

## File Structure

```
roco-kingdom-world-script/
├── src/
│   ├── skill_executor.py    # cast_skill 增加 timeout 参数和等待
│   ├── elf_manager.py       # 删除 final_action 相关代码
│   └── battle_flow.py       # 修改流程使用新的防御/聚能逻辑
├── config/
│   ├── settings.json        # 增加 skill_wait_after_cast
│   └── elves.json           # 删除 final_action
```

---

## Task 1: 修改 SkillExecutor.cast_skill

**Files:**
- Modify: `src/skill_executor.py:14-39`

- [ ] **Step 1: 修改 cast_skill 方法签名和实现**

```python
def cast_skill(self, skill_name: str, timeout: float = 5) -> bool:
    """释放技能（通过识图点击技能栏）

    Args:
        skill_name: 技能名 (comet / defense)
        timeout: 查找技能图标的超时时间（秒）

    Returns:
        是否成功
    """
    template_map = {
        "comet": "skills/comet.png",
        "defense": "skills/defense.png",
    }
    template = template_map.get(skill_name)
    if not template:
        logger.error(f"未知技能: {skill_name}")
        return False

    pos = self.ctrl.find_image_with_timeout(template, timeout=timeout, similarity=0.8)
    if pos is None:
        logger.warning(f"技能图标未找到: {skill_name}")
        return False

    self.ctrl.click_at(*pos)
    logger.info(f"释放技能: {skill_name}")

    # 技能释放后等待（可配置）
    wait_time = self.ctrl.settings.get("skill_wait_after_cast", 10)
    time.sleep(wait_time)
    return True
```

**说明:**
- `timeout` 参数传递给 `find_image_with_timeout`，用于检测图标是否出现
- `pos is None` 是关键判断（不是 `== (-1, -1)`）
- 技能释放后自动等待 `skill_wait_after_cast` 秒
- 默认 timeout=5 秒，默认等待 10 秒

- [ ] **Step 2: 确认 SkillExecutor 导入 time 模块**

检查文件顶部是否有 `import time`，如果没有则添加。

- [ ] **Step 3: Commit**

```bash
git add src/skill_executor.py
git commit -m "feat(skill_executor): cast_skill增加timeout参数和技能后等待"
```

---

## Task 2: 修改 ElfManager

**Files:**
- Modify: `src/elf_manager.py`

- [ ] **Step 1: 删除 final_action 属性**

在 `__init__` 方法中删除：
```python
self.final_action = config.get("final_action", "energy")
```

- [ ] **Step 2: 删除 get_final_action 方法**

删除整个方法（113-115行）：
```python
def get_final_action(self) -> str:
    """获取最后精灵的动作"""
    return self.final_action
```

- [ ] **Step 3: Commit**

```bash
git add src/elf_manager.py
git commit -m "feat(elf_manager): 删除final_action相关代码"
```

---

## Task 3: 修改 battle_flow.py

**Files:**
- Modify: `src/battle_flow.py`

### 3.1 faster_flow 修改

- [ ] **Step 1: 修改 faster_flow 方法（第 151-180 行）**

将第 174-179 行：
```python
action = self.elf_mgr.get_final_action()
if action == "energy":
    self.skill.press_energy()
else:
    self.skill.cast_skill("defense")
```

替换为：
```python
# 尝试释放防御（图标亮=可释放），如果失败（冷却中）则聚能
if not self.skill.cast_skill("defense", timeout=1):
    self.skill.press_energy()
```

### 3.2 slower_flow 修改

- [ ] **Step 2: 修改 slower_flow 方法（第 181-214 行）**

将第 186-191 行：
```python
action = self.elf_mgr.get_final_action()
if action == "energy":
    self.skill.press_energy()
else:
    self.skill.cast_skill("defense")
```

替换为：
```python
# 尝试释放防御（图标亮=可释放），如果失败（冷却中）则聚能
if not self.skill.cast_skill("defense", timeout=1):
    self.skill.press_energy()
```

### 3.3 sacrifice_sequence 修改

- [ ] **Step 3: 修改 sacrifice_sequence 方法（第 130-150 行）**

将第 144-149 行：
```python
action = self.elf_mgr.get_final_action()
if action == "energy":
    self.skill.press_energy()
else:
    self.skill.cast_skill("defense")
```

替换为：
```python
# 尝试释放防御，如果失败则聚能
if not self.skill.cast_skill("defense", timeout=1):
    self.skill.press_energy()
```

- [ ] **Step 4: Commit**

```bash
git add src/battle_flow.py
git commit -m "feat(battle_flow): 使用新的防御/聚能尝试逻辑"
```

---

## Task 4: 修改配置文件

### 4.1 settings.json

**Files:**
- Modify: `config/settings.json`

- [ ] **Step 1: 添加 skill_wait_after_cast 配置项**

在根层级添加（与 `similarity` 同级）：
```json
{
  "similarity": 0.6,
  "skill_wait_after_cast": 10,
  "timeouts": {
    ...
  }
}
```

### 4.2 elves.json

**Files:**
- Modify: `config/elves.json`

- [ ] **Step 2: 删除 final_action 字段**

删除第 8 行：
```json
"final_action": "energy"
```

- [ ] **Step 3: Commit**

```bash
git add config/settings.json config/elves.json
git commit -m "feat(config): 添加skill_wait_after_cast，删除final_action"
```

---

## Task 5: 验证

- [ ] **Step 1: 运行语法检查**

```bash
python -m py_compile src/skill_executor.py src/elf_manager.py src/battle_flow.py
```

- [ ] **Step 2: 运行测试（如果有）**

```bash
pytest tests/ -v
```

- [ ] **Step 3: 检查 git status**

```bash
git status
git diff --stat
```

---

## Summary

| Task | Files | Changes |
|------|-------|---------|
| 1 | skill_executor.py | cast_skill 增加 timeout 参数和 skill_wait_after_cast 等待 |
| 2 | elf_manager.py | 删除 final_action 属性和 get_final_action() 方法 |
| 3 | battle_flow.py | faster_flow, slower_flow, sacrifice_sequence 使用新逻辑 |
| 4 | settings.json, elves.json | 添加 skill_wait_after_cast，删除 final_action |
