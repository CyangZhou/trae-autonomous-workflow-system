---
name: autonomous-agent
description: 自主执行总调度器 v8.2。触发词：开始、继续、自主执行、autonomous、蜂群。
---

# Autonomous Agent v8.2 (精简版)

## 触发词

`开始` | `继续` | `自主执行` | `autonomous` | `蜂群` | `并行执行` | `swarm`

## 执行流程

**必须按顺序执行以下命令：**

### 1. 初始化
```bash
python .trae/skills/autonomous-agent/agent.py init
```

### 2. 任务解析
```bash
python .trae/skills/autonomous-agent/agent.py analyze "用户任务描述"
```
返回 JSON：`{"execution_mode": "swarm|single", "complexity": 1-10, "confidence": 0.0-1.0, "recommended_agents": [...], "subtasks": [...]}`

### 3. 执行模式选择
- **Swarm 模式** (complexity >= 6)：在一条消息中同时发起多个 Task 调用
- **Solo 模式** (complexity < 6)：顺序执行

### 4. 验证
```bash
python .trae/skills/autonomous-agent/agent.py validate
```

### 5. 记忆记录
```bash
python .trae/skills/autonomous-agent/agent.py save --session <session_id>
```

## 检查点

```
[检查点1] 初始化完成
[检查点2] 任务解析完成 - 目标: xxx, 复杂度: x
[检查点3] 执行模式选择 - 模式: Swarm/Solo
[检查点4] 验证完成
[检查点5] 记忆记录完成
```

## Swarm 并行规范

**正确**：一条消息中同时发起多个 Task
```
Task(subagent_type="search", description="...")
Task(subagent_type="backend-architect", description="...")
Task(subagent_type="testing-validation-expert", description="...")
```

**错误**：顺序调用（禁止）

## 智能体映射

| 任务类型 | 智能体 |
|---------|--------|
| web开发 | search, frontend-implementation-expert |
| 后端开发 | backend-architect, testing-validation-expert |
| 数据分析 | search, backend-architect |
| 量化交易 | alpha-picker, factor-validator |
| 内容创作 | priest-style-architect |
| 技能开发 | trae-skill-forge |

## Memory 记忆

- 写入：`.trae/memory/sessions/`, `.trae/memory/errors/`, `.trae/memory/tasks/`
- 索引：`.trae/memory/index.json`
- 读取：任务开始时读取相似任务笔记，错误时读取修复笔记
