"""
Unified Kernel Analysis Mixin
"""
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from core.intelligence import IntelligentAssistant
from core.scenario_selector import ScenarioSelector, ScenarioType
from core.skill_discovery import SkillDiscovery
from core.smart_router import SmartRouter
from core.intelligent_monitor import IntelligentMonitor
from core.token_tracker import estimate_tokens, estimate_tokens_for_dict, record_session_tokens
from core.execution_tracker import get_tracker
from core.memory import WriteTrigger

class KernelAnalysisMixin:
    """
    分析内核Mixin - 负责任务分析、路由、场景选择、技能发现
    """
    def __init__(self):
        self.intelligence = IntelligentAssistant()
        self.scenario_selector = ScenarioSelector()
        self.skill_discovery = SkillDiscovery()
        self.smart_router = SmartRouter()
        self.intelligent_monitor = IntelligentMonitor()
        
    def analyze(self, task_description: str):
        # Pass LTM for Adaptive Specialization
        result = self.intelligence.analyze(task_description, ltm=self.ltm)
        
        self.current_scenario = result.get('scenario', 'plan_review')
        
        record_session_tokens(
            self.session_id or "pre-analysis",
            task_description,
            json.dumps(result, ensure_ascii=False),
            task_type=result.get('task_type', 'analysis')
        )
        
        if result['execution_mode'] == 'swarm':
            # Note: self.swarm comes from ExecutionMixin
            self.session_id = self.swarm.create_swarm_session(task_description, result.get('subtasks', []))
            result['session_id'] = self.session_id
            
            self.tracker = get_tracker(self.session_id)
            
            self.memory.write_note(
                WriteTrigger.TASK_START,
                f"## 任务\n{task_description}\n\n## 场景\n{result.get('scenario_name', 'unknown')}\n\n## 复杂度\n{result['complexity_score']}\n\n## 子任务\n" +
                "\n".join([f"- [{s.get('role', 'worker')}] {s.get('goal', '')}" for s in result.get('subtasks', [])]),
                {'session_id': self.session_id, 'task_type': result.get('task_type', 'general'), 'complexity': result['complexity_score'], 'scenario': self.current_scenario}
            )
        
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    def scenario(self, task_description: str = None):
        if task_description:
            result = self.intelligence.get_scenario_for_task(task_description)
        elif self.current_scenario:
            scenario_info = self.scenario_selector.get_scenario_by_type(ScenarioType(self.current_scenario))
            result = {
                'scenario': self.current_scenario,
                'scenario_name': scenario_info.name if scenario_info else 'unknown',
                'description': scenario_info.description if scenario_info else ''
            }
        else:
            result = {'error': 'No scenario available'}
        
        print(json.dumps(result, ensure_ascii=False, indent=2))

    def discover_skills(self, task_description: str, task_type: str = None):
        # Pass LTM for Adaptive Specialization
        result = self.skill_discovery.discover(task_description, task_type, ltm=self.ltm)
        
        print(json.dumps({
            "task_description": result.task_description,
            "task_type": result.task_type,
            "best_match": {
                "name": result.best_match.name,
                "source": result.best_match.source.value,
                "score": result.best_match.relevance_score
            } if result.best_match else None,
            "all_matches": [
                {"name": m.name, "source": m.source.value, "score": m.relevance_score}
                for m in result.all_matches[:5]
            ],
            "recommendations": result.recommendations
        }, ensure_ascii=False, indent=2))
    
    def list_skills(self):
        result = self.skill_discovery.list_available_skills()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    def route(self, task_description: str):
        """
        智能路由 - 分析任务并推荐执行方式
        """
        decision = self.smart_router.route(task_description)
        
        result = {
            "task_description": task_description,
            "task_type": decision.task_type.value,
            "execution_mode": decision.execution_mode.value,
            "confidence": decision.confidence,
            "matched_workflow": decision.matched_workflow,
            "reason": decision.reason,
            "recommendations": decision.recommendations
        }
        
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        # 如果匹配到工作流，自动执行
        if decision.matched_workflow and decision.execution_mode.value == "workflow":
            print(f"\n[检查点] 自动执行匹配的工作流: {decision.matched_workflow}")
            # Note: self.workflow comes from ExecutionMixin
            return self.workflow.run(decision.matched_workflow)
        
        return result
    
    def monitor(self):
        """
        智能监控 - 分析项目上下文并推荐工作流
        """
        report = self.intelligent_monitor.get_monitoring_report()
        print(json.dumps(report, ensure_ascii=False, indent=2))
        
        # 如果有高置信度推荐，提示用户
        if report.get('workflow_recommendations'):
            top_rec = report['workflow_recommendations'][0]
            if top_rec['confidence'] >= 0.7:
                print(f"\n💡 建议执行工作流: {top_rec['workflow']} (置信度: {top_rec['confidence']:.0%})")
                print(f"   原因: {top_rec['reason']}")
        
        return report
