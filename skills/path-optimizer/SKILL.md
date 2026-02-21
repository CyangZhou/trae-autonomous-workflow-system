---
name: path-optimizer
version: "1.0.0"
description: 自动检测与修复硬编码绝对路径，实现路径动态化与可移植性。
tags: ["path-migration", "refactoring", "automation", "python"]
triggers:
  - 路径优化
  - 硬编码路径
  - 路径修复
  - path fix
priority: 30
---

# Skill: Path Optimizer (路径优化专家)

## Description
本技能用于自动化检测和修复项目代码中的硬编码绝对路径（如 `/Users/username/project/...`）。它能将这些路径转换为基于 `pathlib` 的动态相对路径，确保代码在不同环境（多人协作、CI/CD、容器化）下的可移植性。

## When to use
- 当你需要迁移项目到新环境或新机器时。
- 当你需要修复代码中的“it works on my machine”路径问题时。
- 当你需要审计项目中的路径依赖时。
- 当用户询问“如何修复路径错误”或“为什么找不到文件”时。

## Tools
### 1. Scan Hardcoded Paths
扫描项目中的硬编码绝对路径。

```bash
python3 .trae/skills/path-optimizer/scripts/scan_paths.py --root .
```

### 2. Generate Path Fix Suggestion
生成修复硬编码路径的代码建议。

```bash
python3 .trae/skills/path-optimizer/scripts/fix_paths.py --file <file_path> --line <line_number> --path <absolute_path>
```

## Instructions
1.  **Always scan first**: Before applying any fixes, run the scan tool to identify all affected files.
2.  **Analyze context**: Verify if the hardcoded path points to a file *inside* the project. If it points outside (e.g., system libraries), do not touch it.
3.  **Use Fix Tool for Suggestions**: Use `fix_paths.py` to generate the correct `pathlib` relative path code.
4.  **Prefer `pathlib`**: When fixing, always use `pathlib.Path(__file__).resolve().parents[n]` instead of `os.path`.
5.  **Verify**: After fixing, run the modified script (if possible) or check syntax with `python -m py_compile`.
