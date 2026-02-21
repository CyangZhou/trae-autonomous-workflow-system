---
name: "memory-core"
description: "RAG记忆管理核心。任务开始前检索记忆，任务结束后持久化上下文。支持向量语义检索、错误/成功/决策分类存储。Invoke when task starts or ends, or user asks to remember something."
---

# Memory Core

云舒的记忆中枢，基于 RAG（检索增强生成）架构。

## 核心协议

### 任务开始前（强制）
```bash
python .trae/skills/memory-core/memory_core.py --action retrieve --query "任务关键词"
```

### 任务结束后（强制）
```bash
python .trae/skills/memory-core/memory_core.py --action success --intent "意图" --steps "步骤1,步骤2"
python .trae/skills/memory-core/memory_core.py --action error --type "错误类型" --wrong "错误做法" --right "正确做法"
python .trae/skills/memory-core/memory_core.py --action decision --choice "选择" --reason "理由"
```

## 命令列表

| Action | 用途 | 必需参数 |
|--------|------|----------|
| `retrieve` | 语义检索记忆 | `--query` |
| `success` | 记录成功模式 | `--intent`, `--steps` |
| `error` | 记录错误模式 | `--type`, `--wrong`, `--right` |
| `decision` | 记录决策 | `--choice`, `--reason` |
| `context` | 记录上下文 | `--content` |
| `list` | 列出所有记忆 | - |
| `rebuild` | 重建向量索引 | - |
| `stats` | 显示统计信息 | - |

## 可选参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--top_k` | 返回结果数 | 5 |
| `--min_similarity` | 最小相似度阈值 | 0.05 |
| `--tags` | 标签（逗号分隔） | - |

## 存储位置

记忆数据存储在项目内：
- `.trae/memory/core/memory.json` - 记忆元数据
- `.trae/memory/core/vectors.index` - 向量索引
- `.trae/memory/core/memory.md` - 人类可读格式

## 特性

1. **向量语义检索**：基于 sentence-transformers，支持中英文混合检索
2. **原子写入**：索引和元数据同步更新，避免不一致
3. **去重检测**：自动跳过相似度 > 0.95 的重复内容
4. **Git 友好**：存储在项目内，便于版本控制

## 依赖

```bash
pip install sentence-transformers faiss-cpu numpy
```

模型：`paraphrase-multilingual-MiniLM-L12-v2`（首次使用自动下载）
