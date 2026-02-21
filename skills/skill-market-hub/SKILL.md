---
name: skill-market-hub
version: "1.0.0"
description: 技能市场聚合器，从开源市场和 GitHub 搜索、发现、下载 AI 技能。
tags: ["market", "download", "skills", "github", "discovery"]
triggers:
  - 技能市场
  - 下载技能
  - 搜索技能
  - skill market
priority: 35
---

# Skill Market Hub

一个技能市场聚合器，可以从多个开源技能市场和 GitHub 仓库搜索、发现、下载 AI 技能到本地项目。

## 功能

- 🔍 搜索技能：在多个开源市场搜索特定技能
- 🔥 发现热门：获取当前最火的技能列表
- ⬇️ 一键下载：自动下载并安装到 `.trae/skills/` 目录
- 📦 多源支持：支持 GitHub、OpenPackage 等主流技能源

## 使用方法 (相对路径)

### 1. 搜索特定技能
```bash
python ./.trae/skills/skill-market-hub/skill_market_hub.py search "pdf"
```

### 2. 获取热门技能
```bash
python ./.trae/skills/skill-market-hub/skill_market_hub.py trending
```

### 3. 安装技能
```bash
python ./.trae/skills/skill-market-hub/skill_market_hub.py install <skill-name> --source <source>
```

### 4. 列出可用源
```bash
python ./.trae/skills/skill-market-hub/skill_market_hub.py sources
```

## 支持的数据源

| 源 | 类型 | 描述 |
|---|-----|-----|
| github | 仓库 | 搜索 GitHub 上的技能相关仓库 |
| opencode | 市场 | OpenCode 官方技能市场 |
| awesome-ai | 列表 | Awesome AI Agents 列表 |

## 输出格式

返回 JSON 格式结果：
```json
{
  "status": "success",
  "action": "search",
  "results": [
    {
      "name": "skill-name",
      "description": "技能描述",
      "source": "github",
      "url": "https://github.com/...",
      "stars": 1200,
      "installed": false
    }
  ]
}
```

## 注意事项

- 下载前会检查本地是否已存在同名技能
- 支持自动解析 SKILL.md 元数据
- 需要网络连接访问外部 API
