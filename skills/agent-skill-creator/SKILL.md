---
name: agent-skill-creator
description: 专为 Trae 设计的元技能 (Meta-Skill)，用于指导云舒自主创建、架构和实现高质量的 AI 技能与智能体。支持从需求分析到代码实现的完整流程，确保生成的技能符合 Trae 规范并可直接使用。
---
# Agent Skill Creator (Trae Edition)

> **一句话**：我是“技能的母亲”。我教云舒如何为自己创造新的能力。

此技能指导云舒如何在 Trae 环境中自主创建完整的 AI 技能 (Skills) 和智能体 (Agents)。

## 🎯 何时使用 (Triggers)

当用户表达以下需求时，云舒应自动激活此技能：

- **创建技能/Agent**：
  - "做一个查天气的技能"
  - "我需要一个能自动写周报的 Agent"
  - "开发一个工具来处理 PDF"
- **自动化工作流**：
  - "每天早上我都要手动下载数据，能不能自动化？"
  - "把这个处理流程变成一个技能"
- **扩展能力**：
  - "你现在的能力不够，给自己加个技能吧"

## 🏗️ 创建流程 (5-Step Protocol)

激活后，云舒将按照以下 5 个阶段自主执行：

### PHASE 1: DISCOVERY (发现)
- **分析需求**：用户到底想要什么？核心痛点是什么？
- **技术选型**：需要哪些 Python 库？是否有现成的 API？
- **可行性验证**：先写个小脚本测试一下核心功能 (Proof of Concept)。

### PHASE 2: DESIGN (设计)
- **交互模式**：用户怎么调用？(是命令行参数，还是自然语言触发？)
- **输入输出**：输入是什么（文件路径、URL、文本）？输出是什么（文件、报告、终端打印）？
- **错误处理**：如果断网了怎么办？文件不存在怎么办？

### PHASE 3: ARCHITECTURE (架构)
- **目录结构**：规划文件布局。
  ```
  .trae/skills/new-skill-name/
  ├── SKILL.md              # 核心元数据与说明书 (MANDATORY)
  ├── requirements.txt      # 依赖库
  ├── main.py               # 入口脚本 (或 scripts/xxx.py)
  └── README.md             # 用户文档
  ```

### PHASE 4: IMPLEMENTATION (实现)
- **编写代码**：使用 Python 编写功能逻辑。
  - *要求*：代码必须健壮，包含错误处理。
  - *风格*：符合 Python PEP8 规范。
- **编写 SKILL.md**：这是 Trae 识别技能的关键。
  - *格式*：必须包含 Frontmatter (YAML 头)。
  - *内容*：详细描述技能的功能、参数和使用示例。

### PHASE 5: VALIDATION (验证)
- **安装依赖**：运行 `pip install -r requirements.txt`。
- **功能测试**：在终端运行脚本，验证功能是否符合预期。
- **交付确认**：告诉用户技能已就绪，并演示如何使用。

---

## 📝 核心文件规范 (Standard)

### 1. SKILL.md (必须)

所有 Trae 技能必须包含此文件。

```markdown
---
name: my-new-skill                  # 技能名称 (英文, kebab-case)
description: 简短描述技能的功能...    # 技能描述 (出现在工具提示中)
---
# My New Skill

**Description:** 详细的功能介绍。

## Usage
...
```

### 2. Python 脚本

- 推荐使用 `argparse` 处理命令行参数，以便 Trae 能够通过 CLI 调用。
- 尽量保持独立性，减少对外部环境的依赖。

---

## 🚀 示例：创建一个“天气查询”技能

**用户输入**："帮我做一个查天气的技能"

**云舒执行**：
1.  **创建目录**：`mkdir .trae/skills/weather-reporter`
2.  **编写代码**：`weather-reporter/weather.py` (调用 OpenWeatherMap API)
3.  **编写描述**：`weather-reporter/SKILL.md`
    ```markdown
    ---
    name: weather-reporter
    description: 查询指定城市的实时天气信息。
    ---
    # Weather Reporter
    ...
    ```
4.  **测试运行**：`python .trae/skills/weather-reporter/weather.py "Beijing"`

---

## ⚠️ 注意事项

1.  **依赖管理**：尽量使用标准库；如果必须使用第三方库，务必在 `requirements.txt` 中列出，并提示用户安装。
2.  **路径处理**：使用相对路径或动态获取脚本所在目录，确保技能的可移植性。
