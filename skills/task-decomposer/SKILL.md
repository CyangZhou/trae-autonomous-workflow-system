---
name: task-decomposer
version: "2.0.0"
description: 增强版原子级任务拆解，自动生成执行计划、任务列表及依赖关系。
tags: ["decomposition", "planning", "tasks", "atomic"]
triggers:
  - 任务拆解
  - 拆分任务
  - 分解任务
  - task decompose
priority: 65
---

# Task Decomposer Skill

**Description:** 
基于增强版任务拆解算法 (Enhanced Atomic Task Decomposer v2.0)，根据任务描述自动生成执行计划。整合了知识边界感知、长期记忆检索和自适应策略。

## Usage

### CLI
```bash
python .trae/skills/task-decomposer/main.py "Your task description here"
```

### Options
- `task_description`: 任务描述 (Required)
- `--output-dir`: 任务文档保存目录 (Optional)
- `--session-id`: 指定会话ID (Optional)

### Example
```bash
python .trae/skills/task-decomposer/main.py "为项目添加用户认证模块"
```

## Output
JSON string containing:
- session_id
- total_tasks
- execution_order
- decomposition_strategy
- tasks (list of tasks with id, name, description, agent_type, dependencies)
