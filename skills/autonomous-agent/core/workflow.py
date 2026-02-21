"""
Workflow Runner v1.1 - 工作流执行器
动态路径解析，支持跨项目移植
使用统一路径模块
集成 Token 追踪功能
"""

import os
import subprocess
import sys
import yaml
import json
from pathlib import Path
from datetime import datetime

from .paths import get_workflows_dir
from .token_tracker import record_session_tokens, estimate_tokens, estimate_tokens_for_dict


class WorkflowRunner:
    def __init__(self, workflow_dir=None):
        if workflow_dir:
            self.workflow_dir = Path(workflow_dir)
        else:
            self.workflow_dir = get_workflows_dir()
        
        if not self.workflow_dir.exists():
            cwd_workflow_dir = Path('自动化工作流组件库/workflows').resolve()
            if cwd_workflow_dir.exists():
                self.workflow_dir = cwd_workflow_dir

    def run(self, workflow_name, session_id=None):
        """
        执行工作流
        
        参数:
            workflow_name: 工作流名称
            session_id: 会话ID (用于 Token 追踪)
        
        返回:
            dict: 执行结果
        """
        start_time = datetime.now()
        input_text = f"workflow:{workflow_name}"
        
        manager_script = self.workflow_dir / 'workflow_manager_v2.py'
        
        if manager_script.exists():
            cmd = [sys.executable, str(manager_script), 'run', workflow_name]
            try:
                result = subprocess.run(cmd, capture_output=True, encoding='utf-8', timeout=300)
                
                if result.returncode == 0:
                    output_result = {'status': 'success', 'output': result.stdout}
                else:
                    output_result = {'status': 'error', 'message': result.stderr}
                
                if session_id:
                    output_text = json.dumps(output_result, ensure_ascii=False)[:500]
                    record_session_tokens(
                        session_id, 
                        input_text, 
                        output_text, 
                        "workflow_execution"
                    )
                
                return output_result
                
            except Exception as e:
                error_result = {'status': 'error', 'message': str(e)}
                
                if session_id:
                    record_session_tokens(
                        session_id, 
                        input_text, 
                        str(e), 
                        "workflow_error"
                    )
                
                return error_result
        else:
            error_result = {'status': 'error', 'message': f'Workflow manager not found at {manager_script}'}
            
            if session_id:
                record_session_tokens(
                    session_id, 
                    input_text, 
                    error_result['message'], 
                    "workflow_not_found"
                )
            
            return error_result

    def list_workflows(self):
        """列出所有可用工作流"""
        workflows = []
        
        for yaml_file in self.workflow_dir.glob('*.yaml'):
            workflow_info = {
                'name': yaml_file.stem,
                'path': str(yaml_file),
                'description': ''
            }
            
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    content = yaml.safe_load(f)
                    if content:
                        workflow_info['description'] = content.get('description', '')
                        workflow_info['triggers'] = content.get('triggers', [])
            except:
                pass
            
            workflows.append(workflow_info)
        
        return workflows

    def get_workflow_info(self, workflow_name):
        """获取工作流详细信息"""
        workflow_path = self.workflow_dir / f'{workflow_name}.yaml'
        
        if not workflow_path.exists():
            return None
        
        try:
            with open(workflow_path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)
            
            return {
                'name': workflow_name,
                'path': str(workflow_path),
                'description': content.get('description', ''),
                'triggers': content.get('triggers', []),
                'steps': content.get('steps', []),
                'skills': content.get('skills', [])
            }
        except Exception as e:
            return {
                'name': workflow_name,
                'path': str(workflow_path),
                'error': str(e)
            }
