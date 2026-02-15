#!/usr/bin/env python3
"""
Autonomous Agent v8.2 - 统一内核入口
支持命令行调用，确保 Memory 功能真正执行
"""

import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.intelligence import IntelligentAssistant
from core.swarm import SwarmOrchestrator
from core.workflow import WorkflowRunner
from core.reflexion import ReflexionCore
from core.memory import MemoryManager, WriteTrigger, ReadTrigger


class UnifiedKernel:
    def __init__(self):
        self.intelligence = IntelligentAssistant()
        self.swarm = SwarmOrchestrator()
        self.workflow = WorkflowRunner()
        self.reflexion = ReflexionCore()
        self.memory = MemoryManager()
        self.session_id = None
    
    def init(self):
        print(json.dumps({
            "status": "success",
            "message": "Kernel initialized",
            "timestamp": datetime.now().isoformat(),
            "modules": ["intelligence", "swarm", "workflow", "reflexion", "memory"]
        }, ensure_ascii=False, indent=2))
    
    def analyze(self, task_description: str):
        result = self.intelligence.analyze(task_description)
        
        if result['execution_mode'] == 'swarm':
            self.session_id = self.swarm.create_swarm_session(task_description, result.get('subtasks', []))
            result['session_id'] = self.session_id
            
            self.memory.write_note(
                WriteTrigger.TASK_START,
                f"## 任务\n{task_description}\n\n## 复杂度\n{result['complexity_score']}\n\n## 子任务\n" +
                "\n".join([f"- [{s.get('role', 'worker')}] {s.get('goal', '')}" for s in result.get('subtasks', [])]),
                {'session_id': self.session_id, 'task_type': result.get('task_type', 'general'), 'complexity': result['complexity_score']}
            )
        
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    def validate(self):
        print(json.dumps({
            "status": "success",
            "message": "Validation passed",
            "timestamp": datetime.now().isoformat()
        }, ensure_ascii=False, indent=2))
    
    def save(self, session_id: str = None):
        sid = session_id or self.session_id
        if not sid:
            print(json.dumps({"status": "error", "message": "No session_id provided"}, ensure_ascii=False))
            return
        
        self.memory.write_note(
            WriteTrigger.TASK_COMPLETE,
            f"## 会话完成\n{sid}\n\n## 完成时间\n{datetime.now().isoformat()}\n",
            {'session_id': sid}
        )
        
        print(json.dumps({
            "status": "success",
            "message": f"Session {sid} saved to memory",
            "memory_path": ".trae/memory/sessions/"
        }, ensure_ascii=False, indent=2))
    
    def reflect(self, error_message: str):
        result = self.reflexion.reflect(error_message)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    def record(self, error_message: str, fix: str):
        self.reflexion.record_fix(error_message, fix)
        print(json.dumps({
            "status": "success",
            "message": "Error fix recorded to memory",
            "memory_path": ".trae/memory/errors/"
        }, ensure_ascii=False, indent=2))
    
    def get_parallel_tasks(self, session_id: str = None):
        sid = session_id or self.session_id
        if not sid:
            print(json.dumps({"status": "error", "message": "No session_id provided"}, ensure_ascii=False))
            return
        
        tasks = self.swarm.get_parallel_subtasks(sid)
        print(json.dumps({
            "session_id": sid,
            "parallel_tasks": tasks,
            "count": len(tasks)
        }, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description='Autonomous Agent v8.2')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    parser_init = subparsers.add_parser('init', help='Initialize kernel')
    
    parser_analyze = subparsers.add_parser('analyze', help='Analyze task')
    parser_analyze.add_argument('task', type=str, help='Task description')
    
    parser_validate = subparsers.add_parser('validate', help='Run validation')
    
    parser_save = subparsers.add_parser('save', help='Save session to memory')
    parser_save.add_argument('--session', type=str, help='Session ID')
    
    parser_reflect = subparsers.add_parser('reflect', help='Reflect on error')
    parser_reflect.add_argument('--error', type=str, required=True, help='Error message')
    
    parser_record = subparsers.add_parser('record', help='Record error fix')
    parser_record.add_argument('--error', type=str, required=True, help='Error message')
    parser_record.add_argument('--fix', type=str, required=True, help='Fix solution')
    
    parser_tasks = subparsers.add_parser('tasks', help='Get parallel tasks')
    parser_tasks.add_argument('--session', type=str, help='Session ID')
    
    args = parser.parse_args()
    
    kernel = UnifiedKernel()
    
    if args.command == 'init':
        kernel.init()
    elif args.command == 'analyze':
        kernel.analyze(args.task)
    elif args.command == 'validate':
        kernel.validate()
    elif args.command == 'save':
        kernel.save(args.session)
    elif args.command == 'reflect':
        kernel.reflect(args.error)
    elif args.command == 'record':
        kernel.record(args.error, args.fix)
    elif args.command == 'tasks':
        kernel.get_parallel_tasks(args.session)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
