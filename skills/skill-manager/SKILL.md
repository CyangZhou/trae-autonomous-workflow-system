---
name: skill-manager
version: "1.0.0"
description: 技能管理器，负责安装、更新、卸载和管理 AI 技能。
tags: ["skill", "management", "install", "uninstall", "update"]
triggers:
  - 技能管理
  - 安装技能
  - 卸载技能
  - skill manager
priority: 80
---

# Skill Manager - 技能管理器

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

## 📋 使用示例 (相对路径)

### 命令行工具

#### 1. 列出已安装技能
```bash
python ./.trae/skills/skill-manager/skill_manager.py list
```

#### 2. 扫描本地技能
```bash
python ./.trae/skills/skill-manager/skill_manager.py scan
```

#### 3. 搜索技能
```bash
python ./.trae/skills/skill-manager/skill_manager.py search "pdf"
```

#### 4. 安装技能
```bash
# 从本地源安装
python ./.trae/skills/skill-manager/skill_manager.py install <skill-name>

# 从 GitHub 安装
python ./.trae/skills/skill-manager/skill_manager.py install browser-use --source github --repo https://github.com/browser-use/browser-use
```

#### 5. 更新技能
```bash
python ./.trae/skills/skill-manager/skill_manager.py update neuro-bridge
```

#### 6. 卸载技能
```bash
python ./.trae/skills/skill-manager/skill_manager.py uninstall <skill-name>
```

### Python API

```python
# 确保添加到路径
import sys
from pathlib import Path
sys.path.append(str(Path('.trae/skills/skill-manager').resolve()))

from skill_manager import SkillManager

manager = SkillManager()

# 列出已安装技能
skills = manager.list_skills()

# 安装技能
manager.install_skill("new-skill")

# 卸载技能
manager.uninstall_skill("old-skill")

# 更新技能
manager.update_skill("existing-skill")
```

## 🔗 依赖关系

- **skill-registry.json**: 技能注册表
- **skill-market-hub**: 技能市场（用于下载）
