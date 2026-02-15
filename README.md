# Trae Autonomous Workflow System

> 🚀 企业级自动化工作流系统 - 支持蜂群并行执行、智能路由、自愈机制

## 📋 系统架构

```
.trae/
├── skills/                    # 技能模块
│   ├── autonomous-agent/      # 自主执行核心 (v8.2)
│   │   ├── agent.py          # 统一内核入口
│   │   ├── core/
│   │   │   ├── intelligence.py  # 智能分析引擎
│   │   │   ├── swarm.py         # 蜂群编排器
│   │   │   ├── memory.py        # 记忆系统
│   │   │   ├── reflexion.py     # 反思引擎
│   │   │   └── workflow.py      # 工作流运行器
│   │   └── skill.yaml
│   ├── feishu-doc-master/     # 飞书文档大师
│   ├── neuro-bridge/          # 本地系统桥接
│   ├── skill-manager/         # 技能管理器
│   ├── workflow-market/       # 工作流市场
│   └── ...
├── workflows/                 # 工作流定义 (60+)
│   ├── workflow_manager_v2.py # 自验证闭环工作流管理器
│   ├── smart_router.py        # 智能路由器
│   └── *.yaml                 # 各类工作流配置
├── swarm/                     # 蜂群系统
│   ├── agent_registry.json    # 智能体注册表
│   └── swarm_core.db          # 任务数据库
├── memory/                    # 记忆系统
│   ├── sessions/              # 会话记忆
│   ├── errors/                # 错误修复记忆
│   ├── tasks/                 # 任务记忆
│   └── index.json             # 记忆索引
├── knowledge/                 # 知识库
└── rules/                     # 项目规则
```

## 🧠 核心组件

### 1. Autonomous Agent v8.2 (自主执行层)

**核心能力:**
- 智能任务分析 (复杂度评估、执行模式选择)
- 蜂群并行执行 (Swarm模式)
- 记忆系统 (错误修复、任务经验)
- 反思进化 (Reflexion Loop)

**使用方式:**
```bash
# 初始化
python .trae/skills/autonomous-agent/agent.py init

# 任务分析
python .trae/skills/autonomous-agent/agent.py analyze "你的任务描述"

# 验证
python .trae/skills/autonomous-agent/agent.py validate

# 保存记忆
python .trae/skills/autonomous-agent/agent.py save --session <session_id>
```

### 2. Workflow Manager V2 (工作流管理器)

**核心能力:**
- YAML工作流定义
- 自验证闭环
- 自愈机制
- 变量替换

**使用方式:**
```bash
# 列出工作流
python .trae/workflows/workflow_manager_v2.py list

# 执行工作流
python .trae/workflows/workflow_manager_v2.py run <workflow_name>

# 验证工作流
python .trae/workflows/workflow_manager_v2.py validate <workflow_name>
```

### 3. Swarm Orchestrator (蜂群编排器)

**核心能力:**
- SQLite任务队列
- 并行子任务分发
- 结果聚合
- 状态追踪

### 4. Memory System (记忆系统)

**记忆类型:**
- `sessions/` - 会话记忆
- `errors/` - 错误修复记忆
- `tasks/` - 任务经验记忆
- `global/` - 全局知识

## 🤖 智能体映射

| 任务类型 | 推荐智能体 |
|---------|-----------|
| Web开发 | search, frontend-implementation-expert, testing-validation-expert |
| API开发 | api-specification-expert, backend-architect, testing-validation-expert |
| 数据分析 | search, backend-architect, frontend-implementation-expert |
| 量化交易 | alpha-picker, factor-validator, a-share-market-analyzer, stock-ranker |
| 内容创作 | priest-style-architect, prompt-crafter |
| 技能开发 | trae-skill-forge, agent-forge-master |
| DevOps | release-ops-expert, performance-diagnostic-expert |

## 📦 工作流列表 (60+)

### 开发类
- `python-ci-local.yaml` - Python CI
- `code-review.yaml` - 代码审查
- `code-refactor.yaml` - 代码重构
- `test-automation.yaml` - 测试自动化

### 部署类
- `docker-build-local.yaml` - Docker构建
- `security-scan-local.yaml` - 安全扫描
- `release-notes.yaml` - 发布说明

### 自动化类
- `email-automation.yaml` - 邮件自动化
- `invoice-processing.yaml` - 发票处理
- `meeting-minutes-auto.yaml` - 会议纪要

### 分析类
- `log-anomaly-detection.yaml` - 日志异常检测
- `performance-benchmark.yaml` - 性能基准
- `data-processing.yaml` - 数据处理

## 🔧 配置说明

### skill.yaml 结构

```yaml
name: skill-name
version: "1.0.0"
description: 技能描述

triggers:
  - "触发词1"
  - "触发词2"

category: "automation"
tags:
  - "tag1"
  - "tag2"

# 检查点配置
checkpoints:
  enabled: true
  mandatory: true
  
# 蜂群配置
swarm:
  enabled: true
  trigger_conditions:
    min_complexity: 6
```

### workflow.yaml 结构

```yaml
name: workflow-name
description: 工作流描述
version: "1.0.0"

steps:
  - id: 1
    name: "步骤名称"
    action: "run_command"
    params:
      command: "echo 'Hello'"
    
  - id: 2
    name: "验证步骤"
    action: "verify"
    type: "file_exists"
    path: "/path/to/file"
```

## 🚀 快速开始

1. **克隆仓库**
```bash
git clone https://github.com/your-username/trae-workflow-system.git
cd trae-workflow-system
```

2. **初始化系统**
```bash
python .trae/skills/autonomous-agent/agent.py init
```

3. **执行任务**
```bash
python .trae/skills/autonomous-agent/agent.py analyze "创建一个Web应用"
```

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！
