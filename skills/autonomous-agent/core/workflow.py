
import os
import yaml
from pathlib import Path

class WorkflowRunner:
    def __init__(self, workflow_dir=None):
        if workflow_dir:
            self.workflow_dir = Path(workflow_dir)
        else:
            # 自动定位到项目根目录下的 .trae/workflows
            # 假设当前文件在 .trae/skills/autonomous-agent/core/workflow.py
            current_file = Path(__file__).resolve()
            # 向上回溯 4 层: core -> autonomous-agent -> skills -> .trae -> root
            project_root = current_file.parent.parent.parent.parent.parent
            self.workflow_dir = project_root / '.trae' / 'workflows'
        
        if not self.workflow_dir.exists():
             # Fallback: 尝试当前工作目录
             self.workflow_dir = Path('.trae/workflows')

    def run(self, workflow_name):
        import subprocess
        import sys
        
        # 尝试使用 workflow_manager_v2.py
        manager_script = self.workflow_dir / 'workflow_manager_v2.py'
        
        if manager_script.exists():
            cmd = [sys.executable, str(manager_script), 'run', workflow_name]
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                if result.returncode == 0:
                     return {'status': 'success', 'output': result.stdout}
                else:
                     return {'status': 'error', 'message': result.stderr}
            except Exception as e:
                return {'status': 'error', 'message': str(e)}
        else:
            return {'status': 'error', 'message': f'Workflow manager not found at {manager_script}'}
