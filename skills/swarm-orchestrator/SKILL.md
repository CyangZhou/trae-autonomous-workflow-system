# Swarm Orchestrator - 蜂群编排器

---
**版本**：1.0.0
---

## 📝 技能描述

蜂群编排器是 autonomous-agent 的核心组件，负责协调多个智能体并行执行复杂任务。

## 🎯 核心能力

| 能力 | 说明 |
|------|------|
| **蜂群会话管理** | 创建、监控、关闭蜂群执行会话 |
| **并行任务分发** | 将复杂任务拆分为可并行执行的子任务 |
| **结果聚合** | 收集所有子任务结果并生成汇总报告 |
| **错误恢复** | 自动检测失败任务并触发 Reflexion 修复 |
| **记忆集成** | 与 Memory 系统集成，记录执行经验 |

## 🚀 触发词

- `蜂群编排`
- `并行执行`
- `swarm orchestrator`
- `多智能体协调`
- `任务分发`

## 📋 使用示例

```python
from core.swarm import SwarmOrchestrator

orchestrator = SwarmOrchestrator()

# 创建蜂群会话
session_id = orchestrator.create_swarm_session(
    main_task="开发数据分析系统",
    subtasks=[
        {'type': 'search', 'role': 'researcher', 'goal': '调研技术方案'},
        {'type': 'backend-architect', 'role': 'coder', 'goal': '实现核心逻辑'},
        {'type': 'testing-validation-expert', 'role': 'tester', 'goal': '编写测试'}
    ]
)

# 获取并行子任务
parallel_tasks = orchestrator.get_parallel_subtasks(session_id)

# 聚合结果
results = orchestrator.aggregate_results(session_id)
```

## 🔗 依赖关系

- **autonomous-agent**: 核心调度器
- **memory**: 记忆系统
- **reflexion**: 反思进化模块
