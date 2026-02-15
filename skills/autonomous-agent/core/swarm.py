"""
Swarm 蜂群编排器 v2.2
"""

import sqlite3
import uuid
import json
import logging
from pathlib import Path
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, List, Any

from .memory import MemoryManager, WriteTrigger

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('SwarmCore')


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class SwarmOrchestrator:
    def __init__(self, db_path='.trae/swarm/swarm_core.db', memory_dir='.trae/memory'):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.memory = MemoryManager(memory_dir)
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path, timeout=10)

    def _init_db(self):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('PRAGMA journal_mode=WAL;')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY, parent_id TEXT, status TEXT DEFAULT 'pending',
                priority INTEGER DEFAULT 5, worker_type TEXT, payload TEXT, result TEXT,
                error_message TEXT, created_at DATETIME, updated_at DATETIME, completed_at DATETIME
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS swarm_sessions (
                session_id TEXT PRIMARY KEY, main_task TEXT, subtask_count INTEGER,
                completed_count INTEGER DEFAULT 0, status TEXT DEFAULT 'running',
                created_at DATETIME, completed_at DATETIME
            )
        ''')
        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")

    def create_swarm_session(self, main_task: str, subtasks: List[Dict]) -> str:
        session_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO swarm_sessions (session_id, main_task, subtask_count, created_at) VALUES (?, ?, ?, ?)',
                       (session_id, main_task, len(subtasks), now))
        
        for subtask in subtasks:
            task_id = str(uuid.uuid4())
            cursor.execute('INSERT INTO tasks (task_id, parent_id, status, priority, worker_type, payload, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                           (task_id, session_id, TaskStatus.PENDING.value, subtask.get('priority', 5), subtask['type'], json.dumps(subtask), now, now))
        
        conn.commit()
        conn.close()
        
        self.memory.write_note(WriteTrigger.TASK_START,
            f"## 主任务\n{main_task}\n\n## 子任务数量\n{len(subtasks)}\n\n## 子任务列表\n" + "\n".join([f"- [{s.get('role', 'worker')}] {s.get('goal', '')}" for s in subtasks]),
            {'session_id': session_id, 'task_type': subtasks[0].get('context', 'general') if subtasks else 'general'})
        
        logger.info(f"Swarm session created: {session_id} with {len(subtasks)} subtasks")
        return session_id

    def get_parallel_subtasks(self, session_id: str) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT task_id, worker_type, payload FROM tasks WHERE parent_id = ? AND status = ? ORDER BY priority DESC, created_at ASC',
                       (session_id, TaskStatus.PENDING.value))
        rows = cursor.fetchall()
        conn.close()
        
        subtasks = []
        for row in rows:
            task_id, worker_type, payload_json = row
            payload = json.loads(payload_json)
            subtasks.append({
                'task_id': task_id, 'subagent_type': worker_type, 'role': payload.get('role', 'worker'),
                'goal': payload.get('goal', ''), 'context': payload.get('context', ''),
                'description': f"{payload.get('role', 'worker')}: {payload.get('goal', '')[:30]}"
            })
        return subtasks

    def complete_task(self, task_id: str, result: Dict[str, Any], key_findings: List[str] = None):
        now = datetime.now().isoformat()
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('UPDATE tasks SET status = ?, result = ?, completed_at = ?, updated_at = ? WHERE task_id = ?',
                       (TaskStatus.COMPLETED.value, json.dumps(result), now, now, task_id))
        cursor.execute('SELECT parent_id, worker_type, payload FROM tasks WHERE task_id = ?', (task_id,))
        row = cursor.fetchone()
        if row:
            parent_id, worker_type, payload_json = row
            payload = json.loads(payload_json) if payload_json else {}
            cursor.execute('UPDATE swarm_sessions SET completed_count = completed_count + 1 WHERE session_id = ?', (parent_id,))
            if key_findings or result:
                summary = result.get('summary', str(result)[:200]) if isinstance(result, dict) else str(result)[:200]
                self.memory.record_subtask_result(task_id, summary, key_findings or [], {'session_id': parent_id, 'task_type': payload.get('context', 'general')})
        conn.commit()
        conn.close()
        logger.info(f"Task completed: {task_id}")

    def fail_task(self, task_id: str, error_message: str):
        now = datetime.now().isoformat()
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('UPDATE tasks SET status = ?, error_message = ?, updated_at = ? WHERE task_id = ?',
                       (TaskStatus.FAILED.value, error_message, now, task_id))
        cursor.execute('SELECT parent_id, payload FROM tasks WHERE task_id = ?', (task_id,))
        row = cursor.fetchone()
        if row:
            parent_id, payload_json = row
            payload = json.loads(payload_json) if payload_json else {}
            self.memory.write_note(WriteTrigger.ERROR_OCCURRED, f"## 任务ID\n{task_id}\n\n## 错误信息\n```\n{error_message}\n```\n",
                                   {'session_id': parent_id, 'task_type': payload.get('context', 'general'), 'error_message': error_message})
        conn.commit()
        conn.close()
        logger.error(f"Task failed: {task_id} - {error_message}")

    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM swarm_sessions WHERE session_id = ?', (session_id,))
        row = cursor.fetchone()
        if row:
            cols = [d[0] for d in cursor.description]
            session = dict(zip(cols, row))
            cursor.execute('SELECT status, COUNT(*) FROM tasks WHERE parent_id = ? GROUP BY status', (session_id,))
            session['task_status'] = dict(cursor.fetchall())
            conn.close()
            return session
        conn.close()
        return None

    def aggregate_results(self, session_id: str) -> Dict[str, Any]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT task_id, worker_type, result, error_message FROM tasks WHERE parent_id = ? AND status = ?', (session_id, TaskStatus.COMPLETED.value))
        rows = cursor.fetchall()
        cursor.execute('SELECT main_task FROM swarm_sessions WHERE session_id = ?', (session_id,))
        main_task_row = cursor.fetchone()
        main_task = main_task_row[0] if main_task_row else ''
        conn.close()
        
        results = {'session_id': session_id, 'completed_tasks': len(rows), 'results_by_type': {}, 'errors': []}
        all_findings = []
        
        for row in rows:
            task_id, worker_type, result_json, error = row
            if worker_type not in results['results_by_type']:
                results['results_by_type'][worker_type] = []
            if result_json:
                result_data = json.loads(result_json)
                results['results_by_type'][worker_type].append({'task_id': task_id, 'result': result_data})
                if isinstance(result_data, dict) and 'key_findings' in result_data:
                    all_findings.extend(result_data['key_findings'])
            if error:
                results['errors'].append({'task_id': task_id, 'error': error})
        
        self.memory.write_note(WriteTrigger.TASK_COMPLETE,
            f"## 主任务\n{main_task}\n\n## 完成子任务数\n{len(rows)}\n\n## 关键发现汇总\n" + "\n".join([f"- {f}" for f in all_findings[:10]]),
            {'session_id': session_id})
        
        return results
