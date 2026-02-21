"""
Enhanced Atomic Task Decomposer v2.0 - 增强版原子级任务拆解器
核心功能:
1. 整合知识边界感知 (KnowSelf)
2. 整合长期记忆 (LTM)
3. 智能复杂度评估
4. 自适应任务拆解策略

升级点:
- 根据知识边界感知决定拆解深度
- 从长期记忆中检索相关经验
- 动态调整拆解策略
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum

from .knowledge_boundary import KnowledgeBoundaryAwareness, ThinkingMode, KnowledgeDomain
from .ltm import LongTermMemory


class AtomicityLevel(Enum):
    ATOMIC = "atomic"
    COMPOUND = "compound"
    COMPLEX = "complex"


class TaskType(Enum):
    CODE_WRITE = "code_write"
    CODE_MODIFY = "code_modify"
    CODE_REVIEW = "code_review"
    DOC_WRITE = "doc_write"
    TEST_WRITE = "test_write"
    RESEARCH = "research"
    DEPLOY = "deploy"
    INTEGRATE = "integrate"
    VALIDATE = "validate"


class DecompositionStrategy(Enum):
    ONE_SHOT = "one_shot"
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HYBRID = "hybrid"
    KNOWLEDGE_ENHANCED = "knowledge_enhanced"


@dataclass
class AtomicTask:
    task_id: str
    name: str
    description: str
    task_type: TaskType
    atomicity: AtomicityLevel
    agent_type: str
    dependencies: List[str] = field(default_factory=list)
    inputs: List[str] = field(default_factory=list)
    expected_outputs: List[str] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)
    estimated_complexity: int = 1
    priority: int = 5
    context: str = ""
    reference_docs: List[str] = field(default_factory=list)
    error_handling: str = ""
    timeout_seconds: int = 300
    thinking_mode: str = "slow"
    knowledge_required: List[str] = field(default_factory=list)


@dataclass
class TaskDocument:
    session_id: str
    main_task: str
    created_at: str
    total_tasks: int
    tasks: List[AtomicTask]
    dependency_graph: Dict[str, List[str]]
    execution_order: List[str]
    integration_plan: Dict[str, Any]
    validation_plan: Dict[str, Any]
    decomposition_strategy: str
    confidence_assessment: Dict[str, Any]
    relevant_memory: List[Dict[str, Any]]


class EnhancedAtomicTaskDecomposer:
    """
    增强版原子级任务拆解器
    
    核心升级:
    1. 知识边界感知 - 根据置信度决定拆解深度
    2. 长期记忆检索 - 从历史经验中学习
    3. 自适应策略 - 动态选择最佳拆解策略
    4. 智能复杂度评估 - 多维度分析
    """
    
    TASK_TYPE_PATTERNS = {
        TaskType.CODE_WRITE: [
            r"创建|新建|编写|实现|开发|构建",
            r"写一个|做一个|实现一个",
        ],
        TaskType.CODE_MODIFY: [
            r"修改|更新|优化|重构|修复|改进",
            r"改一下|优化一下|修复.*bug",
        ],
        TaskType.CODE_REVIEW: [
            r"审查|检查|review|代码评审",
        ],
        TaskType.DOC_WRITE: [
            r"文档|说明|readme|文档化",
        ],
        TaskType.TEST_WRITE: [
            r"测试|test|单元测试|集成测试",
        ],
        TaskType.RESEARCH: [
            r"研究|调研|分析|查找|搜索|了解",
            r"联网|查阅|调查",
        ],
        TaskType.DEPLOY: [
            r"部署|发布|上线|deploy",
        ],
        TaskType.INTEGRATE: [
            r"整合|集成|合并|组合|打结",
        ],
        TaskType.VALIDATE: [
            r"验证|校验|检查|确认",
        ],
    }
    
    AGENT_MAPPING = {
        TaskType.CODE_WRITE: "backend-architect",
        TaskType.CODE_MODIFY: "backend-architect",
        TaskType.CODE_REVIEW: "search",
        TaskType.DOC_WRITE: "feishu-doc-master",
        TaskType.TEST_WRITE: "testing-validation-expert",
        TaskType.RESEARCH: "search",
        TaskType.DEPLOY: "release-ops-expert",
        TaskType.INTEGRATE: "project-orchestrator",
        TaskType.VALIDATE: "testing-validation-expert",
    }
    
    def __init__(self, output_dir: str = None):
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path("自动化工作流组件库/memory/task_docs")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.knowledge_boundary = KnowledgeBoundaryAwareness()
        self.ltm = LongTermMemory()
    
    def decompose(self, task_description: str, session_id: str = None) -> TaskDocument:
        """
        主入口: 智能拆解任务
        
        升级流程:
        1. 知识边界感知评估
        2. 检索相关记忆
        3. 确定拆解策略
        4. 执行拆解
        5. 生成文档
        """
        session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        
        thinking_decision = self.knowledge_boundary.decide_thinking_mode(task_description)
        
        relevant_memory = self.ltm.retrieve_relevant(task_description, top_k=3)
        
        main_task_type = self._detect_task_type(task_description)
        complexity = self._estimate_complexity_enhanced(task_description, relevant_memory)
        
        strategy = self._determine_strategy(thinking_decision, complexity, relevant_memory)
        
        tasks = self._decompose_with_strategy(
            task_description, session_id, main_task_type, 
            strategy, thinking_decision, relevant_memory
        )
        
        dependency_graph = self._build_dependency_graph(tasks)
        execution_order = self._topological_sort(tasks, dependency_graph)
        integration_plan = self._create_integration_plan(tasks, task_description)
        validation_plan = self._create_validation_plan(tasks, task_description)
        
        doc = TaskDocument(
            session_id=session_id,
            main_task=task_description,
            created_at=datetime.now().isoformat(),
            total_tasks=len(tasks),
            tasks=tasks,
            dependency_graph=dependency_graph,
            execution_order=execution_order,
            integration_plan=integration_plan,
            validation_plan=validation_plan,
            decomposition_strategy=strategy.value,
            confidence_assessment={
                "thinking_mode": thinking_decision.mode.value,
                "confidence": thinking_decision.confidence,
                "reasoning": thinking_decision.reasoning,
            },
            relevant_memory=[
                {
                    "type": mem_type,
                    "items": items[:2]
                }
                for mem_type, items in relevant_memory.items()
                if items
            ],
        )
        
        self._save_document(doc)
        
        return doc
    
    def _detect_task_type(self, description: str) -> TaskType:
        """检测任务类型"""
        for task_type, patterns in self.TASK_TYPE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, description, re.IGNORECASE):
                    return task_type
        return TaskType.CODE_WRITE
    
    def _estimate_complexity_enhanced(self, description: str, 
                                       relevant_memory: Dict) -> int:
        """增强版复杂度评估"""
        base_score = 1
        
        complexity_indicators = [
            (r"并", 2), (r"多个", 2), (r"完整", 2),
            (r"系统", 3), (r"架构", 3), (r"集成", 2),
            (r"部署", 2), (r"测试", 1), (r"文档", 1),
            (r"验证", 1), (r"优化", 2), (r"重构", 3),
            (r"分布式", 4), (r"微服务", 4), (r"高并发", 3),
        ]
        
        for pattern, weight in complexity_indicators:
            if re.search(pattern, description):
                base_score += weight
        
        word_count = len(description.split())
        if word_count > 100:
            base_score += 3
        elif word_count > 50:
            base_score += 2
        elif word_count > 20:
            base_score += 1
        
        memory_adjustment = 0
        if relevant_memory.get("episodic"):
            memory_adjustment -= 1
        if relevant_memory.get("procedural"):
            memory_adjustment -= 2
        
        return max(1, min(10, base_score + memory_adjustment))
    
    def _determine_strategy(self, thinking_decision, complexity: int,
                            relevant_memory: Dict) -> DecompositionStrategy:
        """确定拆解策略"""
        if thinking_decision.mode == ThinkingMode.FAST:
            return DecompositionStrategy.ONE_SHOT
        
        if thinking_decision.mode == ThinkingMode.KNOWLEDGE:
            return DecompositionStrategy.KNOWLEDGE_ENHANCED
        
        if complexity <= 2:
            return DecompositionStrategy.ONE_SHOT
        elif complexity <= 4:
            return DecompositionStrategy.SEQUENTIAL
        elif complexity <= 6:
            return DecompositionStrategy.PARALLEL
        else:
            return DecompositionStrategy.HYBRID
    
    def _decompose_with_strategy(self, description: str, session_id: str,
                                  main_type: TaskType, strategy: DecompositionStrategy,
                                  thinking_decision, relevant_memory: Dict) -> List[AtomicTask]:
        """根据策略执行拆解"""
        if strategy == DecompositionStrategy.ONE_SHOT:
            return self._decompose_one_shot(description, session_id, main_type, thinking_decision)
        elif strategy == DecompositionStrategy.SEQUENTIAL:
            return self._decompose_sequential(description, session_id, main_type, thinking_decision)
        elif strategy == DecompositionStrategy.PARALLEL:
            return self._decompose_parallel(description, session_id, main_type, thinking_decision)
        elif strategy == DecompositionStrategy.KNOWLEDGE_ENHANCED:
            return self._decompose_knowledge_enhanced(description, session_id, main_type, 
                                                       thinking_decision, relevant_memory)
        else:
            return self._decompose_hybrid(description, session_id, main_type, thinking_decision)
    
    def _decompose_one_shot(self, description: str, session_id: str,
                            task_type: TaskType, thinking_decision) -> List[AtomicTask]:
        """单步拆解"""
        return [
            AtomicTask(
                task_id=f"{session_id}_T001",
                name=description[:50],
                description=description,
                task_type=task_type,
                atomicity=AtomicityLevel.ATOMIC,
                agent_type=self.AGENT_MAPPING.get(task_type, "search"),
                acceptance_criteria=[
                    f"完成: {description[:100]}",
                    "代码可运行无错误",
                ],
                estimated_complexity=1,
                priority=5,
                thinking_mode=thinking_decision.mode.value,
            )
        ]
    
    def _decompose_sequential(self, description: str, session_id: str,
                              main_type: TaskType, thinking_decision) -> List[AtomicTask]:
        """顺序拆解"""
        tasks = []
        task_counter = 1
        
        def add_task(name: str, desc: str, task_type: TaskType, 
                     deps: List[str] = None, mode: str = "slow", **kwargs):
            nonlocal task_counter
            task = AtomicTask(
                task_id=f"{session_id}_T{task_counter:03d}",
                name=name,
                description=desc,
                task_type=task_type,
                atomicity=AtomicityLevel.ATOMIC,
                agent_type=self.AGENT_MAPPING.get(task_type, "search"),
                dependencies=deps or [],
                thinking_mode=mode,
                **kwargs
            )
            tasks.append(task)
            task_counter += 1
            return task.task_id
        
        research_mode = "knowledge" if thinking_decision.should_use_web else "slow"
        research_id = add_task(
            name="需求分析与技术调研",
            desc=f"分析任务需求，确定技术方案: {description[:100]}",
            task_type=TaskType.RESEARCH,
            acceptance_criteria=[
                "明确技术选型",
                "确定实现方案",
                "识别潜在风险",
            ],
            estimated_complexity=1,
            priority=6,
            mode=research_mode,
        )
        
        impl_id = add_task(
            name="核心功能实现",
            desc=f"实现核心功能代码",
            task_type=main_type,
            dependencies=[research_id],
            acceptance_criteria=[
                "代码实现完整",
                "符合编码规范",
                "无语法错误",
            ],
            estimated_complexity=2,
            priority=5,
        )
        
        test_id = add_task(
            name="测试用例编写",
            desc="编写测试用例验证功能",
            task_type=TaskType.TEST_WRITE,
            dependencies=[impl_id],
            acceptance_criteria=[
                "测试覆盖核心功能",
                "测试用例可执行",
            ],
            estimated_complexity=1,
            priority=4,
        )
        
        add_task(
            name="整合与验证",
            desc="整合所有产出，执行验证",
            task_type=TaskType.INTEGRATE,
            dependencies=[test_id],
            acceptance_criteria=[
                "所有功能正常",
                "测试全部通过",
                "产出完整可用",
            ],
            estimated_complexity=1,
            priority=3,
        )
        
        return tasks
    
    def _decompose_parallel(self, description: str, session_id: str,
                            main_type: TaskType, thinking_decision) -> List[AtomicTask]:
        """并行拆解"""
        tasks = []
        task_counter = 1
        
        def add_task(name: str, desc: str, task_type: TaskType, 
                     deps: List[str] = None, **kwargs):
            nonlocal task_counter
            task = AtomicTask(
                task_id=f"{session_id}_T{task_counter:03d}",
                name=name,
                description=desc,
                task_type=task_type,
                atomicity=AtomicityLevel.ATOMIC,
                agent_type=self.AGENT_MAPPING.get(task_type, "search"),
                dependencies=deps or [],
                thinking_mode=thinking_decision.mode.value,
                **kwargs
            )
            tasks.append(task)
            task_counter += 1
            return task.task_id
        
        research_id = add_task(
            name="需求分析与架构设计",
            desc=f"全面分析需求，设计系统架构: {description}",
            task_type=TaskType.RESEARCH,
            acceptance_criteria=[
                "需求文档完整",
                "架构图清晰",
                "技术选型合理",
            ],
            estimated_complexity=2,
            priority=7,
        )
        
        impl_ids = []
        for i in range(1, 3):
            impl_id = add_task(
                name=f"模块{i}实现",
                desc=f"实现第{i}个核心模块",
                task_type=main_type,
                dependencies=[research_id],
                acceptance_criteria=[
                    f"模块{i}功能完整",
                    "代码质量达标",
                ],
                estimated_complexity=2,
                priority=5,
            )
            impl_ids.append(impl_id)
        
        test_id = add_task(
            name="集成测试编写",
            desc="编写集成测试",
            task_type=TaskType.TEST_WRITE,
            dependencies=impl_ids,
            acceptance_criteria=[
                "集成测试覆盖主流程",
            ],
            estimated_complexity=2,
            priority=4,
        )
        
        add_task(
            name="最终整合与交付",
            desc="整合所有产出，生成交付文档",
            task_type=TaskType.INTEGRATE,
            dependencies=[test_id],
            acceptance_criteria=[
                "交付物完整",
            ],
            estimated_complexity=1,
            priority=2,
        )
        
        return tasks
    
    def _decompose_knowledge_enhanced(self, description: str, session_id: str,
                                       main_type: TaskType, thinking_decision,
                                       relevant_memory: Dict) -> List[AtomicTask]:
        """知识增强拆解"""
        tasks = []
        task_counter = 1
        
        knowledge_gaps = thinking_decision.confidence if hasattr(thinking_decision, 'confidence') else []
        
        def add_task(name: str, desc: str, task_type: TaskType, 
                     deps: List[str] = None, knowledge_req: List[str] = None, **kwargs):
            nonlocal task_counter
            task = AtomicTask(
                task_id=f"{session_id}_T{task_counter:03d}",
                name=name,
                description=desc,
                task_type=task_type,
                atomicity=AtomicityLevel.ATOMIC,
                agent_type=self.AGENT_MAPPING.get(task_type, "search"),
                dependencies=deps or [],
                thinking_mode="knowledge",
                knowledge_required=knowledge_req or [],
                **kwargs
            )
            tasks.append(task)
            task_counter += 1
            return task.task_id
        
        research_id = add_task(
            name="深度研究与知识收集",
            desc=f"联网查找相关知识和最佳实践: {description}",
            task_type=TaskType.RESEARCH,
            acceptance_criteria=[
                "收集足够的背景知识",
                "找到相关最佳实践",
                "识别关键技术点",
            ],
            estimated_complexity=2,
            priority=7,
            knowledge_req=["外部知识检索"],
        )
        
        analysis_id = add_task(
            name="知识整合与分析",
            desc="整合收集的知识，制定实现方案",
            task_type=TaskType.RESEARCH,
            dependencies=[research_id],
            acceptance_criteria=[
                "知识整合完整",
                "方案清晰可行",
            ],
            estimated_complexity=1,
            priority=6,
        )
        
        impl_id = add_task(
            name="基于知识的实现",
            desc="根据研究知识实现功能",
            task_type=main_type,
            dependencies=[analysis_id],
            acceptance_criteria=[
                "实现符合最佳实践",
                "代码质量达标",
            ],
            estimated_complexity=2,
            priority=5,
        )
        
        test_id = add_task(
            name="验证与测试",
            desc="验证实现是否符合预期",
            task_type=TaskType.TEST_WRITE,
            dependencies=[impl_id],
            acceptance_criteria=[
                "测试通过",
                "功能验证完成",
            ],
            estimated_complexity=1,
            priority=4,
        )
        
        add_task(
            name="知识沉淀与交付",
            desc="沉淀新知识，生成交付文档",
            task_type=TaskType.INTEGRATE,
            dependencies=[test_id],
            acceptance_criteria=[
                "新知识已记录",
                "交付物完整",
            ],
            estimated_complexity=1,
            priority=3,
        )
        
        return tasks
    
    def _decompose_hybrid(self, description: str, session_id: str,
                          main_type: TaskType, thinking_decision) -> List[AtomicTask]:
        """混合拆解"""
        tasks = []
        task_counter = 1
        
        def add_task(name: str, desc: str, task_type: TaskType, 
                     deps: List[str] = None, **kwargs):
            nonlocal task_counter
            task = AtomicTask(
                task_id=f"{session_id}_T{task_counter:03d}",
                name=name,
                description=desc,
                task_type=task_type,
                atomicity=AtomicityLevel.ATOMIC,
                agent_type=self.AGENT_MAPPING.get(task_type, "search"),
                dependencies=deps or [],
                thinking_mode=thinking_decision.mode.value,
                **kwargs
            )
            tasks.append(task)
            task_counter += 1
            return task.task_id
        
        research_id = add_task(
            name="深度需求分析与架构设计",
            desc=f"全面分析需求，设计系统架构: {description}",
            task_type=TaskType.RESEARCH,
            acceptance_criteria=[
                "需求文档完整",
                "架构图清晰",
                "技术选型合理",
                "风险评估到位",
            ],
            estimated_complexity=2,
            priority=7,
        )
        
        design_id = add_task(
            name="详细设计与接口定义",
            desc="设计模块接口、数据结构、流程图",
            task_type=TaskType.DOC_WRITE,
            dependencies=[research_id],
            acceptance_criteria=[
                "接口文档完整",
                "数据结构定义清晰",
            ],
            estimated_complexity=2,
            priority=6,
        )
        
        impl_ids = []
        for i in range(1, 4):
            impl_id = add_task(
                name=f"模块{i}实现",
                desc=f"实现第{i}个核心模块",
                task_type=main_type,
                dependencies=[design_id],
                acceptance_criteria=[
                    f"模块{i}功能完整",
                    "代码质量达标",
                    "单元测试通过",
                ],
                estimated_complexity=2,
                priority=5,
            )
            impl_ids.append(impl_id)
        
        test_id = add_task(
            name="集成测试编写",
            desc="编写集成测试和端到端测试",
            task_type=TaskType.TEST_WRITE,
            dependencies=impl_ids,
            acceptance_criteria=[
                "集成测试覆盖主流程",
                "边界条件测试完整",
            ],
            estimated_complexity=2,
            priority=4,
        )
        
        validate_id = add_task(
            name="全面验证",
            desc="执行全面验证，确保质量",
            task_type=TaskType.VALIDATE,
            dependencies=[test_id],
            acceptance_criteria=[
                "所有测试通过",
                "代码审查完成",
            ],
            estimated_complexity=1,
            priority=3,
        )
        
        add_task(
            name="最终整合与交付",
            desc="整合所有产出，生成交付文档",
            task_type=TaskType.INTEGRATE,
            dependencies=[validate_id],
            acceptance_criteria=[
                "交付物完整",
                "部署指南清晰",
            ],
            estimated_complexity=1,
            priority=2,
        )
        
        return tasks
    
    def _build_dependency_graph(self, tasks: List[AtomicTask]) -> Dict[str, List[str]]:
        """构建依赖图"""
        graph = {}
        for task in tasks:
            graph[task.task_id] = task.dependencies
        return graph
    
    def _topological_sort(self, tasks: List[AtomicTask], graph: Dict[str, List[str]]) -> List[str]:
        """拓扑排序"""
        in_degree = {task.task_id: 0 for task in tasks}
        
        for task_id, deps in graph.items():
            in_degree[task_id] = len([d for d in deps if d in in_degree])
        
        queue = [tid for tid, deg in in_degree.items() if deg == 0]
        result = []
        
        while queue:
            current = queue.pop(0)
            result.append(current)
            
            for task_id, deps in graph.items():
                if current in deps:
                    in_degree[task_id] -= 1
                    if in_degree[task_id] == 0:
                        queue.append(task_id)
        
        return result
    
    def _create_integration_plan(self, tasks: List[AtomicTask], main_task: str) -> Dict[str, Any]:
        """创建整合计划"""
        integration_tasks = [t for t in tasks if t.task_type == TaskType.INTEGRATE]
        
        return {
            "integration_tasks": [t.task_id for t in integration_tasks],
            "inputs_to_integrate": [
                {
                    "task_id": t.task_id,
                    "expected_outputs": t.expected_outputs,
                    "type": t.task_type.value
                }
                for t in tasks if t.task_type != TaskType.INTEGRATE
            ],
            "integration_strategy": "sequential_merge",
            "output_format": "delivery_document",
        }
    
    def _create_validation_plan(self, tasks: List[AtomicTask], main_task: str) -> Dict[str, Any]:
        """创建验证计划"""
        return {
            "validation_phases": [
                {
                    "phase": "unit_validation",
                    "description": "单元验证 - 每个子任务完成后验证",
                },
                {
                    "phase": "integration_validation",
                    "description": "整合验证 - 整合后验证",
                },
                {
                    "phase": "final_validation",
                    "description": "最终验证 - 交付前验证",
                }
            ],
            "fallback_strategy": {
                "on_failure": "research_and_fix",
                "max_retries": 3,
            }
        }
    
    def _save_document(self, doc: TaskDocument):
        """保存任务文档"""
        doc_path = self.output_dir / f"{doc.session_id}_task_doc.json"
        
        doc_dict = {
            "session_id": doc.session_id,
            "main_task": doc.main_task,
            "created_at": doc.created_at,
            "total_tasks": doc.total_tasks,
            "tasks": [asdict(t) for t in doc.tasks],
            "dependency_graph": doc.dependency_graph,
            "execution_order": doc.execution_order,
            "integration_plan": doc.integration_plan,
            "validation_plan": doc.validation_plan,
            "decomposition_strategy": doc.decomposition_strategy,
            "confidence_assessment": doc.confidence_assessment,
            "relevant_memory": doc.relevant_memory,
        }
        
        for task in doc_dict["tasks"]:
            task["task_type"] = task["task_type"].value
            task["atomicity"] = task["atomicity"].value
        
        with open(doc_path, 'w', encoding='utf-8') as f:
            json.dump(doc_dict, f, ensure_ascii=False, indent=2)
    
    def get_execution_directive(self, session_id: str) -> Dict[str, Any]:
        """获取执行指令"""
        doc = self.load_document(session_id)
        
        if not doc:
            return {"error": f"No task document found for session {session_id}"}
        
        parallel_groups = self._identify_parallel_groups(doc)
        
        return {
            "session_id": session_id,
            "main_task": doc.main_task,
            "total_tasks": doc.total_tasks,
            "execution_order": doc.execution_order,
            "parallel_groups": parallel_groups,
            "decomposition_strategy": doc.decomposition_strategy,
            "confidence_assessment": doc.confidence_assessment,
            "tasks_detail": [
                {
                    "task_id": t.task_id,
                    "name": t.name,
                    "description": t.description,
                    "agent_type": t.agent_type,
                    "dependencies": t.dependencies,
                    "acceptance_criteria": t.acceptance_criteria,
                    "thinking_mode": t.thinking_mode,
                    "knowledge_required": t.knowledge_required,
                }
                for t in doc.tasks
            ],
        }
    
    def _identify_parallel_groups(self, doc: TaskDocument) -> List[List[str]]:
        """识别可并行执行的任务组"""
        groups = []
        remaining = set(t.task_id for t in doc.tasks)
        completed = set()
        
        while remaining:
            ready = []
            for task_id in remaining:
                deps = doc.dependency_graph.get(task_id, [])
                if all(d in completed for d in deps):
                    ready.append(task_id)
            
            if ready:
                groups.append(ready)
                completed.update(ready)
                remaining -= set(ready)
            else:
                break
        
        return groups
    
    def load_document(self, session_id: str) -> Optional[TaskDocument]:
        """加载任务文档"""
        doc_path = self.output_dir / f"{session_id}_task_doc.json"
        
        if not doc_path.exists():
            return None
        
        with open(doc_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        tasks = []
        for t in data["tasks"]:
            task = AtomicTask(
                task_id=t["task_id"],
                name=t["name"],
                description=t["description"],
                task_type=TaskType(t["task_type"]),
                atomicity=AtomicityLevel(t["atomicity"]),
                agent_type=t["agent_type"],
                dependencies=t.get("dependencies", []),
                inputs=t.get("inputs", []),
                expected_outputs=t.get("expected_outputs", []),
                acceptance_criteria=t.get("acceptance_criteria", []),
                estimated_complexity=t.get("estimated_complexity", 1),
                priority=t.get("priority", 5),
                context=t.get("context", ""),
                reference_docs=t.get("reference_docs", []),
                error_handling=t.get("error_handling", ""),
                timeout_seconds=t.get("timeout_seconds", 300),
                thinking_mode=t.get("thinking_mode", "slow"),
                knowledge_required=t.get("knowledge_required", []),
            )
            tasks.append(task)
        
        return TaskDocument(
            session_id=data["session_id"],
            main_task=data["main_task"],
            created_at=data["created_at"],
            total_tasks=data["total_tasks"],
            tasks=tasks,
            dependency_graph=data["dependency_graph"],
            execution_order=data["execution_order"],
            integration_plan=data["integration_plan"],
            validation_plan=data["validation_plan"],
            decomposition_strategy=data.get("decomposition_strategy", "sequential"),
            confidence_assessment=data.get("confidence_assessment", {}),
            relevant_memory=data.get("relevant_memory", []),
        )
