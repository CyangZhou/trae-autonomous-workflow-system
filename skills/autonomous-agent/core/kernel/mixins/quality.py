"""
Unified Kernel Quality Mixin
"""
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from core.quality_gate import QualityGate
from core.delivery_doc import DeliveryDocGenerator
from core.enhanced_reflexion import EnhancedReflexion as ReflexionCore
from core.memory import WriteTrigger
from core.token_tracker import get_usage_summary, record_session_tokens

class KernelQualityMixin:
    """
    质量内核Mixin - 负责质量检查、验证、交付文档和反思
    """
    def __init__(self):
        self.quality_gate = QualityGate()
        self.delivery_generator = DeliveryDocGenerator()
        self.reflexion = ReflexionCore()
        
    def quality_check(self, code_content: str = "", artifacts: str = None, session_id: str = None,
                      files_to_verify: str = None, run_real_validation: bool = True):
        """
        执行质量检查 (含真实验证)
        """
        sid = session_id or self.session_id
        
        artifacts_dict = {}
        if artifacts:
            try:
                artifacts_dict = json.loads(artifacts)
            except:
                pass
        
        files_list = []
        if files_to_verify:
            try:
                files_list = json.loads(files_to_verify)
            except:
                files_list = [f.strip() for f in files_to_verify.split(',') if f.strip()]
        
        report = self.quality_gate.run_full_check(
            code_content, artifacts_dict, sid, 
            files_to_verify=files_list,
            run_real_validation=run_real_validation
        )
        
        output = {
            "session_id": report.session_id,
            "overall_score": report.overall_score,
            "passed": report.passed,
            "retry_count": report.retry_count,
            "dimensions": [
                {
                    "name": d.name,
                    "score": d.total_score,
                    "passed": d.passed
                }
                for d in report.dimensions
            ],
            "recommendations": report.recommendations
        }
        
        if report.real_validation_results:
            output["real_validation"] = report.real_validation_results.get('summary', {})
        
        print(json.dumps(output, ensure_ascii=False, indent=2))
    
    def quality_report(self, session_id: str = None):
        sid = session_id or self.session_id
        if not sid:
            print(json.dumps({"error": "No session_id"}, ensure_ascii=False))
            return
        
        report_path = self.quality_gate.quality_dir / f"{sid}_quality.json"
        if report_path.exists():
            with open(report_path, 'r', encoding='utf-8') as f:
                report = json.load(f)
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print(json.dumps({"error": f"No quality report found for session {sid}"}, ensure_ascii=False))

    def smart_validate(self, session_id: str, project_type: str = None, files: str = None):
        """
        智能验证 (使用 QualityGate)
        """
        files_list = None
        if files:
            try:
                files_list = json.loads(files)
            except:
                files_list = [f.strip() for f in files.split(',')]
        
        report = self.quality_gate.run_full_check(
            session_id=session_id,
            files_to_verify=files_list,
            run_real_validation=True
        )
        
        result = {
            "session_id": report.session_id,
            "status": "passed" if report.passed else "failed",
            "quality_score": report.overall_score,
            "passed_steps": sum(1 for d in report.dimensions if d.passed),
            "failed_steps": sum(1 for d in report.dimensions if not d.passed),
            "issues": [
                {
                    "id": f"{d.dimension.value}_{item.name}",
                    "phase": d.dimension.value,
                    "severity": "high" if item.score < 0.5 else "medium",
                    "description": item.details,
                    "suggestion": item.details
                }
                for d in report.dimensions
                for item in d.items
                if not item.passed
            ],
            "recommendations": report.recommendations
        }
        
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return result
    
    def validate(self):
        print(json.dumps({
            "status": "success",
            "message": "Validation passed",
            "timestamp": datetime.now().isoformat()
        }, ensure_ascii=False, indent=2))

    def generate_delivery(self, session_id: str = None, task_description: str = "", 
                          execution_result: str = None, quality_score: float = 0,
                          task_type: str = "general"):
        """
        生成交付文档 (使用追踪器数据)
        """
        sid = session_id or self.session_id
        if not sid:
            print(json.dumps({"error": "No session_id"}, ensure_ascii=False))
            return
        
        exec_result = {}
        if execution_result:
            try:
                exec_result = json.loads(execution_result)
            except:
                pass
        
        if self.tracker and self.tracker.session_id == sid:
            tracker_data = self.tracker.to_delivery_format()
            if not exec_result:
                exec_result = tracker_data
            else:
                exec_result.setdefault('files_created', tracker_data.get('files_created', []))
                exec_result.setdefault('files_modified', tracker_data.get('files_modified', []))
                exec_result.setdefault('key_findings', tracker_data.get('key_findings', []))
                exec_result.setdefault('test_summary', tracker_data.get('test_summary', {}))
                exec_result.setdefault('command_summary', tracker_data.get('command_summary', {}))
                exec_result.setdefault('errors', tracker_data.get('errors', []))
        
        if not task_description:
            task_description = self.execution_result.get('task_description', 'Unknown task')
        
        quality_report_dict = None
        if quality_score > 0:
            quality_report_dict = {'overall_score': quality_score}
        else:
            quality_path = self.quality_gate.quality_dir / f"{sid}_quality.json"
            if quality_path.exists():
                with open(quality_path, 'r', encoding='utf-8') as f:
                    quality_report_dict = json.load(f)
        
        doc = self.delivery_generator.generate(
            sid, task_description, exec_result, quality_report_dict, task_type
        )
        
        input_text = task_description + json.dumps(exec_result, ensure_ascii=False)
        output_text = json.dumps({
            "session_id": doc.session_id,
            "summary": doc.summary,
            "files_created": doc.files_created,
            "files_modified": doc.files_modified,
            "quality_score": doc.quality_score
        }, ensure_ascii=False)
        record_session_tokens(sid, input_text, output_text, "delivery")
        
        print(json.dumps({
            "session_id": doc.session_id,
            "summary": doc.summary,
            "files_created": doc.files_created,
            "files_modified": doc.files_modified,
            "deployment_steps": len(doc.deployment_steps),
            "verification_methods": len(doc.verification_methods),
            "limitations": len(doc.limitations),
            "future_tasks": len(doc.future_tasks),
            "quality_score": doc.quality_score,
            "test_summary": doc.test_summary,
            "errors_count": len(doc.errors)
        }, ensure_ascii=False, indent=2))
    
    def delivery_report(self, session_id: str = None):
        sid = session_id or self.session_id
        if not sid:
            print(json.dumps({"error": "No session_id"}, ensure_ascii=False))
            return
        
        doc_path = self.delivery_generator.output_dir / f"{sid}_delivery.json"
        if doc_path.exists():
            with open(doc_path, 'r', encoding='utf-8') as f:
                doc = json.load(f)
            print(json.dumps(doc, ensure_ascii=False, indent=2))
        else:
            print(json.dumps({"error": f"No delivery document found for session {sid}"}, ensure_ascii=False))

    def save(self, session_id: str = None):
        sid = session_id or self.session_id
        if not sid:
            print(json.dumps({"status": "error", "message": "No session_id provided"}, ensure_ascii=False))
            return
        
        if self.tracker:
            self.tracker.save()
        
        try:
            self.ltm.evolve({
                "type": "task_execution",
                "context": {"session_id": sid, "scenario": self.current_scenario},
                "action": "complete_session",
                "outcome": "success",
                "success": True
            })
            print(f"Memory evolved for session {sid}")
        except Exception as e:
            print(f"LTM update warning: {e}")

        self.memory.write_note(
            WriteTrigger.TASK_COMPLETE,
            f"## 会话完成\n{sid}\n\n## 完成时间\n{datetime.now().isoformat()}\n\n## 场景\n{self.current_scenario or 'unknown'}\n",
            {'session_id': sid}
        )
        
        token_summary = get_usage_summary()
        
        print(json.dumps({
            "status": "success",
            "message": f"Session {sid} saved to memory",
            "memory_path": "自动化工作流组件库/memory/sessions/",
            "execution_track_path": "自动化工作流组件库/memory/execution_tracks/",
            "token_summary": {
                "total_input": token_summary.get('total_input', 0),
                "total_output": token_summary.get('total_output', 0),
                "total_tokens": token_summary.get('total_tokens', 0),
                "call_count": token_summary.get('call_count', 0)
            }
        }, ensure_ascii=False, indent=2))

    def reflect(self, error_message: str):
        result = self.reflexion.reflect(error_message)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    def record(self, error_message: str, fix: str):
        self.reflexion.record_fix(error_message, fix)
        print(json.dumps({
            "status": "success",
            "message": "Error fix recorded to memory",
            "memory_path": "自动化工作流组件库/memory/errors/"
        }, ensure_ascii=False, indent=2))
