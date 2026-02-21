"""
Unified Kernel Execution Mixin
"""
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List, Optional

from core.swarm import SwarmOrchestrator
from core.workflow import WorkflowRunner
from core.execution_tracker import get_tracker
from core.token_tracker import get_usage_summary, estimate_tokens, record_usage, record_session_tokens
from core.workers.worker_coder import CoderWorker
from core.workers.worker_researcher import ResearchWorker

class KernelExecutionMixin:
    """
    执行内核Mixin - 负责Swarm执行、工作流执行、追踪和Token管理
    """
    def __init__(self):
        self.swarm = SwarmOrchestrator()
        self.workflow = WorkflowRunner()
        
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
    
    def get_execution_directive(self, session_id: str = None):
        """获取执行指令 - 用于 Agent 直接执行子任务"""
        sid = session_id or self.session_id
        if not sid:
            print(json.dumps({"status": "error", "message": "No session_id provided"}, ensure_ascii=False))
            return
        
        directive = self.swarm.get_execution_directive(sid)
        
        print(json.dumps({
            "status": "success",
            "execution_directive": directive,
            "action_required": "EXECUTE_SUBTASKS" if directive.get('subtasks') else "NO_TASKS"
        }, ensure_ascii=False, indent=2))
    
    def _execute_swarm_tasks(self, session_id: str, subtasks: list):
        """Execute swarm tasks in parallel"""
        print(f"\n🚀 [PARALLEL EXECUTION] Starting {len(subtasks)} tasks...")
        
        results = []
        
        def get_worker(w_type):
            w_type = w_type.lower()
            if 'search' in w_type or 'research' in w_type:
                return ResearchWorker()
            return CoderWorker()

        with ThreadPoolExecutor(max_workers=min(len(subtasks), 10)) as executor:
            future_to_task = {}
            for task in subtasks:
                worker = get_worker(task.get('subagent_type', ''))
                payload = task.get('payload', {})
                
                # Ensure payload has action for CoderWorker
                if isinstance(worker, CoderWorker) and 'action' not in payload:
                    goal_lower = task.get('goal', '').lower()
                    if '创建' in goal_lower or '新建' in goal_lower or '编写' in goal_lower or 'write' in goal_lower:
                        payload['action'] = 'write'
                        if 'file_path' not in payload:
                            payload['file_path'] = f"output_{task['task_id'][:8]}.py"
                        if 'content' not in payload:
                            payload['content'] = f"# Auto-generated file\n# Task: {task.get('goal', '')}\n\nprint('Hello from auto-generated script!')\n"
                    elif 'read' in goal_lower or '读取' in goal_lower:
                        payload['action'] = 'read'
                    elif '分析' in goal_lower or 'analyze' in goal_lower:
                        payload['action'] = 'analyze'
                        if 'file_path' not in payload:
                            payload['file_path'] = 'output.txt'
                    else:
                        payload['action'] = 'write'
                        if 'file_path' not in payload:
                            payload['file_path'] = f"output_{task['task_id'][:8]}.py"
                        if 'content' not in payload:
                            payload['content'] = f"# Auto-generated file\n# Task: {task.get('goal', '')}\n\nprint('Hello from auto-generated script!')\n"

                print(f"  - Submitting task {task['task_id']} to {worker.worker_type}")
                future = executor.submit(worker.execute, payload)
                future_to_task[future] = task

            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    result = future.result()
                    self.swarm.complete_task(task['task_id'], result)
                    results.append(result)
                    print(f"  - ✅ Task {task['task_id']} completed")
                except Exception as e:
                    self.swarm.fail_task(task['task_id'], str(e))
                    print(f"  - ❌ Task {task['task_id']} failed: {e}")
        
        return self.swarm.aggregate_results(session_id)

    def full_workflow(self, task_description: str):
        # M3: Safety check logic is not here, but can be invoked if needed.
        
        print(f"[检查点1] ✅ 初始化完成 - Kernel v2.0 initialized")
        
        # Note: self.intelligence comes from AnalysisMixin, self.ltm comes from BaseMixin
        analysis = self.intelligence.analyze(task_description, ltm=self.ltm)
        self.current_scenario = analysis.get('scenario', 'plan_review')
        
        print(f"[检查点2] ✅ 任务解析完成")
        print(f"  - 核心目标: {task_description[:50]}...")
        print(f"  - 技术领域: {analysis.get('task_type', 'unknown')}")
        print(f"  - 复杂度分数: {analysis['complexity_score']}")
        print(f"  - 执行模式: {analysis['execution_mode']}")
        print(f"  - 置信度: {analysis.get('confidence', 0.0)}")

        rec_workflows = [w['name'] for w in analysis.get('recommended_workflows', [])]
        rec_skills = analysis.get('recommended_skills', [])
        
        print(f"[检查点3] ✅ 智能推荐完成")
        print(f"  - 项目类型: {analysis.get('task_type', 'general')}")
        print(f"  - 推荐工作流: {', '.join(rec_workflows) if rec_workflows else 'None'}")
        print(f"  - 推荐技能: {', '.join(rec_skills) if rec_skills else 'None'}")
        print(f"  - 执行模式确认: {analysis['execution_mode']}")
        
        print(f"[检查点4] ✅ 执行模式选择 - 已调用: {analysis['execution_mode']}")
        
        execution_directive = None
        
        # Check for Specialized Skill (Adaptive Specialization)
        skill_discovery = analysis.get('skill_discovery', {})
        best_match = skill_discovery.get('best_match')
        
        if best_match and best_match.get('source') == 'local' and best_match.get('name') != 'autonomous-agent':
            skill_name = best_match.get('name')
            print(f"  - 🎯 发现最佳匹配技能: {skill_name}")
            
            execution_directive = {
                'type': 'skill',
                'skill_name': skill_name,
                'instruction': f"SKILL_EXECUTION_REQUIRED: Invoke skill '{skill_name}' immediately."
            }
            
            print(f"\n🚀 [EXECUTION DIRECTIVE - SKILL MODE]")
            print(json.dumps(execution_directive, ensure_ascii=False, indent=2))
            
        elif analysis['execution_mode'] == 'swarm':
            self.session_id = self.swarm.create_swarm_session(task_description, analysis.get('subtasks', []))
            self.tracker = get_tracker(self.session_id)
            print(f"  - Swarm Session ID: {self.session_id}")
            print(f"  - 技能调用: swarm-orchestrator")
            print(f"  - 执行追踪器: 已初始化")
            
            subtasks = self.swarm.get_parallel_subtasks(self.session_id)
            execution_directive = {
                'type': 'swarm',
                'session_id': self.session_id,
                'subtasks': subtasks,
                'instruction': f"PARALLEL_EXECUTION_REQUIRED: Execute {len(subtasks)} subtasks using Task tool in parallel"
            }
            
            print(f"\n🚀 [EXECUTION DIRECTIVE - SWARM MODE]")
            print(json.dumps(execution_directive, ensure_ascii=False, indent=2))
            
        else:
            print(f"  - 技能调用: workflow-runner")
            
            if rec_workflows:
                best_workflow = rec_workflows[0]
                print(f"  - 自动执行工作流: {best_workflow}")
                
                execution_directive = {
                    'type': 'workflow',
                    'workflow_name': best_workflow,
                    'instruction': f"WORKFLOW_EXECUTION_REQUIRED: Run workflow '{best_workflow}'"
                }
                
                result = self.workflow.run(best_workflow)
                execution_directive['result'] = result
                
                if result['status'] == 'success':
                    print(f"  - ✅ 工作流执行成功")
                    output_lines = result.get('output', '').split('\n') if result.get('output') else []
                    print("  - 输出摘要:")
                    for line in output_lines[-10:]:
                        print(f"    {line}")
                else:
                    print(f"  - ❌ 工作流执行失败")
                    print(f"    Error: {result.get('message', 'Unknown error')}")
                    execution_directive['fallback_required'] = True
                    
                print(f"\n🚀 [EXECUTION DIRECTIVE - WORKFLOW MODE]")
                print(json.dumps(execution_directive, ensure_ascii=False, indent=2))
            else:
                execution_plan = analysis.get('execution_plan', {})
                phases = execution_plan.get('phases', [])
                
                print("  - 无匹配工作流，生成执行计划:")
                for i, phase in enumerate(phases, 1):
                    print(f"    {i}. {phase['name']}: {phase['description']}")
                
                execution_directive = {
                    'type': 'plan',
                    'phases': phases,
                    'instruction': f"PLAN_EXECUTION_REQUIRED: Execute {len(phases)} phases sequentially"
                }
                
                print(f"\n🚀 [EXECUTION DIRECTIVE - PLAN MODE]")
                print(json.dumps(execution_directive, ensure_ascii=False, indent=2))
        
        print("\nℹ️  [NEXT STEPS]")
        print("> After execution, you MUST:")
        print("> 1. Track files: `track-file --path <file> --action create/modify`")
        print("> 2. Track commands: `track-command --cmd <command> --exit <code>`")
        print("> 3. Verify results: `quality --session <id> --files <files>`")
        print("> 4. Generate delivery: `delivery --session <id>`")
        print("> 5. Save session: `save --session <id>`")
        
        token_summary = get_usage_summary()
        print(f"\n📊 [TOKEN USAGE]")
        print(f"  - 总输入Token: {token_summary.get('total_input', 0):,}")
        print(f"  - 总输出Token: {token_summary.get('total_output', 0):,}")
        print(f"  - 总Token数: {token_summary.get('total_tokens', 0):,}")
        print(f"  - 调用次数: {token_summary.get('call_count', 0)}")
        if token_summary.get('call_count', 0) > 0:
            print(f"  - 平均Token/调用: {token_summary.get('avg_tokens_per_call', 0):.1f}")

        self.execution_result = {
            'task_description': task_description,
            'scenario': self.current_scenario,
            'analysis': analysis,
            'execution_directive': execution_directive
        }
        
        result = {
            'status': 'success',
            'analysis': analysis,
            'execution_directive': execution_directive,
            'session_id': self.session_id
        }
        
        print("\n📤 [RETURN DATA FOR CONTINUATION]")
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        
        return result

    # Tracking methods
    def track_file(self, path: str, action: str = "create", diff_summary: str = ""):
        if not self.tracker:
            self.tracker = get_tracker(self.session_id)
        
        if action == "create":
            change = self.tracker.track_file_create(path, diff_summary)
        elif action == "modify":
            change = self.tracker.track_file_modify(path, diff_summary)
        elif action == "delete":
            change = self.tracker.track_file_delete(path)
        else:
            print(json.dumps({"error": f"Unknown action: {action}"}, ensure_ascii=False))
            return
        
        print(json.dumps({
            "status": "success",
            "action": action,
            "path": change.path,
            "verified": change.verified,
            "timestamp": change.timestamp
        }, ensure_ascii=False, indent=2))
    
    def track_command(self, command: str, exit_code: int, output: str = "", error: str = ""):
        if not self.tracker:
            self.tracker = get_tracker(self.session_id)
        
        exec_record = self.tracker.track_command(command, exit_code, output, error)
        
        print(json.dumps({
            "status": "success",
            "command": exec_record.command,
            "exit_code": exec_record.exit_code,
            "success": exec_record.exit_code == 0,
            "timestamp": exec_record.timestamp
        }, ensure_ascii=False, indent=2))
    
    def track_test(self, test_name: str, passed: bool, details: str = "", error_message: str = ""):
        if not self.tracker:
            self.tracker = get_tracker(self.session_id)
        
        result = self.tracker.track_test(test_name, passed, details, error_message)
        
        print(json.dumps({
            "status": "success",
            "test_name": result.test_name,
            "passed": result.passed,
            "timestamp": result.timestamp
        }, ensure_ascii=False, indent=2))
    
    def track_verification(self, check_name: str, passed: bool, details: str = "", automated: bool = True):
        if not self.tracker:
            self.tracker = get_tracker(self.session_id)
        
        check = self.tracker.track_verification(check_name, passed, details, automated)
        
        print(json.dumps({
            "status": "success",
            "check_name": check.check_name,
            "passed": check.passed,
            "automated": check.automated,
            "timestamp": check.timestamp
        }, ensure_ascii=False, indent=2))
    
    def add_finding(self, finding: str):
        if not self.tracker:
            self.tracker = get_tracker(self.session_id)
        
        self.tracker.add_finding(finding)
        
        print(json.dumps({
            "status": "success",
            "finding": finding,
            "total_findings": len(self.tracker.key_findings)
        }, ensure_ascii=False, indent=2))
    
    def get_tracker_summary(self, session_id: str = None):
        sid = session_id or self.session_id
        
        from core.execution_tracker import ExecutionTracker # Local import to avoid circular dependency
        if self.tracker and self.tracker.session_id == sid:
            tracker = self.tracker
        else:
            tracker = ExecutionTracker.load(sid)
        
        if not tracker:
            print(json.dumps({"error": f"No tracker found for session {sid}"}, ensure_ascii=False))
            return
        
        summary = tracker.to_dict()
        
        print(json.dumps({
            "session_id": summary["session_id"],
            "summary": summary["summary"],
            "statistics": summary["statistics"],
            "quality_score": summary["quality_score"]
        }, ensure_ascii=False, indent=2))
        
    def token_usage(self):
        summary = get_usage_summary()
        print(json.dumps({
            "status": "success",
            "token_usage": summary
        }, ensure_ascii=False, indent=2))
    
    def record_tools_usage(self, session_id: str = None, tool_calls: str = None, 
                           input_estimate: int = 0, output_estimate: int = 0,
                           task_type: str = "tool_calls"):
        
        sid = session_id or self.session_id or "tool-session"
        
        if tool_calls and input_estimate == 0:
            input_estimate = estimate_tokens(tool_calls)
        
        if input_estimate == 0 and output_estimate == 0:
            print(json.dumps({
                "status": "error",
                "message": "No token estimates provided"
            }, ensure_ascii=False))
            return
        
        result = record_usage("trae-tools", input_estimate, output_estimate, task_type, sid)
        
        print(json.dumps({
            "status": "success",
            "session_id": sid,
            "recorded": {
                "input_tokens": input_estimate,
                "output_tokens": output_estimate,
                "total_tokens": input_estimate + output_estimate
            },
            "cumulative_summary": get_usage_summary()
        }, ensure_ascii=False, indent=2))
    
    def estimate_session(self, session_id: str = None, description: str = ""):
        sid = session_id or self.session_id or "estimated-session"
        
        current_summary = get_usage_summary()
        
        print(json.dumps({
            "session_id": sid,
            "description": description,
            "current_tracked": current_summary,
            "instruction": "Agent should estimate tool calls and call record-tools to log them"
        }, ensure_ascii=False, indent=2))
