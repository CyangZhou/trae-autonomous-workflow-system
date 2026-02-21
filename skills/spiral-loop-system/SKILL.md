---
name: spiral-loop-system
version: "1.0.0"
description: 螺旋循环重构系统，提供三层记忆、检查点管理、循环检测与跳跃、规范检查。
tags: ["memory", "checkpoint", "solver", "specs", "loop-detection"]
triggers:
  - 检查点
  - 循环检测
  - 螺旋
  - 规范检查
  - checkpoint
priority: 55
---

# Spiral Loop System (国学系统)

## 1. Knowledge Layer (知识层)

### 1.1 核心定义
**Spiral Loop System** 是基于复杂系统理论的工程化实现，旨在解决 LLM 任务执行中的“线性循环困境”，通过螺旋上升算法实现目标的精确性。它包含记忆、检查点、求解器和规范检查四大原子能力。

### 1.2 核心模块 (Atomic Skills)
- **Memory**: 三层记忆结构 (Instant/Working/Long-term)
- **Checkpoint**: 状态快照与恢复
- **Solver**: 循环检测与螺旋跳跃
- **Specs**: 项目规范检查

### 1.3 架构映射
```
.trae/skills/spiral-loop-system/
├── core/
│   ├── memory.py      # [MEMORY] 三层记忆管理
│   ├── checkpoint.py  # [CHECKPOINT] 检查点管理
│   ├── solver.py      # [SOLVER] 循环求解器
│   └── specs.py       # [SPECS] 规范检查器
├── scripts/
│   └── main.py        # [CLI] 统一命令行入口
└── SKILL.md           # [DOC] 技能文档
```

## 2. Goal Layer (目标层)

### 2.1 输入期望
- **触发场景**: 任务中断、陷入死循环、需要回溯状态、项目规范检查。
- **调用方式**: 通过 `RunCommand` 调用 `scripts/main.py`。

### 2.2 输出标准
- **Memory**: 成功存储或读取节点/模式。
- **Checkpoint**: 创建检查点 ID 或恢复状态数据。
- **Solver**: 检测结果（normal/loop）或跳跃策略建议。
- **Specs**: 规范合规性报告 (Valid/Issues)。

## 3. Behavior Layer (行为层)

### 3.1 原子级技能调用指南 (CLI Usage)

#### A. 记忆管理 (Memory)
```bash
# 添加瞬时节点
python ".trae/skills/spiral-loop-system/scripts/main.py" memory --action add --content "当前思考内容"

# 查看最近节点
python ".trae/skills/spiral-loop-system/scripts/main.py" memory --action list
```

#### B. 检查点管理 (Checkpoint)
```bash
# 创建检查点 (在关键决策前)
python ".trae/skills/spiral-loop-system/scripts/main.py" checkpoint --action create --desc "完成阶段A"

# 恢复检查点
python ".trae/skills/spiral-loop-system/scripts/main.py" checkpoint --action restore --id "ckpt_123456"

# 列出所有检查点
python ".trae/skills/spiral-loop-system/scripts/main.py" checkpoint --action list
```

#### C. 循环求解 (Solver)
```bash
# 检测当前状态是否陷入循环
python ".trae/skills/spiral-loop-system/scripts/main.py" solver --action detect --state "当前输出内容"

# 获取跳跃策略 (当陷入循环时)
python ".trae/skills/spiral-loop-system/scripts/main.py" solver --action jump --state "当前困境" --strategy spiral
```

#### D. 规范检查 (Specs)
```bash
# 检查文档结构
python ".trae/skills/spiral-loop-system/scripts/main.py" specs --action check_doc --file "path/to/doc.md"

# 检查文件组织
python ".trae/skills/spiral-loop-system/scripts/main.py" specs --action check_org --dir "path/to/module"
```

## 4. Protocol Layer (协议层)

### 4.1 使用原则
- **主动记录**: 在长任务中，主动调用 `memory add` 记录关键节点。
- **防御性检查**: 在生成重要代码前，调用 `checkpoint create`。
- **破局思维**: 一旦发现 `solver detect` 返回 `linear_loop`，立即调用 `solver jump` 获取新思路。
- **合规交付**: 在交付文档前，必须运行 `specs check_doc` 确保格式正确。
