# Intelligent Workflow Assistant - 智能工作流助手

---
**版本**：1.0.0
---

## 📝 技能描述

智能工作流助手是 autonomous-agent 的 Intelligence 模块，负责分析用户任务并推荐最佳执行方案。

## 🎯 核心能力

| 能力 | 说明 |
|------|------|
| **任务解析** | 分析用户输入，提取核心目标和技术领域 |
| **复杂度评估** | 评估任务复杂度（1-10分），决定执行模式 |
| **工作流推荐** | 从工作流库中推荐最佳实践工作流 |
| **技能匹配** | 根据任务类型匹配合适的技能 |
| **智能体推荐** | 推荐最适合执行任务的智能体组合 |

## 🚀 触发词

- `智能工作流`
- `工作流推荐`
- `帮我看看项目`
- `检查项目`
- `workflow assistant`

## 📋 使用示例

```python
from core.intelligence import IntelligentAssistant

assistant = IntelligentAssistant()

# 分析任务
analysis = assistant.analyze("帮我开发一个用户认证系统")

# 返回结果
# {
#     'core_goal': '开发用户认证系统',
#     'complexity': 7,
#     'execution_mode': 'swarm',
#     'confidence': 0.85,
#     'recommended_agents': ['backend-architect', 'testing-validation-expert'],
#     'recommended_workflow': 'security-scan.yaml',
#     'recommended_skills': ['autonomous-agent']
# }
```

## 🔗 依赖关系

- **autonomous-agent**: 核心调度器
- **swarm-orchestrator**: 蜂群编排器
