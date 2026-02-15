"""
Memory 笔记系统 v1.1
"""

import json
import hashlib
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass
from enum import Enum


class MemoryType(Enum):
    SESSION = "sessions"
    TASK = "tasks"
    ERROR = "errors"
    GLOBAL = "global"


class ReadTrigger(Enum):
    TASK_START = "task_start"
    ERROR_ENCOUNTERED = "error_encountered"
    SIMILAR_TASK = "similar_task"


class WriteTrigger(Enum):
    TASK_START = "task_start"
    KEY_DECISION = "key_decision"
    SUBTASK_COMPLETE = "subtask_complete"
    ERROR_OCCURRED = "error_occurred"
    ERROR_FIXED = "error_fixed"
    TASK_COMPLETE = "task_complete"


@dataclass
class MemoryEntry:
    timestamp: str
    trigger: str
    content: str
    metadata: Dict[str, Any]


class MemoryManager:
    def __init__(self, memory_dir: str = '.trae/memory'):
        self.memory_dir = Path(memory_dir)
        self._init_directories()
        self._index_cache = None
    
    def _init_directories(self):
        for mem_type in MemoryType:
            (self.memory_dir / mem_type.value).mkdir(parents=True, exist_ok=True)
    
    def _get_note_path(self, mem_type: MemoryType, note_id: str) -> Path:
        return self.memory_dir / mem_type.value / f"{note_id}.md"
    
    def _generate_hash(self, content: str) -> str:
        return hashlib.md5(content.encode()).hexdigest()[:8]
    
    def _extract_error_signature(self, error_message: str) -> str:
        clean = re.sub(r'File ".*?"', 'File "<path>"', error_message)
        clean = re.sub(r'line \d+', 'line N', clean)
        return self._generate_hash(clean)
    
    def _load_index(self) -> Dict[str, Any]:
        index_path = self.memory_dir / 'index.json'
        if index_path.exists():
            with open(index_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'sessions': {}, 'tasks': {}, 'errors': {}, 'global': {}, 'keywords': {}}
    
    def _save_index(self, index: Dict):
        index_path = self.memory_dir / 'index.json'
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
    
    def should_write(self, trigger: WriteTrigger, context: Dict[str, Any]) -> Tuple[bool, str, MemoryType]:
        if trigger == WriteTrigger.TASK_START:
            session_id = context.get('session_id', self._generate_hash(str(datetime.now())))
            return True, session_id, MemoryType.SESSION
        elif trigger == WriteTrigger.ERROR_OCCURRED:
            error_sig = self._extract_error_signature(context.get('error_message', ''))
            return True, error_sig, MemoryType.ERROR
        elif trigger == WriteTrigger.ERROR_FIXED:
            error_sig = context.get('error_signature', self._extract_error_signature(context.get('error_message', '')))
            return True, error_sig, MemoryType.ERROR
        elif trigger == WriteTrigger.TASK_COMPLETE:
            task_type = context.get('task_type', 'general')
            task_hash = self._generate_hash(context.get('task_description', str(datetime.now())))
            return True, f"{task_type}_{task_hash}", MemoryType.TASK
        return False, "", MemoryType.SESSION
    
    def write_note(self, trigger: WriteTrigger, content: str, context: Dict[str, Any] = None) -> Optional[str]:
        context = context or {}
        should, note_id, mem_type = self.should_write(trigger, context)
        if not should:
            return None
        
        note_path = self._get_note_path(mem_type, note_id)
        mode = 'a' if note_path.exists() else 'w'
        
        with open(note_path, mode, encoding='utf-8') as f:
            if mode == 'a':
                f.write("\n\n---\n\n")
            f.write(f"# [{datetime.now().isoformat()}] {trigger.value}\n\n{content}\n")
        
        index = self._load_index()
        type_key = mem_type.value
        if type_key not in index:
            index[type_key] = {}
        if note_id not in index[type_key]:
            index[type_key][note_id] = {'created_at': datetime.now().isoformat(), 'task_type': context.get('task_type')}
        self._save_index(index)
        
        return note_id
    
    def read_note(self, note_id: str, mem_type: MemoryType = None) -> Optional[str]:
        if '/' in note_id and mem_type is None:
            parts = note_id.split('/', 1)
            mem_type = MemoryType(parts[0])
            note_id = parts[1]
        
        if mem_type is None:
            for mt in MemoryType:
                path = self._get_note_path(mt, note_id)
                if path.exists():
                    mem_type = mt
                    break
        
        if mem_type is None:
            return None
        
        note_path = self._get_note_path(mem_type, note_id)
        if not note_path.exists():
            return None
        
        with open(note_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def get_error_fix(self, error_message: str) -> Optional[Dict[str, str]]:
        error_sig = self._extract_error_signature(error_message)
        content = self.read_note(error_sig, MemoryType.ERROR)
        if not content:
            return None
        
        fix_match = re.search(r'## 修复方案\n(.*?)(?=\n##|\Z)', content, re.DOTALL)
        if fix_match:
            return {'error_signature': error_sig, 'fix': fix_match.group(1).strip(), 'full_note': content}
        return {'error_signature': error_sig, 'full_note': content}
    
    def record_error_and_fix(self, error_message: str, fix: str, context: Dict[str, Any] = None):
        context = context or {}
        self.write_note(WriteTrigger.ERROR_OCCURRED, f"## 错误信息\n```\n{error_message}\n```\n", context)
        self.write_note(WriteTrigger.ERROR_FIXED, f"## 错误签名\n{self._extract_error_signature(error_message)}\n\n## 修复方案\n{fix}\n", context)
    
    def record_subtask_result(self, subtask_id: str, result_summary: str, key_findings: List[str], context: Dict[str, Any] = None):
        context = context or {}
        context['subtask_id'] = subtask_id
        content = f"## 子任务结果摘要\n{result_summary}\n\n## 关键发现\n" + "\n".join([f"- {f}" for f in key_findings])
        self.write_note(WriteTrigger.SUBTASK_COMPLETE, content, context)
