"""
Knowledge Boundary Perception Module v2.0
知识边界感知模块 - 判断思考模式和置信度
"""

from enum import Enum
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


class ThinkingMode(Enum):
    FAST = "fast"
    SLOW = "slow"
    KNOWLEDGE = "knowledge"


class KnowledgeDomain(Enum):
    SOFTWARE_ENGINEERING = "software_engineering"
    DATA_SCIENCE = "data_science"
    DEVOPS = "devops"
    CONTENT_CREATION = "content_creation"
    QUANTITATIVE_FINANCE = "quantitative_finance"
    GENERAL = "general"


@dataclass
class ThinkingDecision:
    mode: ThinkingMode
    confidence: float
    reasoning: str
    should_use_web: bool = False
    knowledge_gaps: List[str] = None
    
    def __post_init__(self):
        if self.knowledge_gaps is None:
            self.knowledge_gaps = []


class KnowledgeBoundaryAwareness:
    """
    知识边界感知器
    
    核心功能:
    1. 判断任务复杂度
    2. 决定思考模式 (Fast/Slow/Knowledge)
    3. 识别知识边界
    4. 建议是否需要联网查询
    """
    
    HIGH_CONFIDENCE_THRESHOLD = 0.85
    LOW_CONFIDENCE_THRESHOLD = 0.5
    
    COMPLEXITY_INDICATORS = {
        'high': ['架构', '系统设计', '分布式', '微服务', '重构', '迁移', '集成'],
        'medium': ['实现', '开发', '构建', '优化', '测试', '部署'],
        'low': ['修改', '更新', '修复', '调整', '配置']
    }
    
    KNOWLEDGE_INTENSIVE_KEYWORDS = [
        '最新', '新版本', '新特性', '最佳实践', '行业标准',
        '框架', '库', 'API', '协议', '规范', '安全'
    ]
    
    def __init__(self):
        self.confidence_history = []
    
    def decide_thinking_mode(self, task_description: str) -> ThinkingDecision:
        """
        决定思考模式
        
        逻辑:
        1. 简单任务 → Fast (高置信度)
        2. 复杂任务 → Slow (中等置信度)
        3. 知识密集型 → Knowledge (低置信度，需要联网)
        """
        complexity = self._assess_complexity(task_description)
        knowledge_intensity = self._assess_knowledge_intensity(task_description)
        confidence = self._calculate_confidence(task_description, complexity, knowledge_intensity)
        
        if knowledge_intensity >= 0.7:
            mode = ThinkingMode.KNOWLEDGE
            should_use_web = True
            reasoning = "任务涉及知识密集型内容，建议联网查询"
        elif confidence >= self.HIGH_CONFIDENCE_THRESHOLD:
            mode = ThinkingMode.FAST
            should_use_web = False
            reasoning = "任务简单明确，可直接执行"
        elif confidence >= self.LOW_CONFIDENCE_THRESHOLD:
            mode = ThinkingMode.SLOW
            should_use_web = knowledge_intensity > 0.3
            reasoning = "任务需要仔细分析"
        else:
            mode = ThinkingMode.KNOWLEDGE
            should_use_web = True
            reasoning = "置信度较低，建议联网查询补充知识"
        
        knowledge_gaps = self._identify_knowledge_gaps(task_description) if should_use_web else []
        
        decision = ThinkingDecision(
            mode=mode,
            confidence=confidence,
            reasoning=reasoning,
            should_use_web=should_use_web,
            knowledge_gaps=knowledge_gaps
        )
        
        self.confidence_history.append({
            'task': task_description[:50],
            'mode': mode.value,
            'confidence': confidence
        })
        
        return decision
    
    def detect(self, task_description: str) -> Dict[str, Any]:
        """
        检测知识边界 (兼容旧接口)
        """
        decision = self.decide_thinking_mode(task_description)
        return {
            "mode": decision.mode.value,
            "confidence": decision.confidence,
            "boundaries": decision.knowledge_gaps,
            "should_use_web": decision.should_use_web,
            "reasoning": decision.reasoning
        }
    
    def _assess_complexity(self, task: str) -> float:
        """评估任务复杂度"""
        task_lower = task.lower()
        
        high_count = sum(1 for kw in self.COMPLEXITY_INDICATORS['high'] if kw in task_lower)
        medium_count = sum(1 for kw in self.COMPLEXITY_INDICATORS['medium'] if kw in task_lower)
        low_count = sum(1 for kw in self.COMPLEXITY_INDICATORS['low'] if kw in task_lower)
        
        if high_count > 0:
            return 0.8 + min(0.2, high_count * 0.05)
        elif medium_count > 0:
            return 0.5 + min(0.3, medium_count * 0.1)
        elif low_count > 0:
            return 0.2 + min(0.2, low_count * 0.05)
        else:
            return 0.5
    
    def _assess_knowledge_intensity(self, task: str) -> float:
        """评估知识密集度"""
        task_lower = task.lower()
        matches = sum(1 for kw in self.KNOWLEDGE_INTENSIVE_KEYWORDS if kw in task_lower)
        return min(1.0, matches * 0.15)
    
    def _calculate_confidence(self, task: str, complexity: float, knowledge_intensity: float) -> float:
        """计算置信度"""
        base_confidence = 0.7
        
        if complexity > 0.7:
            base_confidence -= 0.2
        elif complexity < 0.3:
            base_confidence += 0.1
        
        base_confidence -= knowledge_intensity * 0.3
        
        if len(task) < 20:
            base_confidence -= 0.1
        elif len(task) > 200:
            base_confidence -= 0.05
        
        return max(0.1, min(1.0, base_confidence))
    
    def _identify_knowledge_gaps(self, task: str) -> List[str]:
        """识别知识缺口"""
        gaps = []
        
        for kw in self.KNOWLEDGE_INTENSIVE_KEYWORDS:
            if kw in task.lower():
                gaps.append(f"需要了解{kw}相关信息")
        
        if not gaps:
            gaps.append("建议查阅相关文档和最佳实践")
        
        return gaps[:5]


class KnowledgeBoundary:
    """兼容旧版本的别名"""
    
    def __init__(self):
        self.awareness = KnowledgeBoundaryAwareness()
    
    def detect(self, task_description: str) -> Dict[str, Any]:
        return self.awareness.detect(task_description)
    
    def decide_thinking_mode(self, task_description: str) -> ThinkingDecision:
        return self.awareness.decide_thinking_mode(task_description)
