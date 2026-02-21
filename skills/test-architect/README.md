# Test Architect Skill

Automatically detects project type and manages testing skills.

## Usage
`python .trae/skills/test-architect/architect.py --path "project/path"`

## Logic
1.  Detects framework (Python, React, Node, Go, etc.).
2.  Checks if a dedicated testing skill (e.g., `test-python-pytest`) exists.
3.  If not, it automatically generates a new skill folder with a template.
4.  Returns JSON with the recommended skill name and path.
