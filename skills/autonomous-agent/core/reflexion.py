"""
Reflexion 核心模块 v2.1
"""

from typing import Dict, Any, Optional, List
from .memory import MemoryManager, WriteTrigger, ReadTrigger


class ReflexionCore:
    def __init__(self, memory_dir='.trae/memory'):
        self.memory = MemoryManager(memory_dir)
    
    def reflect(self, error_log: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        context = context or {}
        fix = self.memory.get_error_fix(error_log)
        
        if fix:
            return {'action': 'apply_known_fix', 'fix': fix.get('fix', ''), 'error_signature': fix.get('error_signature', ''), 'source': 'memory'}
        return {'action': 'analyze', 'fix': 'suggestion', 'source': 'inference'}
    
    def record_fix(self, error_message: str, fix_solution: str, context: Dict[str, Any] = None):
        self.memory.record_error_and_fix(error_message, fix_solution, context)
    
    def get_similar_experiences(self, task_type: str, keywords: List[str] = None) -> Dict[str, str]:
        context = {'task_type': task_type, 'keywords': keywords or [], 'complexity': 5}
        return self.memory.read_notes_by_trigger(ReadTrigger.SIMILAR_TASK, context)
    
    def record_decision(self, decision: str, reason: str, session_id: str = None, task_type: str = None):
        content = f"## 决策\n{decision}\n\n## 原因\n{reason}\n"
        self.memory.write_note(WriteTrigger.KEY_DECISION, content, {'session_id': session_id, 'task_type': task_type})
