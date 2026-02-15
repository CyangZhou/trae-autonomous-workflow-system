# Agent 执行核心指令 v8.2 (精简版)

## 强制规则

| 序号 | 规则 | 说明 |
|:---:|:-----|:-----|
| 1 | 触发词必须响应 | "开始/继续/蜂群/autonomous" → 调用 autonomous-agent |
| 2 | 禁止跳过步骤 | 必须执行全部 7 步骤 |
| 3 | 禁止伪并行 | Swarm 必须在一条消息中同时发起多个 Task |
| 4 | 必须调用 Python | 每个步骤必须执行对应 Python 命令 |
| 5 | 必须记录记忆 | 任务完成必须写入 .trae/memory/ |

## 执行协议

### 步骤 1：初始化
```bash
python .trae/skills/autonomous-agent/agent.py init
```

### 步骤 2：任务解析
```bash
python .trae/skills/autonomous-agent/agent.py analyze "任务描述"
```
输出：core_goal, complexity, confidence, recommended_agents, subtasks

### 步骤 3：智能推荐
根据步骤 2 输出的 recommended_workflows 和 recommended_skills 执行

### 步骤 4：执行模式选择
- complexity >= 6 → Swarm 并行模式
- complexity < 6 → Solo 单机模式

### 步骤 5：验证
```bash
python .trae/skills/autonomous-agent/agent.py validate
```

### 步骤 6：反思与记忆
```bash
python .trae/skills/autonomous-agent/agent.py reflect --error "错误信息"
python .trae/skills/autonomous-agent/agent.py record --fix "修复方案"
```

### 步骤 7：工作流沉淀
```bash
python .trae/skills/autonomous-agent/agent.py save --session <session_id>
```

## 检查点输出

```
[检查点1] 初始化完成
[检查点2] 任务解析完成 - 目标: xxx, 复杂度: x
[检查点3] 智能推荐完成 - 工作流: xxx
[检查点4] 执行模式选择 - 模式: Swarm/Solo
[检查点5] 验证完成
[检查点6] 反思与记忆完成 - 新增记忆: x
[检查点7] 工作流沉淀完成
```

## Swarm 并行规范

触发条件：complexity >= 6 或多文件修改

正确做法：一条消息中同时发起多个 Task 调用
```
Task(subagent_type="search", ...)
Task(subagent_type="backend-architect", ...)
Task(subagent_type="testing-validation-expert", ...)
```

## 智能体映射

| 任务类型 | 推荐智能体 |
|---------|-----------|
| web开发 | search, frontend-implementation-expert, testing-validation-expert |
| API开发 | architect-design-expert, backend-architect, testing-validation-expert |
| 数据分析 | search, backend-architect, frontend-implementation-expert |
| 量化交易 | alpha-picker, factor-validator, a-share-market-analyzer |
| 内容创作 | priest-style-architect, prompt-crafter |
| 技能开发 | trae-skill-forge, agent-forge-master |

## Memory 记忆系统

写入时机：
- TASK_START: 任务开始时
- ERROR_OCCURRED: 错误发生时
- ERROR_FIXED: 错误修复后
- TASK_COMPLETE: 任务完成时

读取时机：
- TASK_START: 继续任务时读取会话笔记
- ERROR_ENCOUNTERED: 遇到错误时读取修复笔记
