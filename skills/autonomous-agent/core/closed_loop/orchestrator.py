"""
Closed Loop Orchestrator
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from core.enhanced_decomposer import EnhancedAtomicTaskDecomposer as AtomicTaskDecomposer, TaskDocument
from core.integrator import IntegratorAgent
from core.quality_gate import QualityGate
from core.memory import MemoryManager, WriteTrigger
from core.token_tracker import record_session_tokens

from .models import LoopState, LoopPhase, LoopContext, LoopResult

class ClosedLoopOrchestrator:
    """
    闭环循环编排器
    
    核心流程:
    1. DECOMPOSE: 原子级任务拆解 → 生成任务文档
    2. EXECUTE: 蜂群并行执行 → 收集产出
    3. INTEGRATE: 整合智能体打结 → 生成成品
    4. VALIDATE: 智能验证流程 → 汇总问题
    5. LOOP: 如果有问题 → 联网查找 → 修复 → 重新验证
    6. DELIVER: 无问题 → 交付完成
    """
    
    MAX_ITERATIONS = 5
    
    def __init__(self, output_dir: str = None):
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path("自动化工作流组件库/memory/closed_loop")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.decomposer = AtomicTaskDecomposer()
        self.integrator = IntegratorAgent()
        self.validator = QualityGate()
        self.memory = MemoryManager()
        
        self.contexts: Dict[str, LoopContext] = {}
    
    def start(self, task_description: str, session_id: str = None) -> LoopContext:
        """
        启动闭环流程
        
        步骤:
        1. 初始化上下文
        2. 执行任务拆解
        3. 返回执行指令
        """
        session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        
        context = LoopContext(
            session_id=session_id,
            main_task=task_description,
            state=LoopState.INITIALIZED,
            current_phase=LoopPhase.DECOMPOSE,
            iteration=1,
            max_iterations=self.MAX_ITERATIONS
        )
        
        self.contexts[session_id] = context
        
        self._record_history(context, "INIT", f"启动闭环流程: {task_description[:50]}")
        
        context.state = LoopState.DECOMPOSING
        task_doc = self.decomposer.decompose(task_description, session_id)
        context.task_document = self._doc_to_dict(task_doc)
        
        context.state = LoopState.EXECUTING
        context.current_phase = LoopPhase.EXECUTE
        
        self._save_context(context)
        
        self.memory.write_note(
            WriteTrigger.TASK_START,
            f"## 闭环任务\n{task_description}\n\n## 会话ID\n{session_id}\n\n## 任务数\n{task_doc.total_tasks}",
            {'session_id': session_id, 'loop_mode': True}
        )
        
        record_session_tokens(
            session_id,
            task_description,
            f"Closed loop started with {task_doc.total_tasks} tasks",
            "closed_loop_init"
        )
        
        return context
    
    def _doc_to_dict(self, doc: TaskDocument) -> Dict:
        """转换任务文档为字典"""
        from dataclasses import asdict
        result = {
            "session_id": doc.session_id,
            "main_task": doc.main_task,
            "created_at": doc.created_at,
            "total_tasks": doc.total_tasks,
            "dependency_graph": doc.dependency_graph,
            "execution_order": doc.execution_order,
            "integration_plan": doc.integration_plan,
            "validation_plan": doc.validation_plan,
            "tasks": []
        }
        
        for task in doc.tasks:
            task_dict = asdict(task)
            task_dict["task_type"] = task.task_type.value
            task_dict["atomicity"] = task.atomicity.value
            result["tasks"].append(task_dict)
        
        return result
    
    def execute_phase(self, session_id: str, phase: LoopPhase, 
                      data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        执行指定阶段
        
        支持的阶段:
        - EXECUTE: 执行子任务
        - INTEGRATE: 整合产出
        - VALIDATE: 验证结果
        - RESEARCH: 联网研究
        - FIX: 修复问题
        - DELIVER: 交付完成
        """
        context = self.contexts.get(session_id)
        
        if not context:
            context = self._load_context(session_id)
            if not context:
                return {"error": f"No context found for session {session_id}"}
            self.contexts[session_id] = context
        
        if phase == LoopPhase.EXECUTE:
            return self._execute_tasks(context, data)
        elif phase == LoopPhase.INTEGRATE:
            return self._execute_integration(context)
        elif phase == LoopPhase.VALIDATE:
            return self._execute_validation(context)
        elif phase == LoopPhase.RESEARCH:
            return self._execute_research(context, data)
        elif phase == LoopPhase.FIX:
            return self._execute_fix(context, data)
        elif phase == LoopPhase.DELIVER:
            return self._execute_delivery(context)
        else:
            return {"error": f"Unknown phase: {phase}"}
    
    def _execute_tasks(self, context: LoopContext, data: Dict) -> Dict[str, Any]:
        """执行子任务阶段"""
        self._record_history(context, "EXECUTE", "开始执行子任务")
        
        if data and "results" in data:
            context.execution_results = data["results"]
        
        directive = self.decomposer.get_execution_directive(context.session_id)
        
        return {
            "phase": "execute",
            "session_id": context.session_id,
            "status": "ready_for_execution",
            "execution_directive": directive,
            "instruction": """
# 执行指令

## 任务列表
根据任务文档中的执行顺序，按依赖关系执行子任务。

## 并行策略
- 无依赖的任务可并行执行
- 有依赖的任务按顺序执行

## 输出要求
每个子任务完成后，记录:
- task_id: 任务ID
- status: 执行状态
- files: 生成的文件
- content: 主要内容
- issues: 遇到的问题
"""
        }
    
    def _execute_integration(self, context: LoopContext) -> Dict[str, Any]:
        """执行整合阶段"""
        self._record_history(context, "INTEGRATE", "开始整合产出")
        
        context.state = LoopState.INTEGRATING
        context.current_phase = LoopPhase.INTEGRATE
        
        result = self.integrator.integrate(
            context.session_id,
            context.execution_results
        )
        
        context.integration_result = {
            "status": result.status.value,
            "integrated_files": result.integrated_files,
            "quality_score": result.quality_score,
            "summary": result.summary,
            "conflicts": [
                {
                    "id": c.conflict_id,
                    "type": c.conflict_type.value,
                    "description": c.description,
                    "resolved": c.resolved
                }
                for c in result.conflicts
            ]
        }
        
        self._save_context(context)
        
        return {
            "phase": "integrate",
            "session_id": context.session_id,
            "status": result.status.value,
            "quality_score": result.quality_score,
            "integrated_files": result.integrated_files,
            "conflicts_count": len(result.conflicts),
            "next_phase": "validate"
        }
    
    def _execute_validation(self, context: LoopContext) -> Dict[str, Any]:
        """执行验证阶段"""
        self._record_history(context, "VALIDATE", "开始验证")
        
        context.state = LoopState.VALIDATING
        context.current_phase = LoopPhase.VALIDATE
        
        result = self.validator.run_full_check(
            session_id=context.session_id,
            artifacts=context.artifacts,
            files_to_verify=context.integrated_files,
            run_real_validation=True
        )
        
        context.validation_result = {
            "status": "passed" if result.passed else "failed",
            "quality_score": result.overall_score,
            "passed_steps": sum(1 for d in result.dimensions if d.passed),
            "failed_steps": sum(1 for d in result.dimensions if not d.passed),
            "issues": [
                {
                    "id": f"{d.dimension.value}_{item.name}",
                    "phase": d.dimension.value,
                    "severity": "high" if item.score < 0.5 else "medium",
                    "description": item.details,
                    "suggestion": item.details,
                    "resolved": False
                }
                for d in result.dimensions
                for item in d.items
                if not item.passed
            ],
            "recommendations": result.recommendations
        }
        
        context.issues_found = context.validation_result["issues"]
        
        self._save_context(context)
        
        should_loop, reason = self._should_loop_back(context)
        
        if should_loop:
            context.state = LoopState.LOOPING
            context.current_phase = LoopPhase.RESEARCH
            self._record_history(context, "LOOP", f"需要循环: {reason}")
            
            return {
                "phase": "validate",
                "session_id": context.session_id,
                "status": "needs_fix",
                "quality_score": result.overall_score,
                "issues_count": len(context.validation_result["issues"]),
                "reason": reason,
                "next_phase": "research"
            }
        else:
            context.state = LoopState.COMPLETED
            context.current_phase = LoopPhase.DELIVER
            self._record_history(context, "SUCCESS", "验证通过，准备交付")
            
            return {
                "phase": "validate",
                "session_id": context.session_id,
                "status": "passed",
                "quality_score": result.overall_score,
                "next_phase": "deliver"
            }
    
    def _execute_research(self, context: LoopContext, data: Dict) -> Dict[str, Any]:
        """执行研究阶段 - 联网查找解决方案"""
        self._record_history(context, "RESEARCH", "联网查找解决方案")
        
        context.state = LoopState.RESEARCHING
        context.current_phase = LoopPhase.RESEARCH
        
        research_directive = self.validator.get_research_directive(context.session_id)
        
        if data and "findings" in data:
            context.research_findings = data["findings"]
            context.current_phase = LoopPhase.FIX
            self._save_context(context)
            
            return {
                "phase": "research",
                "session_id": context.session_id,
                "status": "findings_received",
                "findings_count": len(data["findings"]),
                "next_phase": "fix"
            }
        
        return {
            "phase": "research",
            "session_id": context.session_id,
            "status": "research_required",
            "research_directive": research_directive,
            "instruction": """
# 研究指令

## 目标
联网查找以下问题的解决方案:
{issues}

## 研究来源
1. GitHub 开源项目 - 查找类似实现
2. 官方文档 - 查找最佳实践
3. Stack Overflow - 查找问题解答
4. 技术博客 - 查找深度分析

## 输出要求
整理找到的解决方案:
- 问题ID
- 解决方案描述
- 参考来源
- 实施步骤
""".format(issues="\n".join([f"- {i['description']}" for i in context.issues_found[:5]]))
        }
    
    def _execute_fix(self, context: LoopContext, data: Dict) -> Dict[str, Any]:
        """执行修复阶段"""
        self._record_history(context, "FIX", "应用修复方案")
        
        context.state = LoopState.FIXING
        context.current_phase = LoopPhase.FIX
        
        if data and "fixes" in data:
            context.fixes_applied = data["fixes"]
        
        context.iteration += 1
        
        if context.iteration > context.max_iterations:
            context.state = LoopState.FAILED
            self._record_history(context, "FAIL", f"达到最大迭代次数 {context.max_iterations}")
            self._save_context(context)
            
            return {
                "phase": "fix",
                "session_id": context.session_id,
                "status": "max_iterations_reached",
                "iterations": context.iteration,
                "message": "已达到最大迭代次数，需要人工介入"
            }
        
        context.state = LoopState.EXECUTING
        context.current_phase = LoopPhase.EXECUTE
        
        self._save_context(context)
        
        return {
            "phase": "fix",
            "session_id": context.session_id,
            "status": "fixes_applied",
            "iteration": context.iteration,
            "next_phase": "execute",
            "message": f"开始第 {context.iteration} 轮执行"
        }
    
    def _execute_delivery(self, context: LoopContext) -> Dict[str, Any]:
        """执行交付阶段"""
        self._record_history(context, "DELIVER", "生成交付物")
        
        context.state = LoopState.COMPLETED
        
        delivery = {
            "session_id": context.session_id,
            "main_task": context.main_task,
            "completed_at": datetime.now().isoformat(),
            "iterations": context.iteration,
            "task_document": context.task_document,
            "execution_results": context.execution_results,
            "integration_result": context.integration_result,
            "validation_result": context.validation_result,
            "research_findings": context.research_findings,
            "fixes_applied": context.fixes_applied,
            "issues_resolved": len([f for f in context.fixes_applied]),
            "issues_remaining": len([i for i in context.issues_found if not i.get("resolved", False)])
        }
        
        self._save_delivery(delivery)
        
        self.memory.write_note(
            WriteTrigger.TASK_COMPLETE,
            f"## 闭环任务完成\n{context.main_task}\n\n## 迭代次数\n{context.iteration}\n\n## 解决问题\n{len(context.fixes_applied)}",
            {'session_id': context.session_id}
        )
        
        record_session_tokens(
            context.session_id,
            "delivery_generation",
            f"Closed loop completed with {context.iteration} iterations",
            "closed_loop_delivery"
        )
        
        return {
            "phase": "deliver",
            "session_id": context.session_id,
            "status": "completed",
            "delivery": delivery,
            "summary": self._generate_summary(context)
        }
    
    def _should_loop_back(self, context: LoopContext) -> Tuple[bool, str]:
        """判断是否需要循环"""
        if not context.validation_result:
            return True, "无验证结果"
        
        quality_score = context.validation_result.get("quality_score", 0)
        
        if quality_score >= 0.9:
            return False, "验证通过率优秀"
        
        if quality_score >= 0.7:
            unresolved = [i for i in context.issues_found if not i.get("resolved", False)]
            if not unresolved:
                return False, "所有问题已解决"
            return True, f"存在 {len(unresolved)} 个未解决问题"
        
        return True, f"验证通过率 {quality_score:.0%} 低于阈值"
    
    def _record_history(self, context: LoopContext, action: str, detail: str):
        """记录历史"""
        context.history.append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "detail": detail,
            "iteration": context.iteration,
            "state": context.state.value,
            "phase": context.current_phase.value
        })
    
    def _save_context(self, context: LoopContext):
        """保存上下文"""
        context_path = self.output_dir / f"{context.session_id}_context.json"
        
        context_dict = {
            "session_id": context.session_id,
            "main_task": context.main_task,
            "state": context.state.value,
            "current_phase": context.current_phase.value,
            "iteration": context.iteration,
            "max_iterations": context.max_iterations,
            "task_document": context.task_document,
            "execution_results": context.execution_results,
            "integration_result": context.integration_result,
            "validation_result": context.validation_result,
            "research_findings": context.research_findings,
            "issues_found": context.issues_found,
            "fixes_applied": context.fixes_applied,
            "history": context.history
        }
        
        with open(context_path, 'w', encoding='utf-8') as f:
            json.dump(context_dict, f, ensure_ascii=False, indent=2)
    
    def _load_context(self, session_id: str) -> Optional[LoopContext]:
        """加载上下文"""
        context_path = self.output_dir / f"{session_id}_context.json"
        
        if not context_path.exists():
            return None
        
        with open(context_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return LoopContext(
            session_id=data["session_id"],
            main_task=data["main_task"],
            state=LoopState(data["state"]),
            current_phase=LoopPhase(data["current_phase"]),
            iteration=data["iteration"],
            max_iterations=data["max_iterations"],
            task_document=data.get("task_document"),
            execution_results=data.get("execution_results", {}),
            integration_result=data.get("integration_result"),
            validation_result=data.get("validation_result"),
            research_findings=data.get("research_findings", []),
            issues_found=data.get("issues_found", []),
            fixes_applied=data.get("fixes_applied", []),
            history=data.get("history", [])
        )
    
    def _save_delivery(self, delivery: Dict[str, Any]):
        """保存交付物"""
        delivery_path = self.output_dir / f"{delivery['session_id']}_delivery.json"
        
        with open(delivery_path, 'w', encoding='utf-8') as f:
            json.dump(delivery, f, ensure_ascii=False, indent=2)
    
    def _generate_summary(self, context: LoopContext) -> str:
        """生成摘要"""
        lines = [
            f"# 闭环执行报告",
            f"",
            f"## 任务概览",
            f"- 主任务: {context.main_task[:100]}",
            f"- 会话ID: {context.session_id}",
            f"- 总迭代次数: {context.iteration}",
            f"- 最终状态: {context.state.value}",
            f"",
            f"## 执行统计",
        ]
        
        if context.task_document:
            lines.append(f"- 任务数: {context.task_document.get('total_tasks', 0)}")
        
        if context.validation_result:
            lines.append(f"- 验证通过率: {context.validation_result.get('quality_score', 0):.0%}")
            lines.append(f"- 通过步骤: {context.validation_result.get('passed_steps', 0)}")
            lines.append(f"- 失败步骤: {context.validation_result.get('failed_steps', 0)}")
        
        lines.extend([
            f"",
            f"## 问题处理",
            f"- 发现问题: {len(context.issues_found)}",
            f"- 应用修复: {len(context.fixes_applied)}",
            f"- 研究发现: {len(context.research_findings)}",
        ])
        
        return "\n".join(lines)
    
    def get_current_state(self, session_id: str) -> Dict[str, Any]:
        """获取当前状态"""
        context = self.contexts.get(session_id) or self._load_context(session_id)
        
        if not context:
            return {"error": f"No context found for session {session_id}"}
        
        return {
            "session_id": context.session_id,
            "state": context.state.value,
            "phase": context.current_phase.value,
            "iteration": context.iteration,
            "max_iterations": context.max_iterations,
            "issues_count": len(context.issues_found),
            "fixes_count": len(context.fixes_applied),
            "next_action": self._get_next_action(context)
        }
    
    def _get_next_action(self, context: LoopContext) -> str:
        """获取下一步动作"""
        phase_actions = {
            LoopPhase.DECOMPOSE: "执行子任务",
            LoopPhase.EXECUTE: "整合产出",
            LoopPhase.INTEGRATE: "验证结果",
            LoopPhase.VALIDATE: "检查是否需要循环",
            LoopPhase.RESEARCH: "联网查找解决方案",
            LoopPhase.FIX: "应用修复方案",
            LoopPhase.DELIVER: "生成交付物"
        }
        
        return phase_actions.get(context.current_phase, "未知")
    
    def resume(self, session_id: str) -> Dict[str, Any]:
        """恢复中断的闭环流程"""
        context = self._load_context(session_id)
        
        if not context:
            return {"error": f"No context found for session {session_id}"}
        
        self.contexts[session_id] = context
        
        return {
            "session_id": session_id,
            "status": "resumed",
            "current_state": self.get_current_state(session_id),
            "instruction": f"""
# 恢复执行

## 当前状态
- 阶段: {context.current_phase.value}
- 迭代: {context.iteration}/{context.max_iterations}
- 状态: {context.state.value}

## 下一步
{self._get_next_action(context)}
"""
        }
