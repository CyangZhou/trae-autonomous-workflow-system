---
name: delivery-documenter
version: "1.0.0"
description: 智能交付文档生成，自动生成部署说明、验证方法和限制说明。
tags: ["delivery", "documentation", "automation"]
triggers:
  - 交付文档
  - 生成交付
  - delivery
priority: 40
---

# Delivery Documenter Skill

**Description:** 
基于智能交付文档生成模块 (Smart Delivery Generator v1.0)，自动生成标准化的交付文档。
包含：
1. 任务摘要与文件变更
2. 部署步骤 (Deployment Steps)
3. 验证方法 (Verification Methods)
4. 限制说明 (Limitations)
5. 后续建议 (Future Tasks)

## Usage

### CLI
```bash
python .trae/skills/delivery-documenter/main.py "Task Description" --session-id "SESSION_123"
```

### Options
- `task_description`: 任务描述 (Required)
- `--session-id`: 会话ID (Required)
- `--output-dir`: 文档保存目录 (Optional)
- `--execution-result`: 执行结果 JSON 字符串 (Optional)
- `--quality-report`: 质量报告 JSON 字符串 (Optional)
- `--task-type`: 任务类型 (Optional, e.g., 'python', 'web', 'skill')

### Example
```bash
python .trae/skills/delivery-documenter/main.py "Implement login feature" --session-id "LOGIN_001" --task-type "python"
```

## Output
Human-readable summary and path to the generated Markdown file.
