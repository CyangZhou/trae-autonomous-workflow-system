"""
Self-Distillation v1.0 - 自蒸馏持续学习模块
核心功能:
1. 让模型成为自己的老师
2. 持续学习而不遗忘
3. 从交互中提炼高质量知识
4. 实现内生增长

参考论文: "Self-Distillation Enables Continual Learning" (MIT, ETH Zurich, Meta, Stanford 2026)
"""

import json
import hashlib
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class DistillationType(Enum):
    EXPERIENCE = "experience"
    ERROR_RECOVERY = "error_recovery"
    SUCCESS_PATTERN = "success_pattern"
    STRATEGY_REFINEMENT = "strategy_refinement"
    KNOWLEDGE_CONSOLIDATION = "knowledge_consolidation"


class KnowledgeQuality(Enum):
    RAW = 1
    PROCESSED = 2
    REFINED = 3
    DISTILLED = 4


@dataclass
class KnowledgeUnit:
    """知识单元"""
    unit_id: str
    content: str
    domain: str
    quality: KnowledgeQuality
    source_interactions: List[str]
    confidence: float
    usage_count: int
    last_used: str
    created_at: str
    distilled_from: Optional[str] = None


@dataclass
class DistillationSession:
    """蒸馏会话"""
    session_id: str
    distillation_type: DistillationType
    input_knowledge: List[KnowledgeUnit]
    teacher_context: str
    distilled_output: KnowledgeUnit
    quality_improvement: float
    timestamp: str


@dataclass
class TeacherPersona:
    """教师人格 - 增强上下文构建的"超级自我" """
    persona_id: str
    expertise_domains: List[str]
    enhancement_techniques: List[str]
    context_templates: Dict[str, str]
    quality_standards: Dict[str, float]


class SelfDistillation:
    """
    自蒸馏持续学习模块
    
    核心理念:
    模型在特定上下文中可以表现出超越当前权重的智能
    通过精心设计的上下文引导构建"超级自我"
    
    关键洞察:
    1. 自蒸馏: 当前模型 → 更聪明的临时自我
    2. 无需外部教师
    3. 实现内生增长
    4. 防止灾难性遗忘
    """
    
    TEACHER_ENHANCEMENT_TECHNIQUES = [
        "chain_of_thought",
        "reflection",
        "decomposition",
        "analogy",
        "counterfactual",
        "meta_cognition",
    ]
    
    CONTEXT_TEMPLATES = {
        "error_recovery": """
# 专家级错误恢复指导

## 背景
你是一位经验丰富的系统调试专家，擅长从错误中学习和恢复。

## 错误信息
{error_info}

## 历史经验
{historical_experience}

## 任务
请分析这个错误，并提供:
1. 根本原因分析
2. 修复步骤
3. 预防措施
4. 相关知识总结

请以结构化的方式输出，确保知识可复用。
""",
        "success_pattern": """
# 成功模式提炼专家

## 背景
你是一位模式识别专家，擅长从成功经验中提炼可复用的模式。

## 成功案例
{success_case}

## 执行过程
{execution_process}

## 任务
请提炼这个成功案例中的:
1. 关键成功因素
2. 可复用的模式
3. 适用条件
4. 注意事项

请确保提炼的知识具有通用性和可操作性。
""",
        "strategy_refinement": """
# 策略优化专家

## 背景
你是一位策略分析专家，擅长评估和优化执行策略。

## 当前策略
{current_strategy}

## 执行结果
{execution_result}

## 任务
请分析并优化:
1. 策略优点
2. 策略不足
3. 改进建议
4. 替代方案

请提供具体的、可执行的改进建议。
""",
        "knowledge_consolidation": """
# 知识整合专家

## 背景
你是一位知识管理专家，擅长整合和结构化知识。

## 原始知识
{raw_knowledge}

## 相关上下文
{context}

## 任务
请整合这些知识:
1. 提取核心概念
2. 建立概念关联
3. 形成知识结构
4. 标注置信度

请确保知识结构清晰、易于检索和应用。
""",
    }
    
    QUALITY_STANDARDS = {
        "clarity": 0.8,
        "completeness": 0.7,
        "actionability": 0.8,
        "reusability": 0.75,
    }
    
    MAX_KNOWLEDGE_UNITS = 500
    DISTILLATION_THRESHOLD = 3
    
    def __init__(self, memory_dir: str = None):
        if memory_dir:
            self.memory_dir = Path(memory_dir)
        else:
            self.memory_dir = Path("自动化工作流组件库/memory/distillation")
        
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        self.knowledge_base: Dict[str, KnowledgeUnit] = {}
        self.distillation_history: List[DistillationSession] = []
        self.teacher_persona = self._create_teacher_persona()
        
        self._load_knowledge()
    
    def _create_teacher_persona(self) -> TeacherPersona:
        """创建教师人格"""
        return TeacherPersona(
            persona_id="teacher_v1",
            expertise_domains=[
                "error_recovery",
                "pattern_extraction",
                "strategy_optimization",
                "knowledge_consolidation",
            ],
            enhancement_techniques=self.TEACHER_ENHANCEMENT_TECHNIQUES,
            context_templates=self.CONTEXT_TEMPLATES,
            quality_standards=self.QUALITY_STANDARDS,
        )
    
    def _load_knowledge(self):
        """加载知识库"""
        knowledge_path = self.memory_dir / "knowledge_base.json"
        if knowledge_path.exists():
            with open(knowledge_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for unit_id, unit_data in data.get("units", {}).items():
                    self.knowledge_base[unit_id] = KnowledgeUnit(
                        unit_id=unit_data["unit_id"],
                        content=unit_data["content"],
                        domain=unit_data["domain"],
                        quality=KnowledgeQuality(unit_data["quality"]),
                        source_interactions=unit_data["source_interactions"],
                        confidence=unit_data["confidence"],
                        usage_count=unit_data["usage_count"],
                        last_used=unit_data["last_used"],
                        created_at=unit_data["created_at"],
                        distilled_from=unit_data.get("distilled_from"),
                    )
        
        history_path = self.memory_dir / "distillation_history.json"
        if history_path.exists():
            with open(history_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.distillation_history = [
                    DistillationSession(
                        session_id=s["session_id"],
                        distillation_type=DistillationType(s["distillation_type"]),
                        input_knowledge=[
                            KnowledgeUnit(**k) for k in s["input_knowledge"]
                        ],
                        teacher_context=s["teacher_context"],
                        distilled_output=KnowledgeUnit(**s["distilled_output"]),
                        quality_improvement=s["quality_improvement"],
                        timestamp=s["timestamp"],
                    )
                    for s in data.get("sessions", [])
                ]
    
    def _save_knowledge(self):
        """保存知识库"""
        knowledge_path = self.memory_dir / "knowledge_base.json"
        with open(knowledge_path, 'w', encoding='utf-8') as f:
            json.dump({
                "units": {
                    unit_id: {
                        "unit_id": unit.unit_id,
                        "content": unit.content,
                        "domain": unit.domain,
                        "quality": unit.quality.value,
                        "source_interactions": unit.source_interactions,
                        "confidence": unit.confidence,
                        "usage_count": unit.usage_count,
                        "last_used": unit.last_used,
                        "created_at": unit.created_at,
                        "distilled_from": unit.distilled_from,
                    }
                    for unit_id, unit in self.knowledge_base.items()
                }
            }, f, ensure_ascii=False, indent=2)
        
        history_path = self.memory_dir / "distillation_history.json"
        with open(history_path, 'w', encoding='utf-8') as f:
            json.dump({
                "sessions": [
                    {
                        "session_id": s.session_id,
                        "distillation_type": s.distillation_type.value,
                        "input_knowledge": [
                            {
                                "unit_id": k.unit_id,
                                "content": k.content,
                                "domain": k.domain,
                                "quality": k.quality.value,
                                "source_interactions": k.source_interactions,
                                "confidence": k.confidence,
                                "usage_count": k.usage_count,
                                "last_used": k.last_used,
                                "created_at": k.created_at,
                                "distilled_from": k.distilled_from,
                            }
                            for k in s.input_knowledge
                        ],
                        "teacher_context": s.teacher_context,
                        "distilled_output": {
                            "unit_id": s.distilled_output.unit_id,
                            "content": s.distilled_output.content,
                            "domain": s.distilled_output.domain,
                            "quality": s.distilled_output.quality.value,
                            "source_interactions": s.distilled_output.source_interactions,
                            "confidence": s.distilled_output.confidence,
                            "usage_count": s.distilled_output.usage_count,
                            "last_used": s.distilled_output.last_used,
                            "created_at": s.distilled_output.created_at,
                            "distilled_from": s.distilled_output.distilled_from,
                        },
                        "quality_improvement": s.quality_improvement,
                        "timestamp": s.timestamp,
                    }
                    for s in self.distillation_history[-100:]
                ]
            }, f, ensure_ascii=False, indent=2)
    
    def store_experience(self, experience: Dict[str, Any]) -> str:
        """
        存储经验
        
        核心能力: 从交互中提取知识
        """
        unit_id = self._generate_unit_id()
        
        content = self._extract_content(experience)
        domain = self._detect_domain(experience)
        
        unit = KnowledgeUnit(
            unit_id=unit_id,
            content=content,
            domain=domain,
            quality=KnowledgeQuality.RAW,
            source_interactions=[experience.get("interaction_id", "unknown")],
            confidence=0.5,
            usage_count=0,
            last_used=datetime.now().isoformat(),
            created_at=datetime.now().isoformat(),
        )
        
        self.knowledge_base[unit_id] = unit
        
        self._check_distillation_trigger(domain)
        
        self._save_knowledge()
        
        return unit_id
    
    def _generate_unit_id(self) -> str:
        """生成知识单元ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        return f"KU_{timestamp}"
    
    def _extract_content(self, experience: Dict) -> str:
        """提取内容"""
        parts = []
        
        if "action" in experience:
            parts.append(f"## 行动\n{experience['action']}")
        
        if "outcome" in experience:
            parts.append(f"## 结果\n{experience['outcome']}")
        
        if "insights" in experience:
            parts.append(f"## 洞察\n{experience['insights']}")
        
        return "\n\n".join(parts) if parts else str(experience)
    
    def _detect_domain(self, experience: Dict) -> str:
        """检测领域"""
        action = experience.get("action", "").lower()
        
        domain_keywords = {
            "error_recovery": ["错误", "修复", "debug", "error", "fix"],
            "code_writing": ["创建", "编写", "实现", "create", "write"],
            "testing": ["测试", "test", "验证"],
            "deployment": ["部署", "deploy", "发布"],
            "documentation": ["文档", "readme", "document"],
        }
        
        for domain, keywords in domain_keywords.items():
            if any(kw in action for kw in keywords):
                return domain
        
        return "general"
    
    def _check_distillation_trigger(self, domain: str):
        """检查是否触发蒸馏"""
        domain_units = [
            u for u in self.knowledge_base.values()
            if u.domain == domain and u.quality == KnowledgeQuality.RAW
        ]
        
        if len(domain_units) >= self.DISTILLATION_THRESHOLD:
            self._trigger_distillation(domain, domain_units)
    
    def _trigger_distillation(self, domain: str, units: List[KnowledgeUnit]):
        """触发蒸馏"""
        distillation_type = self._determine_distillation_type(domain)
        
        session = self.distill(
            distillation_type=distillation_type,
            input_units=units[:5],
            domain=domain,
        )
        
        if session:
            for unit in units[:5]:
                if unit.unit_id in self.knowledge_base:
                    del self.knowledge_base[unit.unit_id]
    
    def _determine_distillation_type(self, domain: str) -> DistillationType:
        """确定蒸馏类型"""
        mapping = {
            "error_recovery": DistillationType.ERROR_RECOVERY,
            "code_writing": DistillationType.SUCCESS_PATTERN,
            "testing": DistillationType.SUCCESS_PATTERN,
            "deployment": DistillationType.SUCCESS_PATTERN,
            "documentation": DistillationType.KNOWLEDGE_CONSOLIDATION,
        }
        return mapping.get(domain, DistillationType.EXPERIENCE)
    
    def create_teacher_context(self, distillation_type: DistillationType,
                                context_data: Dict[str, Any]) -> str:
        """
        创建教师上下文
        
        核心能力: 通过精心设计的上下文引导构建"超级自我"
        """
        template_key = distillation_type.value
        template = self.teacher_persona.context_templates.get(
            template_key,
            self.CONTEXT_TEMPLATES.get("knowledge_consolidation")
        )
        
        enhanced_context = template.format(**context_data)
        
        enhancement_prefix = self._apply_enhancement_techniques(distillation_type)
        
        return enhancement_prefix + "\n\n" + enhanced_context
    
    def _apply_enhancement_techniques(self, distillation_type: DistillationType) -> str:
        """应用增强技术"""
        techniques = []
        
        techniques.append("""
## 思维增强

请使用以下思维技术来增强你的分析:
1. **链式思考**: 逐步推理，展示思考过程
2. **反思**: 对自己的分析进行反思和验证
3. **分解**: 将复杂问题分解为简单子问题
4. **类比**: 使用类比来解释复杂概念
5. **元认知**: 思考自己的思考方式

""")
        
        return "".join(techniques)
    
    def distill(self, distillation_type: DistillationType,
                input_units: List[KnowledgeUnit],
                domain: str) -> Optional[DistillationSession]:
        """
        执行蒸馏
        
        核心能力: 让模型成为自己的老师
        """
        if not input_units:
            return None
        
        session_id = f"DIST_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        context_data = self._prepare_context_data(input_units, distillation_type)
        
        teacher_context = self.create_teacher_context(distillation_type, context_data)
        
        distilled_content = self._generate_distilled_content(
            input_units, teacher_context, distillation_type
        )
        
        distilled_unit = KnowledgeUnit(
            unit_id=self._generate_unit_id(),
            content=distilled_content,
            domain=domain,
            quality=KnowledgeQuality.DISTILLED,
            source_interactions=[u.unit_id for u in input_units],
            confidence=self._calculate_distilled_confidence(input_units),
            usage_count=0,
            last_used=datetime.now().isoformat(),
            created_at=datetime.now().isoformat(),
            distilled_from=session_id,
        )
        
        quality_improvement = self._calculate_quality_improvement(
            input_units, distilled_unit
        )
        
        session = DistillationSession(
            session_id=session_id,
            distillation_type=distillation_type,
            input_knowledge=input_units,
            teacher_context=teacher_context,
            distilled_output=distilled_unit,
            quality_improvement=quality_improvement,
            timestamp=datetime.now().isoformat(),
        )
        
        self.knowledge_base[distilled_unit.unit_id] = distilled_unit
        self.distillation_history.append(session)
        
        self._save_knowledge()
        
        return session
    
    def _prepare_context_data(self, units: List[KnowledgeUnit],
                               distillation_type: DistillationType) -> Dict[str, Any]:
        """准备上下文数据"""
        combined_content = "\n\n---\n\n".join([u.content for u in units])
        
        if distillation_type == DistillationType.ERROR_RECOVERY:
            return {
                "error_info": combined_content,
                "historical_experience": self._get_historical_experience("error_recovery"),
            }
        elif distillation_type == DistillationType.SUCCESS_PATTERN:
            return {
                "success_case": combined_content,
                "execution_process": "多个成功案例的综合",
            }
        elif distillation_type == DistillationType.STRATEGY_REFINEMENT:
            return {
                "current_strategy": combined_content,
                "execution_result": "需要进一步分析",
            }
        else:
            return {
                "raw_knowledge": combined_content,
                "context": "知识整合",
            }
    
    def _get_historical_experience(self, domain: str) -> str:
        """获取历史经验"""
        domain_units = [
            u for u in self.knowledge_base.values()
            if u.domain == domain and u.quality == KnowledgeQuality.DISTILLED
        ]
        
        if not domain_units:
            return "暂无相关历史经验"
        
        return "\n\n".join([u.content for u in domain_units[:3]])
    
    def _generate_distilled_content(self, units: List[KnowledgeUnit],
                                     teacher_context: str,
                                     distillation_type: DistillationType) -> str:
        """生成蒸馏内容"""
        key_insights = []
        
        for unit in units:
            insights = re.findall(r'## 洞察\n(.+?)(?=\n##|\Z)', unit.content, re.DOTALL)
            key_insights.extend(insights)
        
        distilled = f"""# 蒸馏知识 ({distillation_type.value})

## 来源
整合自 {len(units)} 个知识单元

## 核心内容
{self._synthesize_content(units)}

## 关键洞察
{chr(10).join(f'- {i.strip()}' for i in key_insights[:5]) if key_insights else '- 从实践中总结的经验'}

## 应用指南
1. 识别适用场景
2. 应用核心方法
3. 验证结果
4. 必要时调整

## 置信度
基于 {len(units)} 个案例的综合分析
"""
        
        return distilled
    
    def _synthesize_content(self, units: List[KnowledgeUnit]) -> str:
        """综合内容"""
        all_content = " ".join([u.content for u in units])
        
        key_patterns = [
            r'关键[:：]\s*(.+?)(?:\n|$)',
            r'重要[:：]\s*(.+?)(?:\n|$)',
            r'注意[:：]\s*(.+?)(?:\n|$)',
            r'建议[:：]\s*(.+?)(?:\n|$)',
        ]
        
        synthesized = []
        for pattern in key_patterns:
            matches = re.findall(pattern, all_content)
            synthesized.extend(matches[:2])
        
        if synthesized:
            return "\n".join(f"- {m.strip()}" for m in synthesized[:5])
        
        return "综合多个案例的核心经验"
    
    def _calculate_distilled_confidence(self, units: List[KnowledgeUnit]) -> float:
        """计算蒸馏后置信度"""
        if not units:
            return 0.5
        
        base_confidence = sum(u.confidence for u in units) / len(units)
        
        diversity_bonus = min(0.2, len(units) * 0.05)
        
        return min(1.0, base_confidence + diversity_bonus + 0.1)
    
    def _calculate_quality_improvement(self, input_units: List[KnowledgeUnit],
                                        output_unit: KnowledgeUnit) -> float:
        """计算质量提升"""
        if not input_units:
            return 0.0
        
        input_avg_quality = sum(u.quality.value for u in input_units) / len(input_units)
        output_quality = output_unit.quality.value
        
        return output_quality - input_avg_quality
    
    def retrieve_knowledge(self, query: str, top_k: int = 5) -> List[KnowledgeUnit]:
        """
        检索知识
        
        核心能力: 向量检索 + 语义匹配
        """
        query_keywords = set(re.findall(r'\w+', query.lower()))
        
        scored_units = []
        for unit in self.knowledge_base.values():
            score = 0.0
            
            content_keywords = set(re.findall(r'\w+', unit.content.lower()))
            keyword_overlap = len(query_keywords & content_keywords)
            score += keyword_overlap * 0.3
            
            score += unit.quality.value * 0.2
            
            score += unit.confidence * 0.2
            
            score += min(0.1, unit.usage_count * 0.01)
            
            if score > 0:
                scored_units.append((unit, score))
        
        scored_units.sort(key=lambda x: x[1], reverse=True)
        
        result_units = [u for u, s in scored_units[:top_k]]
        
        for unit in result_units:
            unit.usage_count += 1
            unit.last_used = datetime.now().isoformat()
        
        self._save_knowledge()
        
        return result_units
    
    def learn_from_interaction(self, interaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        从交互中学习
        
        核心能力: 持续学习而不遗忘
        """
        unit_id = self.store_experience(interaction)
        
        relevant_knowledge = self.retrieve_knowledge(
            interaction.get("action", ""),
            top_k=3
        )
        
        return {
            "stored_unit_id": unit_id,
            "relevant_knowledge": [
                {
                    "unit_id": k.unit_id,
                    "content_preview": k.content[:200],
                    "quality": k.quality.name,
                    "confidence": k.confidence,
                }
                for k in relevant_knowledge
            ],
            "knowledge_base_size": len(self.knowledge_base),
        }
    
    def get_distillation_report(self) -> Dict[str, Any]:
        """获取蒸馏报告"""
        quality_distribution = {}
        for quality in KnowledgeQuality:
            quality_distribution[quality.name] = len([
                u for u in self.knowledge_base.values()
                if u.quality == quality
            ])
        
        domain_distribution = {}
        for unit in self.knowledge_base.values():
            domain_distribution[unit.domain] = domain_distribution.get(unit.domain, 0) + 1
        
        return {
            "total_knowledge_units": len(self.knowledge_base),
            "distillation_sessions": len(self.distillation_history),
            "quality_distribution": quality_distribution,
            "domain_distribution": domain_distribution,
            "recent_distillations": [
                {
                    "session_id": s.session_id,
                    "type": s.distillation_type.value,
                    "quality_improvement": s.quality_improvement,
                }
                for s in self.distillation_history[-5:]
            ],
            "top_knowledge": [
                {
                    "unit_id": u.unit_id,
                    "domain": u.domain,
                    "confidence": u.confidence,
                    "usage_count": u.usage_count,
                }
                for u in sorted(
                    self.knowledge_base.values(),
                    key=lambda x: x.confidence * x.usage_count,
                    reverse=True
                )[:5]
            ],
        }
