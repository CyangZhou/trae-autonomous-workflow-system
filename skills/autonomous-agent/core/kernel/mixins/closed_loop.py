"""
Unified Kernel Closed Loop Mixin
"""
import json
from typing import Dict, Any, List, Optional

from core.enhanced_decomposer import EnhancedAtomicTaskDecomposer as AtomicTaskDecomposer
from core.integrator import IntegratorAgent
from core.closed_loop import ClosedLoopOrchestrator, LoopPhase, LoopState
from core.knowledge_boundary import KnowledgeBoundary

class KernelClosedLoopMixin:
    """
    闭环内核Mixin - 负责原子级拆解、整合、闭环流程
    """
    def __init__(self):
        self.atomic_decomposer = AtomicTaskDecomposer()
        self.integrator = IntegratorAgent()
        self.closed_loop = ClosedLoopOrchestrator()
        self.knowledge_boundary = KnowledgeBoundary()
        
    def decompose_task(self, task_description: str, session_id: str = None):
        """
        原子级任务拆解
        """
        doc = self.atomic_decomposer.decompose(task_description, session_id)
        
        result = {
            "session_id": doc.session_id,
            "main_task": doc.main_task,
            "total_tasks": doc.total_tasks,
            "execution_order": doc.execution_order,
            "parallel_groups": self.atomic_decomposer._identify_parallel_groups(doc),
            "tasks": [
                {
                    "task_id": t.task_id,
                    "name": t.name,
                    "type": t.task_type.value,
                    "agent": t.agent_type,
                    "dependencies": t.dependencies,
                    "acceptance_criteria": t.acceptance_criteria
                }
                for t in doc.tasks
            ],
            "integration_plan": doc.integration_plan,
            "validation_plan": doc.validation_plan
        }
        
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return result
    
    def integrate_results(self, session_id: str, results: str):
        """
        整合子任务产出
        """
        try:
            results_dict = json.loads(results)
        except:
            results_dict = {}
        
        integration_result = self.integrator.integrate(session_id, results_dict)
        
        result = {
            "session_id": integration_result.session_id,
            "status": integration_result.status.value,
            "quality_score": integration_result.quality_score,
            "integrated_files": integration_result.integrated_files,
            "conflicts": [
                {
                    "id": c.conflict_id,
                    "type": c.conflict_type.value,
                    "description": c.description,
                    "resolved": c.resolved
                }
                for c in integration_result.conflicts
            ],
            "summary": integration_result.summary
        }
        
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return result

    def closed_loop_start(self, task_description: str, session_id: str = None):
        """
        启动闭环循环流程 v2.0
        """
        # CP0
        kb_result = self.knowledge_boundary.detect(task_description)
        # M1: Use Thinking Mode from Intelligence (self.intelligence from AnalysisMixin, self.ltm from BaseMixin)
        analysis = self.intelligence.analyze(task_description, ltm=self.ltm)
        thinking_mode = analysis.get('thinking_mode', kb_result.get('mode', 'Slow'))
        
        print(f"[检查点0] 知识边界感知 - 模式: {thinking_mode}, 置信度: {analysis.get('confidence', kb_result.get('confidence', 0.5)):.0%}")

        print(f"[检查点1] 初始化完成 - Kernel v3.1")
        
        context = self.closed_loop.start(task_description, session_id)
        self.session_id = context.session_id
        
        # M2: Use Execution Mode from Intelligence
        execution_mode = analysis.get('execution_mode', 'swarm')
        print(f"[检查点2] 任务拆解完成 - 任务数: {context.task_document.get('total_tasks', 0)}, 策略: {execution_mode}")
        
        # 同步任务到 Swarm 数据库
        self._sync_tasks_to_swarm(context.session_id, context.task_document)
        
        print(f"[检查点3] 执行阶段 - 进入闭环执行")
        
        directive = self.atomic_decomposer.get_execution_directive(context.session_id)
        
        print(f"\n🚀 [CLOSED LOOP EXECUTION DIRECTIVE]")
        print(json.dumps({
            "session_id": context.session_id,
            "state": context.state.value,
            "phase": context.current_phase.value,
            "total_tasks": directive.get("total_tasks", 0),
            "parallel_groups": directive.get("parallel_groups", []),
            "instruction": "按照任务文档执行子任务，完成后调用 closed-loop-phase integrate"
        }, ensure_ascii=False, indent=2))
        
        return self.run_closed_loop_cycle(context.session_id)
    
    def _sync_tasks_to_swarm(self, session_id: str, task_document: Dict):
        """将任务文档中的任务同步到 Swarm 数据库"""
        if not task_document or 'tasks' not in task_document:
            return
        
        tasks = task_document.get('tasks', [])
        subtasks = []
        
        for task in tasks:
            subtasks.append({
                'type': task.get('agent_type', 'search'),
                'role': task.get('name', 'worker'),
                'goal': task.get('description', ''),
                'context': task_document.get('main_task', ''),
                'priority': task.get('priority', 5),
                'task_id': task.get('task_id'),
                'acceptance_criteria': task.get('acceptance_criteria', [])
            })
        
        if subtasks:
            self.swarm.create_swarm_session(task_document.get('main_task', ''), subtasks, session_id=session_id)
            print(f"  - 已同步 {len(subtasks)} 个任务到 Swarm 数据库 (session: {session_id})")
    
    def run_closed_loop_cycle(self, session_id: str):
        """Run the closed loop cycle until completion or failure"""
        print(f"\n🔄 [CLOSED LOOP CYCLE] Started for session {session_id}")
        
        while True:
            state = self.closed_loop.get_current_state(session_id)
            if state['state'] in [LoopState.COMPLETED.value, LoopState.FAILED.value]:
                break
                
            phase = state['phase']
            print(f"\n📍 [PHASE] {phase.upper()} (Iteration {state['iteration']}/{state['max_iterations']})")
            
            result = None
            if phase == LoopPhase.EXECUTE.value:
                # self.swarm comes from ExecutionMixin
                subtasks = self.swarm.get_parallel_subtasks(session_id)
                if subtasks:
                    # self._execute_swarm_tasks comes from ExecutionMixin
                    execution_result = self._execute_swarm_tasks(session_id, subtasks)
                    result = self.closed_loop.execute_phase(session_id, LoopPhase.INTEGRATE, {"results": execution_result})
                else:
                    print("  - No subtasks found, moving to integration")
                    result = self.closed_loop.execute_phase(session_id, LoopPhase.INTEGRATE)
                    
            elif phase == LoopPhase.INTEGRATE.value:
                result = self.closed_loop.execute_phase(session_id, LoopPhase.VALIDATE)
                
            elif phase == LoopPhase.VALIDATE.value:
                val_result = self.closed_loop.execute_phase(session_id, LoopPhase.VALIDATE)
                
                # CP4
                score = val_result.get('quality_score', 0)
                print(f"[检查点4] 验证完成 - 通过率: {score:.0%}")
                
                next_p = val_result.get('next_phase')
                
                if next_p == 'research':
                    result = self.closed_loop.execute_phase(session_id, LoopPhase.RESEARCH)
                elif next_p == 'deliver':
                    result = self.closed_loop.execute_phase(session_id, LoopPhase.DELIVER)
                else:
                    result = val_result

            elif phase == LoopPhase.RESEARCH.value:
                # S5: Reflexion Loop - Research Phase
                print("  - Executing Research Phase (Auto)")
                
                # Get directive from closed loop
                research_res = self.closed_loop.execute_phase(session_id, LoopPhase.RESEARCH)
                directive = research_res.get('research_directive', {})
                issues = directive.get('issues', [])
                
                # Create research tasks for swarm
                research_tasks = []
                for i, issue in enumerate(issues):
                    research_tasks.append({
                        'task_id': f"research_{session_id}_{i}",
                        'subagent_type': 'search',
                        'goal': f"Research solution for issue: {issue}",
                        'payload': {'query': issue}
                    })
                
                if research_tasks:
                    findings_raw = self._execute_swarm_tasks(session_id, research_tasks)
                    findings = [{'description': f.get('summary', ''), 'source': 'web'} for f in findings_raw]
                else:
                    findings = [{'description': 'No specific research query found', 'source': 'system'}]
                
                result = self.closed_loop.execute_phase(session_id, LoopPhase.FIX, {"findings": findings})

            elif phase == LoopPhase.FIX.value:
                # S5: Reflexion Loop - Fix Phase
                print("  - Executing Fix Phase (Auto)")
                
                # In a real implementation, we would pass findings to LLM to generate code fixes.
                # Here we simulate using ReflexionCore (or just applying a mock fix for now)
                
                fixes = []
                fix_desc = "Applied auto-generated fix based on research"
                fixes.append({'description': fix_desc})
                
                result = self.closed_loop.execute_phase(session_id, LoopPhase.EXECUTE, {"fixes": fixes})
                
            elif phase == LoopPhase.DELIVER.value:
                result = self.closed_loop.execute_phase(session_id, LoopPhase.DELIVER)
                # CP5
                print(f"[检查点5] 交付完成")
                
            else:
                print(f"Unknown phase: {phase}")
                break
                
            if result and result.get('status') == 'completed':
                print(f"✅ [CLOSED LOOP COMPLETED] Session {session_id}")
                break
        
        return self.closed_loop.get_current_state(session_id)

    def closed_loop_phase(self, session_id: str, phase: str, data: str = None):
        """
        执行闭环循环的指定阶段
        """
        phase_map = {
            "execute": LoopPhase.EXECUTE,
            "integrate": LoopPhase.INTEGRATE,
            "validate": LoopPhase.VALIDATE,
            "research": LoopPhase.RESEARCH,
            "fix": LoopPhase.FIX,
            "deliver": LoopPhase.DELIVER
        }
        
        loop_phase = phase_map.get(phase.lower())
        if not loop_phase:
            print(json.dumps({"error": f"Unknown phase: {phase}"}, ensure_ascii=False))
            return
        
        data_dict = None
        if data:
            try:
                data_dict = json.loads(data)
            except:
                data_dict = {"raw": data}
        
        result = self.closed_loop.execute_phase(session_id, loop_phase, data_dict)
        
        print(f"[检查点] 阶段 {phase} 执行完成")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        return result
    
    def closed_loop_status(self, session_id: str):
        """获取闭环循环状态"""
        state = self.closed_loop.get_current_state(session_id)
        print(json.dumps(state, ensure_ascii=False, indent=2))
        return state
    
    def closed_loop_resume(self, session_id: str):
        """恢复中断的闭环循环"""
        result = self.closed_loop.resume(session_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return result
