import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime

from .models import (
    EpisodicMemory, SemanticMemory, ProceduralMemory, WorldModel, InteractionType
)

class MemoryStorage:
    """
    记忆持久化层
    负责将记忆对象序列化为JSON并保存到磁盘
    """
    
    def __init__(self, memory_dir: Path):
        self.memory_dir = memory_dir
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
    def load_episodic(self) -> List[EpisodicMemory]:
        path = self.memory_dir / "episodic.json"
        if not path.exists():
            return []
            
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [
                    EpisodicMemory(
                        episode_id=e["episode_id"],
                        timestamp=e["timestamp"],
                        interaction_type=InteractionType(e["interaction_type"]),
                        context=e["context"],
                        action=e["action"],
                        outcome=e["outcome"],
                        success=e["success"],
                        emotional_valence=e["emotional_valence"],
                        importance_score=e["importance_score"],
                        related_episodes=e.get("related_episodes", []),
                        consolidated=e.get("consolidated", False)
                    ) for e in data.get("episodes", [])
                ]
        except Exception as e:
            print(f"Error loading episodic memory: {e}")
            return []

    def load_semantic(self) -> Dict[str, SemanticMemory]:
        path = self.memory_dir / "semantic.json"
        if not path.exists():
            return {}
            
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                result = {}
                for k, v in data.get("knowledge", {}).items():
                    result[k] = SemanticMemory(**v)
                return result
        except Exception as e:
            print(f"Error loading semantic memory: {e}")
            return {}

    def load_procedural(self) -> Dict[str, ProceduralMemory]:
        path = self.memory_dir / "procedural.json"
        if not path.exists():
            return {}
            
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                result = {}
                for k, v in data.get("procedures", {}).items():
                    result[k] = ProceduralMemory(**v)
                return result
        except Exception as e:
            print(f"Error loading procedural memory: {e}")
            return {}

    def load_world_model(self) -> WorldModel:
        path = self.memory_dir / "world_model.json"
        default_model = WorldModel(
            entities={},
            relations={},
            rules={},
            last_updated=datetime.now().isoformat()
        )
        
        if not path.exists():
            return default_model
            
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Convert relations back to tuples if needed (JSON stores lists)
                relations = {}
                for k, v in data.get("relations", {}).items():
                    relations[k] = [tuple(pair) for pair in v]
                    
                return WorldModel(
                    entities=data.get("entities", {}),
                    relations=relations,
                    rules=data.get("rules", {}),
                    last_updated=data.get("last_updated", datetime.now().isoformat())
                )
        except Exception as e:
            print(f"Error loading world model: {e}")
            return default_model

    def save_episodic(self, episodes: List[EpisodicMemory], max_items: int):
        path = self.memory_dir / "episodic.json"
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({
                "episodes": [
                    {
                        "episode_id": e.episode_id,
                        "timestamp": e.timestamp,
                        "interaction_type": e.interaction_type.value,
                        "context": e.context,
                        "action": e.action,
                        "outcome": e.outcome,
                        "success": e.success,
                        "emotional_valence": e.emotional_valence,
                        "importance_score": e.importance_score,
                        "related_episodes": e.related_episodes,
                        "consolidated": e.consolidated,
                    }
                    for e in episodes[-max_items:]
                ]
            }, f, ensure_ascii=False, indent=2)

    def save_semantic(self, knowledge: Dict[str, SemanticMemory], max_items: int):
        path = self.memory_dir / "semantic.json"
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({
                "knowledge": {
                    k: {
                        "knowledge_id": v.knowledge_id,
                        "domain": v.domain,
                        "concept": v.concept,
                        "definition": v.definition,
                        "relationships": v.relationships,
                        "confidence": v.confidence,
                        "source_episodes": v.source_episodes,
                        "last_accessed": v.last_accessed,
                        "access_count": v.access_count,
                    }
                    for k, v in list(knowledge.items())[-max_items:]
                }
            }, f, ensure_ascii=False, indent=2)

    def save_procedural(self, procedures: Dict[str, ProceduralMemory], max_items: int):
        path = self.memory_dir / "procedural.json"
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({
                "procedures": {
                    k: {
                        "procedure_id": v.procedure_id,
                        "name": v.name,
                        "trigger_conditions": v.trigger_conditions,
                        "action_sequence": v.action_sequence,
                        "success_rate": v.success_rate,
                        "execution_count": v.execution_count,
                        "last_used": v.last_used,
                        "variations": v.variations,
                    }
                    for k, v in list(procedures.items())[-max_items:]
                }
            }, f, ensure_ascii=False, indent=2)

    def save_world_model(self, model: WorldModel):
        path = self.memory_dir / "world_model.json"
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({
                "entities": model.entities,
                "relations": {k: [list(pair) for pair in v] for k, v in model.relations.items()},
                "rules": model.rules,
                "last_updated": model.last_updated,
            }, f, ensure_ascii=False, indent=2)
