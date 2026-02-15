---
name: skill-matcher
version: "1.1.0"
description: 技能匹配器 v1.1 - 扫描可用技能、根据触发词匹配、支持优先级机制、返回推荐技能列表。被 intelligent-workflow-assistant 调用。
priority: 90
---

# Skill Matcher - 技能匹配器 v1.1

## 核心定位

**技能匹配引擎**：扫描 `.trae/skills/` 目录，根据任务描述匹配可用技能，返回推荐列表。

---

## 🚨 v1.1 核心升级

### 优先级机制

当多个技能匹配时，按以下规则决定优先级：

| 优先级 | 技能类型 | 说明 |
|:------:|:---------|:-----|
| **100** | `autonomous-agent` | 内核入口，强制最高优先级 |
| **90** | 系统级技能 | skill-matcher, neuro-bridge 等 |
| **70** | 领域专用技能 | 量化交易、内容创作等 |
| **50** | 通用技能 | 文档写作、格式优化等 |

### 强制触发规则

**当用户消息包含以下触发词时，必须强制调用 `autonomous-agent`：**

```python
KERNEL_TRIGGERS = [
    "开始", "继续", "自主执行", "自动规划", "autonomous",
    "agent执行", "蜂群", "并行执行", "swarm"
]

def check_kernel_trigger(user_message):
    """检查是否触发内核"""
    for trigger in KERNEL_TRIGGERS:
        if trigger in user_message.lower():
            return True, "autonomous-agent"
    return False, None
```

---

## 执行协议

### 步骤 1：检查内核触发（强制）

```python
def check_kernel_trigger(user_message):
    KERNEL_TRIGGERS = [
        "开始", "继续", "自主执行", "自动规划", "autonomous",
        "agent执行", "蜂群", "并行执行", "swarm"
    ]
    
    for trigger in KERNEL_TRIGGERS:
        if trigger in user_message.lower():
            return {
                "kernel_triggered": True,
                "skill": "autonomous-agent",
                "priority": 100,
                "reason": f"触发词 '{trigger}' 匹配内核入口"
            }
    
    return {"kernel_triggered": False}
```

### 步骤 2：扫描可用技能

```python
import os
import re
import json
import yaml
from pathlib import Path

def scan_skills():
    skills_dir = Path('.trae/skills')
    skills = []
    
    if skills_dir.exists():
        for skill_folder in skills_dir.iterdir():
            if skill_folder.is_dir():
                skill_file = skill_folder / 'SKILL.md'
                if skill_file.exists():
                    content = skill_file.read_text(encoding='utf-8')
                    
                    skill_info = {
                        'name': skill_folder.name,
                        'path': str(skill_folder),
                        'triggers': [],
                        'description': '',
                        'capabilities': [],
                        'priority': 50  # 默认优先级
                    }
                    
                    # 解析 YAML frontmatter
                    if content.startswith('---'):
                        parts = content.split('---', 2)
                        if len(parts) >= 3:
                            try:
                                fm = yaml.safe_load(parts[1])
                                skill_info['description'] = fm.get('description', '')
                                skill_info['priority'] = fm.get('priority', 50)
                                if 'triggers' in fm:
                                    skill_info['triggers'] = fm['triggers']
                            except:
                                pass
                    
                    # 如果 frontmatter 没有触发词，从内容提取
                    if not skill_info['triggers']:
                        trigger_patterns = [
                            r'触发词[：:]\s*([^\n]+)',
                            r'trigger[s]?:\s*\[([^\]]+)\]',
                        ]
                        
                        for pattern in trigger_patterns:
                            matches = re.findall(pattern, content, re.IGNORECASE)
                            for m in matches:
                                triggers = [t.strip().strip('"\'') for t in re.split(r'[,、，]', m)]
                                skill_info['triggers'].extend(triggers)
                    
                    skill_info['triggers'] = list(set(skill_info['triggers']))
                    skills.append(skill_info)
    
    return skills
```

### 步骤 3：匹配技能（带优先级）

```python
def match_skills(task_description, skills, context=None):
    matched = []
    task_lower = task_description.lower()
    
    for skill in skills:
        score = 0
        matched_triggers = []
        
        # 1. 触发词匹配
        for trigger in skill.get('triggers', []):
            if trigger.lower() in task_lower:
                score += 40
                matched_triggers.append(trigger)
        
        # 2. 能力匹配
        for cap in skill.get('capabilities', []):
            if cap.lower() in task_lower:
                score += 20
        
        # 3. 描述关键词匹配
        desc = skill.get('description', '').lower()
        task_words = set(task_lower.split())
        desc_words = set(desc.split())
        overlap = task_words & desc_words
        score += len(overlap) * 5
        
        # 4. 加上技能自身优先级
        priority = skill.get('priority', 50)
        final_score = score + priority
        
        if score >= 20:
            matched.append({
                'name': skill['name'],
                'score': score,
                'priority_score': priority,
                'final_score': final_score,
                'matched_triggers': matched_triggers,
                'capabilities': skill.get('capabilities', []),
                'description': skill.get('description', '')[:100],
                'priority_level': 'high' if final_score >= 100 else 'medium' if final_score >= 70 else 'low'
            })
    
    # 按最终分数排序
    return sorted(matched, key=lambda x: x['final_score'], reverse=True)
```

### 步骤 4：返回结果

```json
{
  "kernel_triggered": false,
  "matched_skills": [
    {
      "name": "skill-name",
      "score": 80,
      "priority_score": 50,
      "final_score": 130,
      "priority_level": "high",
      "matched_triggers": ["触发词1", "触发词2"],
      "capabilities": ["能力1", "能力2"],
      "description": "技能描述..."
    }
  ],
  "total_available": 8,
  "match_count": 3
}
```

---

## 匹配规则

| 匹配类型 | 权重 | 说明 |
|---------|------|------|
| 触发词完全匹配 | 40分 | 任务描述包含技能触发词 |
| 能力标签匹配 | 20分 | 任务描述包含能力关键词 |
| 描述关键词重叠 | 5分/词 | 任务描述与技能描述重叠词 |
| 技能优先级 | 0-100分 | 技能自身定义的优先级 |

**匹配阈值**：分数 >= 20 才会返回

---

## 强制规则

1. **必须先检查内核触发**：在匹配其他技能前，先检查是否触发 `autonomous-agent`
2. **必须扫描所有技能**：不能遗漏任何 SKILL.md 文件
3. **必须返回 JSON 格式**：方便调用方解析
4. **分数必须准确**：按照权重规则计算
5. **优先级必须正确**：final_score = match_score + priority_score
6. **内核触发词不可被覆盖**：KERNEL_TRIGGERS 中的触发词强制触发 autonomous-agent
