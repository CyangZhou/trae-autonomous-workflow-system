# Skill Manager - 技能管理器

---
**版本**：1.0.0
---

## 📝 技能描述

技能管理器负责安装、更新、卸载和管理 AI 技能。

## 🎯 核心能力

| 能力 | 说明 |
|------|------|
| **安装技能** | 从市场或本地安装技能 |
| **更新技能** | 检查并更新已安装技能 |
| **卸载技能** | 移除不需要的技能 |
| **列出技能** | 显示所有已安装技能 |

## 🚀 触发词

- `技能管理`
- `安装技能`
- `卸载技能`
- `skill manager`

## 📋 使用示例

```python
from skill_manager import SkillManager

manager = SkillManager()

# 列出已安装技能
skills = manager.list_installed()

# 安装技能
manager.install("new-skill")

# 卸载技能
manager.uninstall("old-skill")

# 更新技能
manager.update("existing-skill")
```

## 🔗 依赖关系

- **skill-registry.json**: 技能注册表
- **skill-market-hub**: 技能市场（用于下载）
