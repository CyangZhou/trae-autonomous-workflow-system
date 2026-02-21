"""
Execution Tracker v1.0 - 执行结果追踪模块
解决交付文档空洞问题：追踪实际文件变更、命令执行、错误记录
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum

from .paths import get_memory_dir, ensure_dir


class ChangeType(Enum):
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"


@dataclass
class FileChange:
    path: str
    change_type: ChangeType
    timestamp: str
    size_before: int = 0
    size_after: int = 0
    diff_summary: str = ""
    verified: bool = False


@dataclass
class CommandExecution:
    command: str
    exit_code: int
    timestamp: str
    output_summary: str = ""
    error_summary: str = ""
    duration_ms: int = 0


@dataclass
class TestResult:
    test_name: str
    passed: bool
    timestamp: str
    details: str = ""
    error_message: str = ""


@dataclass
class VerificationCheck:
    check_name: str
    passed: bool
    timestamp: str
    details: str = ""
    automated: bool = True


class ExecutionTracker:
    """
    执行追踪器 - 记录任务执行过程中的所有实际变更
    
    解决问题:
    1. 交付文档 summary 为空
    2. files_created/files_modified 为空
    3. 无法验证实际做了什么
    
    使用方式:
    tracker = ExecutionTracker(session_id)
    tracker.track_file_create("path/to/file.py")
    tracker.track_command("npm test", 0, "All tests passed")
    result = tracker.to_dict()
    """
    
    def __init__(self, session_id: str = None, project_root: str = None):
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.start_time = datetime.now()
        
        self.file_changes: List[FileChange] = []
        self.commands: List[CommandExecution] = []
        self.test_results: List[TestResult] = []
        self.verifications: List[VerificationCheck] = []
        self.errors: List[Dict[str, Any]] = []
        self.key_findings: List[str] = []
        
        self._memory_dir = get_memory_dir()
        self._tracker_dir = self._memory_dir / 'execution_tracks'
        ensure_dir(self._tracker_dir)
    
    def track_file_create(self, path: str, content_preview: str = "") -> FileChange:
        """追踪文件创建"""
        abs_path = self._resolve_path(path)
        
        change = FileChange(
            path=str(abs_path.relative_to(self.project_root)) if abs_path.is_relative_to(self.project_root) else path,
            change_type=ChangeType.CREATED,
            timestamp=datetime.now().isoformat(),
            size_after=abs_path.stat().st_size if abs_path.exists() else 0,
            diff_summary=content_preview[:200] if content_preview else "",
            verified=abs_path.exists()
        )
        
        self.file_changes.append(change)
        self._save_incremental()
        return change
    
    def track_file_modify(self, path: str, diff_summary: str = "", size_before: int = 0) -> FileChange:
        """追踪文件修改"""
        abs_path = self._resolve_path(path)
        
        change = FileChange(
            path=str(abs_path.relative_to(self.project_root)) if abs_path.is_relative_to(self.project_root) else path,
            change_type=ChangeType.MODIFIED,
            timestamp=datetime.now().isoformat(),
            size_before=size_before,
            size_after=abs_path.stat().st_size if abs_path.exists() else 0,
            diff_summary=diff_summary[:500] if diff_summary else "",
            verified=abs_path.exists()
        )
        
        self.file_changes.append(change)
        self._save_incremental()
        return change
    
    def track_file_delete(self, path: str) -> FileChange:
        """追踪文件删除"""
        change = FileChange(
            path=path,
            change_type=ChangeType.DELETED,
            timestamp=datetime.now().isoformat(),
            verified=not self._resolve_path(path).exists()
        )
        
        self.file_changes.append(change)
        self._save_incremental()
        return change
    
    def track_command(self, command: str, exit_code: int, 
                      output: str = "", error: str = "", 
                      duration_ms: int = 0) -> CommandExecution:
        """追踪命令执行"""
        exec_record = CommandExecution(
            command=command,
            exit_code=exit_code,
            timestamp=datetime.now().isoformat(),
            output_summary=output[:1000] if output else "",
            error_summary=error[:500] if error else "",
            duration_ms=duration_ms
        )
        
        self.commands.append(exec_record)
        
        if exit_code != 0:
            self.errors.append({
                "type": "command_failure",
                "command": command,
                "exit_code": exit_code,
                "error": error[:200] if error else "",
                "timestamp": exec_record.timestamp
            })
        
        self._save_incremental()
        return exec_record
    
    def track_test(self, test_name: str, passed: bool, 
                   details: str = "", error_message: str = "") -> TestResult:
        """追踪测试结果"""
        result = TestResult(
            test_name=test_name,
            passed=passed,
            timestamp=datetime.now().isoformat(),
            details=details[:500] if details else "",
            error_message=error_message[:500] if error_message else ""
        )
        
        self.test_results.append(result)
        self._save_incremental()
        return result
    
    def track_verification(self, check_name: str, passed: bool,
                          details: str = "", automated: bool = True) -> VerificationCheck:
        """追踪验证检查"""
        check = VerificationCheck(
            check_name=check_name,
            passed=passed,
            timestamp=datetime.now().isoformat(),
            details=details[:500] if details else "",
            automated=automated
        )
        
        self.verifications.append(check)
        self._save_incremental()
        return check
    
    def add_finding(self, finding: str):
        """添加关键发现"""
        self.key_findings.append(finding)
        self._save_incremental()
    
    def add_error(self, error_type: str, message: str, context: Dict = None):
        """添加错误记录"""
        self.errors.append({
            "type": error_type,
            "message": message,
            "context": context or {},
            "timestamp": datetime.now().isoformat()
        })
        self._save_incremental()
    
    def get_files_created(self) -> List[str]:
        """获取创建的文件列表"""
        return [c.path for c in self.file_changes if c.change_type == ChangeType.CREATED]
    
    def get_files_modified(self) -> List[str]:
        """获取修改的文件列表"""
        return [c.path for c in self.file_changes if c.change_type == ChangeType.MODIFIED]
    
    def get_files_deleted(self) -> List[str]:
        """获取删除的文件列表"""
        return [c.path for c in self.file_changes if c.change_type == ChangeType.DELETED]
    
    def get_test_summary(self) -> Dict[str, int]:
        """获取测试摘要"""
        return {
            "total": len(self.test_results),
            "passed": sum(1 for t in self.test_results if t.passed),
            "failed": sum(1 for t in self.test_results if not t.passed)
        }
    
    def get_verification_summary(self) -> Dict[str, Any]:
        """获取验证摘要"""
        return {
            "total": len(self.verifications),
            "passed": sum(1 for v in self.verifications if v.passed),
            "failed": sum(1 for v in self.verifications if not v.passed),
            "automated": sum(1 for v in self.verifications if v.automated)
        }
    
    def get_command_summary(self) -> Dict[str, Any]:
        """获取命令执行摘要"""
        return {
            "total": len(self.commands),
            "successful": sum(1 for c in self.commands if c.exit_code == 0),
            "failed": sum(1 for c in self.commands if c.exit_code != 0)
        }
    
    def calculate_quality_score(self) -> float:
        """计算质量评分 (基于实际验证结果)"""
        if not self.verifications and not self.test_results:
            return 0.0
        
        scores = []
        
        if self.verifications:
            verification_score = sum(1 for v in self.verifications if v.passed) / len(self.verifications)
            scores.append(verification_score)
        
        if self.test_results:
            test_score = sum(1 for t in self.test_results if t.passed) / len(self.test_results)
            scores.append(test_score * 1.5)
        
        if self.commands:
            cmd_success_rate = sum(1 for c in self.commands if c.exit_code == 0) / len(self.commands)
            scores.append(cmd_success_rate)
        
        if self.errors:
            error_penalty = min(0.3, len(self.errors) * 0.1)
            scores.append(1.0 - error_penalty)
        
        return min(1.0, sum(scores) / len(scores)) if scores else 0.0
    
    def generate_summary(self) -> str:
        """生成任务摘要"""
        parts = []
        
        created = self.get_files_created()
        modified = self.get_files_modified()
        tests = self.get_test_summary()
        verifications = self.get_verification_summary()
        commands = self.get_command_summary()
        
        if created:
            parts.append(f"创建了 {len(created)} 个文件")
        if modified:
            parts.append(f"修改了 {len(modified)} 个文件")
        if tests["total"] > 0:
            parts.append(f"运行了 {tests['total']} 个测试 ({tests['passed']} 通过)")
        if commands["total"] > 0:
            parts.append(f"执行了 {commands['total']} 个命令")
        if verifications["total"] > 0:
            parts.append(f"完成了 {verifications['total']} 项验证")
        
        if parts:
            return "，".join(parts) + "。"
        
        return "任务已执行完成。"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "summary": self.generate_summary(),
            "files_created": self.get_files_created(),
            "files_modified": self.get_files_modified(),
            "files_deleted": self.get_files_deleted(),
            "file_changes_detail": [
                {
                    "path": c.path,
                    "type": c.change_type.value,
                    "timestamp": c.timestamp,
                    "verified": c.verified,
                    "size_after": c.size_after
                }
                for c in self.file_changes
            ],
            "commands": [
                {
                    "command": c.command,
                    "exit_code": c.exit_code,
                    "timestamp": c.timestamp,
                    "success": c.exit_code == 0
                }
                for c in self.commands
            ],
            "test_results": [
                {
                    "name": t.test_name,
                    "passed": t.passed,
                    "timestamp": t.timestamp
                }
                for t in self.test_results
            ],
            "verifications": [
                {
                    "name": v.check_name,
                    "passed": v.passed,
                    "automated": v.automated,
                    "timestamp": v.timestamp
                }
                for v in self.verifications
            ],
            "errors": self.errors,
            "key_findings": self.key_findings,
            "statistics": {
                "files_created": len(self.get_files_created()),
                "files_modified": len(self.get_files_modified()),
                "commands_run": len(self.commands),
                "tests_run": len(self.test_results),
                "tests_passed": sum(1 for t in self.test_results if t.passed),
                "verifications_passed": sum(1 for v in self.verifications if v.passed),
                "errors_count": len(self.errors)
            },
            "quality_score": self.calculate_quality_score()
        }
    
    def to_delivery_format(self) -> Dict[str, Any]:
        """转换为交付文档格式"""
        return {
            "files_created": self.get_files_created(),
            "files_modified": self.get_files_modified(),
            "key_findings": self.key_findings,
            "quality_score": self.calculate_quality_score(),
            "test_summary": self.get_test_summary(),
            "verification_summary": self.get_verification_summary(),
            "command_summary": self.get_command_summary(),
            "errors": [
                {"type": e["type"], "message": e.get("message", e.get("error", ""))}
                for e in self.errors
            ]
        }
    
    def save(self) -> Path:
        """保存追踪记录"""
        save_path = self._tracker_dir / f"{self.session_id}_execution.json"
        
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        
        return save_path
    
    def _save_incremental(self):
        """增量保存 (防止意外中断丢失数据)"""
        self.save()
    
    def _resolve_path(self, path: str) -> Path:
        """解析路径"""
        p = Path(path)
        if p.is_absolute():
            return p
        return self.project_root / path
    
    @classmethod
    def load(cls, session_id: str) -> Optional['ExecutionTracker']:
        """加载已有追踪记录"""
        tracker_dir = get_memory_dir() / 'execution_tracks'
        load_path = tracker_dir / f"{session_id}_execution.json"
        
        if not load_path.exists():
            return None
        
        with open(load_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        tracker = cls(session_id, data.get('project_root'))
        
        for change_data in data.get('file_changes_detail', []):
            change = FileChange(
                path=change_data['path'],
                change_type=ChangeType(change_data['type']),
                timestamp=change_data['timestamp'],
                verified=change_data.get('verified', False),
                size_after=change_data.get('size_after', 0)
            )
            tracker.file_changes.append(change)
        
        for cmd_data in data.get('commands', []):
            cmd = CommandExecution(
                command=cmd_data['command'],
                exit_code=cmd_data['exit_code'],
                timestamp=cmd_data['timestamp']
            )
            tracker.commands.append(cmd)
        
        tracker.key_findings = data.get('key_findings', [])
        tracker.errors = data.get('errors', [])
        
        return tracker


_tracker_instance: Optional[ExecutionTracker] = None


def get_tracker(session_id: str = None, project_root: str = None) -> ExecutionTracker:
    """获取全局追踪器实例"""
    global _tracker_instance
    if _tracker_instance is None or (session_id and _tracker_instance.session_id != session_id):
        _tracker_instance = ExecutionTracker(session_id, project_root)
    return _tracker_instance


def reset_tracker(session_id: str = None):
    """重置追踪器"""
    global _tracker_instance
    _tracker_instance = ExecutionTracker(session_id) if session_id else None
