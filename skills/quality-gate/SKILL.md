---
name: quality-gate
version: "1.1.0"
description: 增强版质量把关，支持静态分析、真实验证、完整性检查和Token追踪。
tags: ["quality", "lint", "test", "validation", "code-review"]
triggers:
  - 质量检查
  - 质量把关
  - lint
  - quality gate
priority: 70
---

# Quality Gate Skill

**Description:** 
基于增强版质量把关模块 (Quality Gate v1.1)，提供全面的代码质量检查。
包含：
1. 边界处理检查 (Boundary)
2. 专业度检查 (Professionalism)
3. 完整性检查 (Completeness)
4. 真实验证 (Real Validation - Lint/Test/TypeCheck)

## Usage

### CLI
```bash
python .trae/skills/quality-gate/main.py "path/to/file_or_dir"
```

### Options
- `path`: 待检查的文件或目录路径 (Required)
- `--code`: 待检查的代码内容 (Optional, defaults to file content)
- `--session-id`: 指定会话ID (Optional)
- `--artifacts`: 交付物元数据 JSON 字符串 (Optional)

### Example
```bash
python .trae/skills/quality-gate/main.py "src/main.py"
```

## Output
Human-readable summary and JSON result with pass/fail status and recommendations.
