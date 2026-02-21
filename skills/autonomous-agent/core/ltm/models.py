from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

class MemoryLayer(Enum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"

class InteractionType(Enum):
    TASK_EXECUTION = "task_execution"
    ERROR_RESOLUTION = "error_resolution"
    DECISION_MAKING = "decision_making"
    LEARNING = "learning"
    COLLABORATION = "collaboration"

@dataclass
class EpisodicMemory:
    """
    情景记忆: 具体交互事件
    灵感来源: 人类大脑海马体
    存储具体的、有时间戳的事件
    """
    episode_id: str
    timestamp: str
    interaction_type: InteractionType
    context: Dict[str, Any]
    action: str
    outcome: str
    success: bool
    emotional_valence: float
    importance_score: float
    related_episodes: List[str] = field(default_factory=list)
    consolidated: bool = False

@dataclass
class SemanticMemory:
    """
    语义记忆: 抽象知识
    灵感来源: 人类大脑皮层
    从情景记忆中抽象出的通用知识
    """
    knowledge_id: str
    domain: str
    concept: str
    definition: str
    relationships: Dict[str, str]
    confidence: float
    source_episodes: List[str]
    last_accessed: str
    access_count: int

@dataclass
class ProceduralMemory:
    """
    程序记忆: 技能模式
    灵感来源: 人类基底神经节
    可重复执行的动作序列
    """
    procedure_id: str
    name: str
    trigger_conditions: List[str]
    action_sequence: List[Dict[str, Any]]
    success_rate: float
    execution_count: int
    last_used: str
    variations: List[str] = field(default_factory=list)

@dataclass
class WorldModel:
    """
    内部世界模型
    自性的核心: 形成对世界的内部表征
    """
    entities: Dict[str, Dict[str, Any]]
    relations: Dict[str, List[Tuple[str, str]]]
    rules: Dict[str, Any]
    last_updated: str
    
    def update_entity_state(self, entity_id: str, new_state: Dict[str, Any]):
        """更新实体状态，支持动态进化"""
        if entity_id in self.entities:
            self.entities[entity_id].update(new_state)
            self.entities[entity_id]['last_updated'] = datetime.now().isoformat()
        else:
            self.entities[entity_id] = new_state
            self.entities[entity_id]['created_at'] = datetime.now().isoformat()
            self.entities[entity_id]['last_updated'] = datetime.now().isoformat()

    def add_relation(self, source: str, target: str, relation_type: str):
        """添加实体间关系，构建知识图谱"""
        if relation_type not in self.relations:
            self.relations[relation_type] = []
        if (source, target) not in self.relations[relation_type]:
            self.relations[relation_type].append((source, target))
