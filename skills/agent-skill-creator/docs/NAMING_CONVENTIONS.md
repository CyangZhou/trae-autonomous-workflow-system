# Naming Conventions for Trae Skills

## 🎯 **Purpose**

Consistent naming makes skills easier to find, use, and maintain.

## 🏷️ **General Rules**

### **1. Folder Names**
- Use **kebab-case** (lowercase with hyphens).
- Keep it descriptive but concise.
- **Avoid** generic names like `utils` or `tools` unless it's a collection.

**Good:**
- `pdf-extractor`
- `weather-reporter`
- `git-automator`

**Bad:**
- `PdfExtractor` (PascalCase)
- `pdf_extractor` (snake_case is okay but less standard for folders)
- `tool1` (nondescript)

### **2. Skill Names (in SKILL.md)**
- The `name` field in YAML frontmatter should match the folder name.
- It should be unique within the project.

```yaml
---
name: pdf-extractor
description: Extracts text from PDF files.
---
```

### **3. Script Names**
- `main.py` is recommended for the primary entry point.
- Use `snake_case` for Python files (e.g., `data_processor.py`).

## 🚫 **Suffixes**

Unlike Claude Skills which often use `-cskill`, Trae skills **do not require any specific suffix**.
- You *can* use `-skill` if you want to be explicit (e.g., `weather-skill`), but it's not mandatory.
- Avoid platform-specific suffixes like `-plugin` or `-extension`.

## 🔧 **Recommendations**

- **Verb-Noun**: `extract-pdf`, `generate-report` (Clear action)
- **Noun-er**: `pdf-extractor`, `report-generator` (Tool identity)
- **Domain-Function**: `git-backup`, `data-cleaner` (Scoped function)
