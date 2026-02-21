---
name: workflow-repair
version: "1.0.0"
description: 自动维修工作流引擎，支持组件扫描、调用验证、规则同步、维修报告生成。
tags: ["repair", "maintenance", "validation", "sync", "self-healing"]
triggers:
  - 维修工作流
  - 同步规则
  - 检测组件
  - 验证依赖
  - 扫描组件
  - repair workflow
negative_triggers:
  - 查看.*维修
  - list.*repair
priority: 40
---

# Workflow Repair Engine

## 核心功能

自动维修工作流引擎，确保自动化工作流系统的完整性和一致性。

### 四大核心模块

| 模块 | 职责 | 输出 |
|:---:|:---|:---|
| **ComponentScanner** | 发现并记录所有工作流组件 | 组件清单 |
| **DependencyValidator** | 验证组件间调用关系 | 问题列表 |
| **RulesSynchronizer** | 同步代码变更到规则文档 | 变更摘要 |
| **RepairReportGenerator** | 生成结构化维修报告 | MD + JSON |

### 扫描范围

```
autonomous-agent/
├── agent.py              # 入口文件
└── core/*.py             # 核心模块

.trae/skills/*/           # 所有技能目录
.trae/workflows/*.yaml    # 所有工作流模板
project_rules.md          # 项目规则
skill-registry.json       # 技能注册表
agent_registry.json       # 智能体注册表
```

### 执行模式

| 触发词 | 执行模式 | 包含步骤 |
|:---:|:---|:---|
| 扫描组件 | scan | 扫描 → 报告 |
| 验证依赖 | validate | 扫描 → 验证 → 报告 |
| 同步规则 | sync | 扫描 → 同步 → 报告 |
| 维修工作流 | full | 扫描 → 验证 → 同步 → 报告 |

---

## 执行协议

### 标准流程 (8步)

**Step 1: 初始化**
- 加载 known_components.json
- 创建维修会话 ID
- 初始化报告结构

**Step 2: 组件扫描**
- 遍历所有目标目录
- 提取组件元数据
- 比对已知组件列表

**Step 3: 依赖验证**
- 解析所有 import 语句
- 验证导入路径有效性
- 检查 __init__.py 导出

**Step 4: 规则同步**
- 读取当前 project_rules.md
- 检测版本和结构变化
- 生成更新内容

**Step 5: 问题分类**
- 区分 ERROR 和 WARNING
- 标记可自动修复项
- 生成修复建议

**Step 6: 报告生成**
- 生成 Markdown 报告
- 生成 JSON 报告
- 保存到 repair_reports/

**Step 7: 状态更新**
- 更新 known_components.json
- 记录维修历史
- 更新组件状态

**Step 8: 结果输出**
- 输出检查点摘要
- 列出关键发现
- 提供后续建议

### 检查点输出

```
[检查点1] ✅ 扫描完成 - 扫描了 X 个组件，发现 Y 个新增
[检查点2] ✅ 验证完成 - 发现 X 个问题 (Y 个 ERROR, Z 个 WARNING)
[检查点3] ✅ 同步完成 - 规则已更新，变更项：A, B, C
[检查点4] ✅ 报告生成 - 保存至 .trae/memory/repair_reports/
```

### CLI 命令

```bash
python ./.trae/skills/autonomous-agent/agent.py repair scan      # 扫描所有组件
python ./.trae/skills/autonomous-agent/agent.py repair validate  # 验证调用关系
python ./.trae/skills/autonomous-agent/agent.py repair detect-new # 检测新增组件
python ./.trae/skills/autonomous-agent/agent.py repair sync      # 同步项目规则
python ./.trae/skills/autonomous-agent/agent.py repair full      # 执行完整维修
```

### 安全约束

| 约束类型 | 说明 |
|:---:|:---|
| **禁止删除** | 维修操作不删除任何文件或目录 |
| **禁止修改代码** | 不修改用户代码逻辑 |
| **只读报告** | 仅生成报告，不自动修复代码 |
| **幂等性** | 多次执行结果一致，可安全重复运行 |

### 交付物

```
.trae/memory/repair_reports/
├── repair_YYYYMMDD_HHMMSS.md    # 人类可读报告
└── repair_YYYYMMDD_HHMMSS.json  # 机器可读报告
```

**报告内容**：
- 扫描结果：组件数量、类型分布
- 验证结果：问题列表、可修复项
- 同步结果：规则变更摘要
- 建议操作：手动修复指引
