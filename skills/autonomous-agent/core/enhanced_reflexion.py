"""
Enhanced Reflexion v1.0 - 增强版反思机制
核心功能:
1. 深度自我反思 - 从失败中学习
2. 反思链追踪 - 记录反思历史
3. 策略自适应 - 根据反思结果调整策略
4. 模式提取 - 从反思中提取通用模式

参考论文: "Reflexion: Language Agents with Verbal Reinforcement Learning" (NeurIPS 2023)
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class ReflectionType(Enum):
    ERROR_ANALYSIS = "error_analysis"
    STRATEGY_REVIEW = "strategy_review"
    OUTCOME_EVALUATION = "outcome_evaluation"
    PATTERN_DISCOVERY = "pattern_discovery"
    SELF_IMPROVEMENT = "self_improvement"


class ReflectionDepth(Enum):
    SURFACE = 1
    MODERATE = 2
    DEEP = 3
    PROFOUND = 4


class FailureCategory(Enum):
    KNOWLEDGE_GAP = "knowledge_gap"
    EXECUTION_ERROR = "execution_error"
    STRATEGY_FLAW = "strategy_flaw"
    RESOURCE_LIMIT = "resource_limit"
    CONTEXT_MISMATCH = "context_mismatch"
    TOOL_FAILURE = "tool_failure"


@dataclass
class ReflectionEntry:
    """反思条目"""
    reflection_id: str
    timestamp: str
    reflection_type: ReflectionType
    depth: ReflectionDepth
    trigger_event: str
    analysis: str
    insights: List[str]
    action_items: List[str]
    patterns_identified: List[str]
    confidence: float
    verified: bool = False


@dataclass
class FailureAnalysis:
    """失败分析"""
    failure_id: str
    category: FailureCategory
    root_cause: str
    contributing_factors: List[str]
    impact_assessment: str
    recovery_strategy: str
    prevention_measures: List[str]


@dataclass
class StrategyAdjustment:
    """策略调整"""
    adjustment_id: str
    original_strategy: str
    adjusted_strategy: str
    reason: str
    expected_improvement: str
    confidence: float


@dataclass
class ReflectionChain:
    """反思链 - 连续反思记录"""
    chain_id: str
    session_id: str
    reflections: List[ReflectionEntry]
    cumulative_insights: List[str]
    strategy_evolution: List[StrategyAdjustment]
    final_outcome: Optional[str]
    success: bool


class EnhancedReflexion:
    """
    增强版反思机制
    
    核心理念:
    自我反思是"自性"的关键 - 自我审视能力
    
    四层反思深度:
    1. 表面层 (Surface) - 直接原因分析
    2. 中等层 (Moderate) - 策略层面分析
    3. 深层 (Deep) - 根本原因挖掘
    4. 深刻层 (Profound) - 模式和认知层面
    
    反思循环:
    Execution -> Evaluation -> Reflection -> Optimization
    """
    
    REFLECTION_PROMPTS = {
        ReflectionDepth.SURFACE: """
# 表面层反思

## 分析框架
1. **直接原因**: 导致失败的最直接因素是什么？
2. **即时影响**: 这个失败对当前任务有什么影响？
3. **快速修复**: 有什么立即可行的解决方案？

## 输出格式
- 直接原因: [一句话描述]
- 影响范围: [列出受影响的部分]
- 快速修复: [具体步骤]
""",
        ReflectionDepth.MODERATE: """
# 中等层反思

## 分析框架
1. **策略评估**: 当前策略是否适合这个任务？
2. **资源分配**: 资源是否被合理分配？
3. **执行路径**: 是否有更优的执行路径？

## 输出格式
- 策略问题: [描述策略层面的问题]
- 资源瓶颈: [识别资源限制]
- 改进方向: [策略调整建议]
""",
        ReflectionDepth.DEEP: """
# 深层反思

## 分析框架
1. **根本原因**: 导致问题的根本原因是什么？
2. **假设检验**: 之前的假设是否成立？
3. **认知偏差**: 是否存在认知偏差？

## 输出格式
- 根本原因: [深入分析]
- 错误假设: [列出被证伪的假设]
- 认知修正: [需要调整的认知]
""",
        ReflectionDepth.PROFOUND: """
# 深刻层反思

## 分析框架
1. **模式识别**: 这个问题是否属于某个更大的模式？
2. **知识缺口**: 揭示了哪些知识缺口？
3. **能力边界**: 对自身能力边界有什么新认识？

## 输出格式
- 模式发现: [识别的通用模式]
- 知识缺口: [需要补充的知识]
- 边界认知: [能力边界的重新定义]
""",
    }
    
    FAILURE_SIGNATURES = {
        FailureCategory.KNOWLEDGE_GAP: [
            r"不知道|不了解|不熟悉|没见过",
            r"无法理解|无法解析|无法处理",
            r"缺少.*知识|知识不足",
        ],
        FailureCategory.EXECUTION_ERROR: [
            r"错误|异常|失败|崩溃",
            r"Error|Exception|Failed|Crash",
            r"Traceback|stack trace",
        ],
        FailureCategory.STRATEGY_FLAW: [
            r"策略.*失败|方法.*不对|方案.*问题",
            r"方向错误|路径错误|选择错误",
            r"不适用|不合适|不匹配",
        ],
        FailureCategory.RESOURCE_LIMIT: [
            r"超时|timeout|时间不够",
            r"内存不足|OOM|out of memory",
            r"限制|limit|quota",
        ],
        FailureCategory.CONTEXT_MISMATCH: [
            r"上下文.*不匹配|环境.*不同",
            r"预期.*不符|结果.*不对",
            r"版本.*冲突|依赖.*问题",
        ],
        FailureCategory.TOOL_FAILURE: [
            r"工具.*失败|调用.*错误",
            r"API.*错误|接口.*异常",
            r"网络.*问题|连接.*失败",
        ],
    }
    
    MAX_REFLECTION_HISTORY = 100
    MAX_CHAIN_LENGTH = 10
    
    def __init__(self, memory_dir: str = None):
        if memory_dir:
            self.memory_dir = Path(memory_dir)
        else:
            self.memory_dir = Path("自动化工作流组件库/memory/reflexion")
        
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        self.reflections: List[ReflectionEntry] = []
        self.reflection_chains: Dict[str, ReflectionChain] = {}
        self.failure_patterns: Dict[str, List[FailureAnalysis]] = {}
        
        self._load_history()
    
    def _load_history(self):
        """加载历史反思"""
        history_path = self.memory_dir / "reflections.json"
        if history_path.exists():
            with open(history_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.reflections = [
                    ReflectionEntry(
                        reflection_id=r["reflection_id"],
                        timestamp=r["timestamp"],
                        reflection_type=ReflectionType(r["reflection_type"]),
                        depth=ReflectionDepth(r["depth"]),
                        trigger_event=r["trigger_event"],
                        analysis=r["analysis"],
                        insights=r["insights"],
                        action_items=r["action_items"],
                        patterns_identified=r["patterns_identified"],
                        confidence=r["confidence"],
                        verified=r.get("verified", False),
                    )
                    for r in data.get("reflections", [])
                ]
        
        patterns_path = self.memory_dir / "failure_patterns.json"
        if patterns_path.exists():
            with open(patterns_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for category, analyses in data.get("patterns", {}).items():
                    self.failure_patterns[category] = [
                        FailureAnalysis(**a) for a in analyses
                    ]
    
    def _save_history(self):
        """保存反思历史"""
        history_path = self.memory_dir / "reflections.json"
        with open(history_path, 'w', encoding='utf-8') as f:
            json.dump({
                "reflections": [
                    {
                        "reflection_id": r.reflection_id,
                        "timestamp": r.timestamp,
                        "reflection_type": r.reflection_type.value,
                        "depth": r.depth.value,
                        "trigger_event": r.trigger_event,
                        "analysis": r.analysis,
                        "insights": r.insights,
                        "action_items": r.action_items,
                        "patterns_identified": r.patterns_identified,
                        "confidence": r.confidence,
                        "verified": r.verified,
                    }
                    for r in self.reflections[-self.MAX_REFLECTION_HISTORY:]
                ]
            }, f, ensure_ascii=False, indent=2)
        
        patterns_path = self.memory_dir / "failure_patterns.json"
        with open(patterns_path, 'w', encoding='utf-8') as f:
            json.dump({
                "patterns": {
                    category: [
                        {
                            "failure_id": a.failure_id,
                            "category": a.category.value,
                            "root_cause": a.root_cause,
                            "contributing_factors": a.contributing_factors,
                            "impact_assessment": a.impact_assessment,
                            "recovery_strategy": a.recovery_strategy,
                            "prevention_measures": a.prevention_measures,
                        }
                        for a in analyses
                    ]
                    for category, analyses in self.failure_patterns.items()
                }
            }, f, ensure_ascii=False, indent=2)
    
    def reflect(self, trajectory: str, outcome: str, success: bool,
                context: Dict[str, Any] = None) -> ReflectionEntry:
        """
        核心方法: 自我反思
        
        这是"自性"的关键 - 自我审视能力
        """
        context = context or {}
        
        depth = self._determine_reflection_depth(success, context)
        reflection_type = self._determine_reflection_type(success, context)
        
        analysis = self._generate_analysis(trajectory, outcome, success, depth, context)
        
        insights = self._extract_insights(analysis, trajectory, outcome)
        
        action_items = self._generate_action_items(insights, success)
        
        patterns = self._identify_patterns(trajectory, outcome, insights)
        
        reflection = ReflectionEntry(
            reflection_id=self._generate_reflection_id(),
            timestamp=datetime.now().isoformat(),
            reflection_type=reflection_type,
            depth=depth,
            trigger_event=trajectory[:200],
            analysis=analysis,
            insights=insights,
            action_items=action_items,
            patterns_identified=patterns,
            confidence=self._calculate_confidence(analysis, insights),
        )
        
        self.reflections.append(reflection)
        
        if not success:
            self._record_failure_pattern(trajectory, outcome, context)
        
        self._save_history()
        
        return reflection
    
    def _determine_reflection_depth(self, success: bool, context: Dict) -> ReflectionDepth:
        """确定反思深度"""
        if success:
            return ReflectionDepth.SURFACE
        
        severity = context.get("severity", "medium")
        retry_count = context.get("retry_count", 0)
        
        if severity == "critical" or retry_count >= 3:
            return ReflectionDepth.PROFOUND
        elif severity == "high" or retry_count >= 2:
            return ReflectionDepth.DEEP
        elif severity == "medium" or retry_count >= 1:
            return ReflectionDepth.MODERATE
        else:
            return ReflectionDepth.SURFACE
    
    def _determine_reflection_type(self, success: bool, context: Dict) -> ReflectionType:
        """确定反思类型"""
        if not success:
            return ReflectionType.ERROR_ANALYSIS
        
        if context.get("strategy_review"):
            return ReflectionType.STRATEGY_REVIEW
        
        if context.get("pattern_discovery"):
            return ReflectionType.PATTERN_DISCOVERY
        
        return ReflectionType.OUTCOME_EVALUATION
    
    def _generate_analysis(self, trajectory: str, outcome: str, success: bool,
                           depth: ReflectionDepth, context: Dict) -> str:
        """生成分析"""
        prompt = self.REFLECTION_PROMPTS[depth]
        
        analysis_parts = [
            f"## 触发事件\n{trajectory[:500]}\n",
            f"## 结果\n{'成功' if success else '失败'}: {outcome[:300]}\n",
            f"## 反思深度\n{depth.name} ({depth.value}级)\n",
        ]
        
        if not success:
            failure_category = self._categorize_failure(outcome)
            analysis_parts.append(f"## 失败类别\n{failure_category.value}\n")
            
            similar_failures = self._find_similar_failures(outcome)
            if similar_failures:
                analysis_parts.append(
                    f"## 历史相似失败\n发现 {len(similar_failures)} 个相似案例\n"
                )
        
        analysis_parts.append(prompt)
        
        return "\n".join(analysis_parts)
    
    def _categorize_failure(self, outcome: str) -> FailureCategory:
        """分类失败"""
        outcome_lower = outcome.lower()
        
        for category, signatures in self.FAILURE_SIGNATURES.items():
            for signature in signatures:
                if re.search(signature, outcome_lower, re.IGNORECASE):
                    return category
        
        return FailureCategory.EXECUTION_ERROR
    
    def _find_similar_failures(self, outcome: str) -> List[FailureAnalysis]:
        """查找相似失败"""
        similar = []
        outcome_keywords = set(re.findall(r'\w+', outcome.lower()))
        
        for category, analyses in self.failure_patterns.items():
            for analysis in analyses:
                root_keywords = set(re.findall(r'\w+', analysis.root_cause.lower()))
                overlap = len(outcome_keywords & root_keywords)
                if overlap >= 2:
                    similar.append(analysis)
        
        return similar[:5]
    
    def _extract_insights(self, analysis: str, trajectory: str, 
                          outcome: str) -> List[str]:
        """提取洞察"""
        insights = []
        
        error_patterns = [
            (r"错误[:：]\s*(.+?)(?:\n|$)", "错误发现"),
            (r"原因[:：]\s*(.+?)(?:\n|$)", "原因分析"),
            (r"建议[:：]\s*(.+?)(?:\n|$)", "改进建议"),
            (r"应该\s+(.+?)(?:\n|$)", "行动建议"),
            (r"需要\s+(.+?)(?:\n|$)", "需求识别"),
        ]
        
        for pattern, insight_type in error_patterns:
            matches = re.findall(pattern, analysis + trajectory + outcome)
            for match in matches:
                insights.append(f"[{insight_type}] {match.strip()}")
        
        if "知识" in analysis or "knowledge" in analysis.lower():
            insights.append("[知识缺口] 需要补充相关知识")
        
        if "策略" in analysis or "strategy" in analysis.lower():
            insights.append("[策略问题] 需要调整执行策略")
        
        return insights[:10]
    
    def _generate_action_items(self, insights: List[str], success: bool) -> List[str]:
        """生成行动项"""
        actions = []
        
        for insight in insights:
            if "错误发现" in insight:
                actions.append(f"修复: {insight.split('] ')[1]}")
            elif "原因分析" in insight:
                actions.append(f"解决根本原因: {insight.split('] ')[1]}")
            elif "改进建议" in insight or "行动建议" in insight:
                actions.append(insight.split('] ')[1])
            elif "需求识别" in insight:
                actions.append(f"满足需求: {insight.split('] ')[1]}")
        
        if not success:
            actions.append("重新评估执行策略")
            actions.append("考虑使用知识调用模式")
        
        return actions[:5]
    
    def _identify_patterns(self, trajectory: str, outcome: str, 
                           insights: List[str]) -> List[str]:
        """识别模式"""
        patterns = []
        
        all_text = (trajectory + outcome + " ".join(insights)).lower()
        
        pattern_indicators = [
            (r"重复|多次|反复", "重复性问题模式"),
            (r"总是|每次|一直", "持续性模式"),
            (r"偶尔|有时|间或", "间歇性问题模式"),
            (r"特定.*条件|当.*时", "条件触发模式"),
        ]
        
        for pattern, pattern_name in pattern_indicators:
            if re.search(pattern, all_text):
                patterns.append(pattern_name)
        
        similar_reflections = self._find_similar_reflections(trajectory)
        if len(similar_reflections) >= 2:
            patterns.append("重复失败模式")
        
        return patterns
    
    def _find_similar_reflections(self, trajectory: str) -> List[ReflectionEntry]:
        """查找相似反思"""
        similar = []
        trajectory_keywords = set(re.findall(r'\w+', trajectory.lower()))
        
        for reflection in self.reflections[-20:]:
            event_keywords = set(re.findall(r'\w+', reflection.trigger_event.lower()))
            overlap = len(trajectory_keywords & event_keywords)
            if overlap >= 3:
                similar.append(reflection)
        
        return similar
    
    def _calculate_confidence(self, analysis: str, insights: List[str]) -> float:
        """计算置信度"""
        confidence = 0.5
        
        if len(insights) >= 3:
            confidence += 0.1
        
        if len(analysis) > 500:
            confidence += 0.1
        
        similar = len(self._find_similar_reflections(analysis))
        if similar > 0:
            confidence += min(0.2, similar * 0.05)
        
        return min(1.0, confidence)
    
    def _record_failure_pattern(self, trajectory: str, outcome: str, context: Dict):
        """记录失败模式"""
        category = self._categorize_failure(outcome)
        
        analysis = FailureAnalysis(
            failure_id=self._generate_reflection_id(),
            category=category,
            root_cause=self._extract_root_cause(trajectory, outcome),
            contributing_factors=self._extract_contributing_factors(context),
            impact_assessment=self._assess_impact(outcome),
            recovery_strategy=self._suggest_recovery(category),
            prevention_measures=self._suggest_prevention(category),
        )
        
        if category.value not in self.failure_patterns:
            self.failure_patterns[category.value] = []
        
        self.failure_patterns[category.value].append(analysis)
    
    def _extract_root_cause(self, trajectory: str, outcome: str) -> str:
        """提取根本原因"""
        combined = trajectory + outcome
        
        cause_patterns = [
            r"因为\s+(.+?)(?:\n|,|，|$)",
            r"由于\s+(.+?)(?:\n|,|，|$)",
            r"原因是\s+(.+?)(?:\n|,|，|$)",
        ]
        
        for pattern in cause_patterns:
            match = re.search(pattern, combined)
            if match:
                return match.group(1).strip()
        
        return "需要进一步分析确定"
    
    def _extract_contributing_factors(self, context: Dict) -> List[str]:
        """提取影响因素"""
        factors = []
        
        if context.get("retry_count", 0) > 0:
            factors.append(f"已重试{context['retry_count']}次")
        
        if context.get("resource_constraint"):
            factors.append("存在资源限制")
        
        if context.get("time_pressure"):
            factors.append("存在时间压力")
        
        return factors
    
    def _assess_impact(self, outcome: str) -> str:
        """评估影响"""
        if "严重" in outcome or "critical" in outcome.lower():
            return "高影响 - 需要立即处理"
        elif "中等" in outcome or "medium" in outcome.lower():
            return "中等影响 - 需要计划处理"
        else:
            return "低影响 - 可以延后处理"
    
    def _suggest_recovery(self, category: FailureCategory) -> str:
        """建议恢复策略"""
        strategies = {
            FailureCategory.KNOWLEDGE_GAP: "启用知识调用模式，联网查找相关信息",
            FailureCategory.EXECUTION_ERROR: "分析错误日志，定位具体问题并修复",
            FailureCategory.STRATEGY_FLAW: "重新评估策略，考虑替代方案",
            FailureCategory.RESOURCE_LIMIT: "优化资源使用或请求更多资源",
            FailureCategory.CONTEXT_MISMATCH: "重新分析上下文，调整执行方式",
            FailureCategory.TOOL_FAILURE: "检查工具状态，尝试替代工具或方法",
        }
        return strategies.get(category, "分析问题并制定针对性解决方案")
    
    def _suggest_prevention(self, category: FailureCategory) -> List[str]:
        """建议预防措施"""
        measures = {
            FailureCategory.KNOWLEDGE_GAP: [
                "建立知识库查询机制",
                "在执行前评估知识储备",
                "启用知识边界感知",
            ],
            FailureCategory.EXECUTION_ERROR: [
                "增加错误处理逻辑",
                "添加输入验证",
                "实现优雅降级",
            ],
            FailureCategory.STRATEGY_FLAW: [
                "建立策略评估机制",
                "增加策略多样性",
                "实现策略自适应",
            ],
            FailureCategory.RESOURCE_LIMIT: [
                "实现资源监控",
                "建立资源预警机制",
                "优化资源使用效率",
            ],
            FailureCategory.CONTEXT_MISMATCH: [
                "增强上下文感知能力",
                "建立环境检测机制",
                "实现上下文自适应",
            ],
            FailureCategory.TOOL_FAILURE: [
                "实现工具健康检查",
                "建立工具备用方案",
                "增加重试机制",
            ],
        }
        return measures.get(category, ["建立问题监控机制"])
    
    def _generate_reflection_id(self) -> str:
        """生成反思ID"""
        import hashlib
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        return f"REF_{timestamp}"
    
    def start_reflection_chain(self, session_id: str) -> str:
        """开始反思链"""
        chain_id = f"CHAIN_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        self.reflection_chains[chain_id] = ReflectionChain(
            chain_id=chain_id,
            session_id=session_id,
            reflections=[],
            cumulative_insights=[],
            strategy_evolution=[],
            final_outcome=None,
            success=False,
        )
        
        return chain_id
    
    def add_to_chain(self, chain_id: str, reflection: ReflectionEntry):
        """添加反思到链"""
        if chain_id not in self.reflection_chains:
            return
        
        chain = self.reflection_chains[chain_id]
        
        if len(chain.reflections) >= self.MAX_CHAIN_LENGTH:
            return
        
        chain.reflections.append(reflection)
        
        for insight in reflection.insights:
            if insight not in chain.cumulative_insights:
                chain.cumulative_insights.append(insight)
        
        self._save_history()
    
    def end_reflection_chain(self, chain_id: str, outcome: str, success: bool):
        """结束反思链"""
        if chain_id not in self.reflection_chains:
            return
        
        chain = self.reflection_chains[chain_id]
        chain.final_outcome = outcome
        chain.success = success
        
        self._save_history()
    
    def get_reflection_guidance(self, current_situation: str) -> Dict[str, Any]:
        """获取反思指导"""
        similar_reflections = self._find_similar_reflections(current_situation)
        
        relevant_insights = []
        for reflection in similar_reflections[:3]:
            relevant_insights.extend(reflection.insights)
        
        failure_category = self._categorize_failure(current_situation)
        recovery_strategy = self._suggest_recovery(failure_category)
        
        return {
            "similar_cases": len(similar_reflections),
            "relevant_insights": list(set(relevant_insights))[:5],
            "suggested_recovery": recovery_strategy,
            "failure_category": failure_category.value,
            "reflection_prompt": self.REFLECTION_PROMPTS[ReflectionDepth.MODERATE],
        }
    
    def get_reflection_report(self) -> Dict[str, Any]:
        """获取反思报告"""
        return {
            "total_reflections": len(self.reflections),
            "failure_patterns": {
                category: len(analyses)
                for category, analyses in self.failure_patterns.items()
            },
            "recent_insights": [
                insight
                for r in self.reflections[-10:]
                for insight in r.insights
            ][:10],
            "depth_distribution": {
                depth.name: len([r for r in self.reflections if r.depth == depth])
                for depth in ReflectionDepth
            },
            "type_distribution": {
                rtype.name: len([r for r in self.reflections if r.reflection_type == rtype])
                for rtype in ReflectionType
            },
            "top_patterns": self._get_top_patterns(),
        }
    
    def _get_top_patterns(self) -> List[str]:
        """获取顶级模式"""
        pattern_counts = {}
        
        for reflection in self.reflections:
            for pattern in reflection.patterns_identified:
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        return sorted(pattern_counts.keys(), key=lambda x: pattern_counts[x], reverse=True)[:5]
    
    def act_with_reflection(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        带反思的行动
        
        核心能力: 将历史反思作为上下文指导当前行动
        """
        context = context or {}
        
        guidance = self.get_reflection_guidance(task)
        
        relevant_reflections = self._find_similar_reflections(task)
        
        context_with_reflection = {
            **context,
            "reflection_guidance": guidance,
            "historical_insights": [
                insight
                for r in relevant_reflections[:3]
                for insight in r.insights
            ][:5],
            "suggested_recovery": guidance["suggested_recovery"],
        }
        
        return context_with_reflection
