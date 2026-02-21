# Task Assessor Skill

Use this skill to assess task complexity and determine execution strategy.

## Usage

### Assess Task
`python .trae/skills/task-assessor/assess_task.py --desc "task description" --type "task_type"`

- `task_type`: refactor, feature, bugfix, doc
- `task_desc`: Full description of the task.

### Output
JSON object with `score`, `level` (L0/L1/L2), and `strategy`.
