# Trae Skills Architecture: Complete Guide

## 🎯 **Purpose**

This document defines the standard architecture for creating skills in Trae IDE.

## 📚 **Core Concepts**

### **Trae Skill**
A **Skill** in Trae is a self-contained folder located in `.trae/skills/` that provides a specific capability to the AI agent (Trae).

It MUST contain a `SKILL.md` file with YAML frontmatter, which Trae uses to register the skill as a tool.

**Example:** `.trae/skills/pdf-extractor/`

## 🏗️ **Standard Structure**

### **The Canonical Layout**

```
.trae/skills/<skill-name>/
├── SKILL.md              # REQUIRED: Metadata & Usage Instructions
├── requirements.txt      # RECOMMENDED: Python dependencies
├── main.py               # RECOMMENDED: Entry point script
├── scripts/              # OPTIONAL: Additional scripts
├── README.md             # OPTIONAL: Human-readable documentation
└── assets/               # OPTIONAL: Resources, templates, etc.
```

### **1. SKILL.md (The Heart)**

This file tells Trae what the skill is and how to use it.

```markdown
---
name: my-skill-name
description: A short description of what this skill does (for tool selection).
---

# My Skill Name

## Description
Detailed explanation of the skill's capabilities.

## Usage

### Command Line
You can run this skill using:
`python .trae/skills/my-skill-name/main.py --arg value`

### Examples
- `python main.py input.pdf`
```

### **2. Python Implementation**

- **Language**: Python is the primary language for Trae skills due to its rich ecosystem.
- **Entry Point**: `main.py` is the standard entry point.
- **Arguments**: Use `argparse` to handle CLI arguments. This allows Trae to invoke the skill using `RunCommand`.

### **3. Dependencies**

- List all external libraries in `requirements.txt`.
- Trae can automatically install them using `pip install -r .trae/skills/<skill-name>/requirements.txt`.

## 🔍 **Best Practices**

1.  **Self-Contained**: A skill should rely as little as possible on the project's global environment.
2.  **Stateless**: Ideally, skills should take input, process it, and produce output without side effects (unless the skill's purpose is side effects like file modification).
3.  **Error Handling**: Scripts should print clear error messages to stderr and exit with non-zero codes on failure.
4.  **Documentation**: Keep `SKILL.md` up-to-date so Trae knows exactly how to call the tool.

## 🚫 **What to Avoid**

- **Hardcoded Paths**: Use `os.path.dirname(__file__)` to locate resources relative to the script.
- **Global Pollution**: Do not modify global project settings unless explicitly requested.
- **Complex Setup**: Skills should be "plug and play". Avoid complex installation steps beyond `pip install`.
