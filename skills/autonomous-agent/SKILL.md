---
name: autonomous-agent
version: "1.0.0"
description: 云舒自主执行引擎，支持5场景决策树、3维度质量把关、Skill自动发现、交付文档生成。
tags: ["autonomous", "workflow", "orchestration", "swarm", "quality-gate"]
triggers:
  - 云舒
  - 开始
  - 继续
  - 自主执行
  - autonomous
  - 蜂群
priority: 100
---

# CloudShu Workflow v1.0 

## 1. Knowledge Layer (知识层)

### 1.1 核心定义
**Autonomous Agent Skill** 是 Trae 的核心执行引擎，负责将自然语言指令转化为完整的工程交付物。它集成了智能决策、多智能体编排 (Swarm)、质量门禁和自动交付系统。       

### 1.2 核心模块
- **Intelligence**: 任务分析与场景决策
- **Swarm**: 多智能体并行编排
- **Workflow**: 标准化流程执行
- **Quality Gate**: 真实验证 (Lint/Test)
- **Delivery**: 自动化文档生成
- **Memory**: 执行追踪与经验沉淀

### 1.3 架构映射 (Self-Awareness Map)
```
项目根目录/
├── .trae/                        # 核心配置 (只读/版本控制)
│   ├── rules/                    # 项目规则
│   └── skills/                   # 技能定义
│       └── autonomous-agent/     # 核心引擎
│           ├── agent.py          # [ENTRY] CLI 入口与命令分发
│           ├── skill.yaml        # [CONFIG] 技能定义与检查点
│           ├── SKILL.md          # [DOC] 技能文档
│           └── core/             # 核心模块
│               ├── kernel/       # [CORE] 统一内核 (Mixin架构)
│               ├── closed_loop/  # [LOOP] 闭环编排器
│               ├── ltm/          # [MEMORY] 长期记忆系统
│               ├── workers/      # [HANDS] 执行工人类
│               ├── paths.py      # [PATH] 路径解析模块
│               ├── knowledge_boundary.py  # [SENSE] 知识边界感知
│               ├── enhanced_reflexion.py  # [HEAL] 反思机制 (4层深度)
│               ├── enhanced_decomposer.py # [DECOMPOSE] 任务拆解
│               ├── quality_gate.py        # [GUARD] 质量门禁 (4维度)
│               ├── skill_discovery.py     # [DISCOVER] 技能发现 (自适应专精)
│               ├── intelligence.py        # [BRAIN] 任务分析与决策
│               ├── swarm.py               # [ORCHESTRATOR] 蜂群编排器
│               └── workflow.py            # [RUNNER] 线性工作流执行
│
└── 自动化工作流组件库/            # 运行时数据 (可修改)
    ├── config/                   # 配置文件
    │   └── skill-registry.json   # 技能注册表
    ├── memory/                   # 记忆存储 (ltm/sessions/tasks/errors/quality)
    ├── delivery/                 # 交付文档
    ├── knowledge/                # 知识库
    ├── workflows/                # 工作流定义
    ├── swarm/                    # Swarm配置 (agent_registry.json)
    ├── templates/                # 模板文件 (validation_scripts)
    └── logs/                     # 日志文件
```

### 1.4 组件交互拓扑
1. **User** -> `agent.py` (CLI)
2. `agent.py` -> `kernel/unified.py` (Kernel)
3. `kernel` -> `intelligence.py` (Analyze)
4. `kernel` -> `knowledge_boundary.py` (Sense)
5. `kernel` -> `closed_loop/orchestrator.py` (Orchestrate)
6. `orchestrator` -> `enhanced_decomposer.py` (Decompose)
7. `orchestrator` -> `swarm.py` (Execute Parallel)
8. `orchestrator` -> `quality_gate.py` (Validate)
9. `orchestrator` -> `ltm/manager.py` (Evolve)
10. `skill_discovery.py` -> `ltm/manager.py` (Adaptive Specialization)

---

## 2. Goal Layer (目标层)

### 2.1 输入期望
- **触发词**: `开始`, `继续`, `自主执行`, `autonomous`, `蜂群`
- **内容**: 明确的任务描述或模糊的需求意图。

### 2.2 输出标准
- **执行结果**: 完成所有代码变更、文件创建。
- **质量报告**: 通过所有预设的质量检查 (Quality Gate)。
- **交付文档**: 生成 `_delivery.md`，包含部署/验证说明。
- **记忆更新**: 将成功模式写入记忆库。
- **执行指令**: 返回结构化的 `execution_directive`，指导后续执行。

---

## 3. Behavior Layer (行为层)

### 3.1 核心能力
- ✅ **5场景决策树**: 自动选择 (提示增强 / Skill复用 / 计划+评审 / Lead-Member / 复合编排)
- ✅ **3维度质量把关**: 边界处理、专业度、完整性 (通过率 >= 70%)
- ✅ **Skill自动发现**: 本地Skill -> 内置Agent -> 通用流程
- ✅ **Swarm蜂群编排**: 支持复杂任务的并行拆解与执行
- ✅ **交付文档生成**: 自动生成部署说明、验证方法、后续建议
- ✅ **执行指令返回**: 返回结构化指令，指导 Agent 后续执行

### 3.2 执行逻辑 (Standard Process)
1. **Init**: 初始化内核与环境。
2. **Analyze**: 解析任务，生成执行计划。
3. **Decide**: 确定场景与所需技能。
4. **Execute**: 
   - **Solo**: 顺序执行。
   - **Swarm**: 并行编排。
5. **Quality**: 运行真实验证。
6. **Deliver**: 生成交付物。

### 3.3 执行指令类型 (Execution Directive Types)
当调用 `workflow` 命令时，返回的 `execution_directive` 包含以下类型：

| 类型 | 触发条件 | 返回内容 |
|:---|:---|:---|
| **swarm** | 复杂度 >= 6 | `subtasks` 列表，`session_id`，并行执行指令 |
| **workflow** | 匹配到工作流 | `workflow_name`，执行结果 |
| **plan** | 无匹配工作流 | `phases` 列表，顺序执行指令 |

---

## 4. Protocol Layer (协议层)

### 4.1 ⚡ 强制触发协议 (Trigger Protocol)
**检测到触发词时，必须立即执行，无例外：**
1. ⚡ **IMMEDIATELY** invoke this skill.
2. 🚫 **DO NOT** chat, explain, or plan.
3. 🚫 **DO NOT** wait for more context.
4. ✅ **JUST EXECUTE**.
5. 📤 **PARSE execution_directive** - 使用返回的指令继续执行。

### 4.2 🔄 强制连续执行协议 (Continuity Protocol)
**获得执行计划后：**
1. 🔄 **YOU MUST NOT STOP** - Continue executing until ALL steps are complete.
2. 🔄 **YOU MUST NOT WAIT** - Execute immediately without asking for confirmation.
3. 🔄 **YOU MUST PARSE OUTPUT** - Use previous step's output as next step's input.
4. 🔄 **YOU MUST COMPLETE ALL CHECKPOINTS**.
5. 🔄 **YOU MUST EXECUTE execution_directive** - 根据指令类型执行后续操作。

### 4.3 🔒 确认协议 (Confirmation Protocol)
> 遵循 `project_rules.md` 中的全局自主决策权定义。


### 4.4 🛠️ CLI 接口规范
```bash
# 1. 初始化 (MANDATORY)
python ./.trae/skills/autonomous-agent/agent.py init

# 2. 任务解析 (MANDATORY)
python ./.trae/skills/autonomous-agent/agent.py analyze "任务描述"

# 3. 完整工作流 (Optional Shortcut)
python ./.trae/skills/autonomous-agent/agent.py workflow "任务描述"

# 4. 获取执行指令 (NEW - 用于后续执行)
python ./.trae/skills/autonomous-agent/agent.py exec-directive --session <ID>

# 5. 质量检查 (MANDATORY)
python ./.trae/skills/autonomous-agent/agent.py quality --session <ID>

# 6. 交付与记忆 (MANDATORY)
python ./.trae/skills/autonomous-agent/agent.py delivery --session <ID>
python ./.trae/skills/autonomous-agent/agent.py save --session <ID>

# 辅助: 追踪工具调用
python ./.trae/skills/autonomous-agent/agent.py record-tools --session <ID>
```

### 4.5 📤 执行指令处理协议 (Execution Directive Protocol)
**当 `execution_directive` 返回时，必须按类型处理：**

#### Swarm 类型
```json
{
  "type": "swarm",
  "session_id": "xxx",
  "subtasks": [...],
  "instruction": "PARALLEL_EXECUTION_REQUIRED"
}
```
**处理方式**: 使用 Task 工具并行执行所有 subtasks。

#### Workflow 类型
```json
{
  "type": "workflow",
  "workflow_name": "xxx",
  "result": {...}
}
```
**处理方式**: 检查 result.status，成功则继续质量检查，失败则 fallback。

#### Plan 类型
```json
{
  "type": "plan",
  "phases": [...]
}
```
**处理方式**: 按顺序执行每个 phase。

---

## 5. Specification Layer (规范层)

### 5.1 失败判定
以下情况视为执行失败：
- ❌ 缺少任何检查点输出。
- ❌ 中途停止执行。
- ❌ 未调用 `quality` 和 `delivery`。
- ❌ Swarm模式下顺序调用Task（伪并行）。
- ❌ 未处理 `execution_directive`。

### 5.2 安全约束
- **文件操作**: 优先使用 `track-file` 记录变更。
- **环境隔离**: 测试应在隔离环境中运行 (如可能)。
- **Token限制**: 必须使用 `record-tools` 记录消耗。

### 5.3 开发规范 (Development Standards)
- **自我感知**: 任何功能变更必须同步更新 `SKILL.md` 的架构映射。
- **代码长度**: 
  - **Hard Limit**: 单个脚本文件严禁超过 500 行。
  - **Action**: 超过限制必须立即触发重构拆分。
  - **Reason**: 确保 LLM 上下文完整性和修改准确性。
- **模块化**: 功能实现应封装在 `core/` 下的独立模块，`agent.py` 仅作为轻量级入口。

### 5.4 版本信息
- **当前版本**: v1.0
- **更新日志**: 
  - v1.0: 初始版本，集成5场景决策树、3维度质量把关、Skill自动发现、交付文档生成。
