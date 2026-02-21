import re
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from .models import (
    EpisodicMemory, SemanticMemory, ProceduralMemory, WorldModel, 
    InteractionType, MemoryLayer
)
from .storage import MemoryStorage

class LongTermMemory:
    """
    长期记忆系统
    
    核心理念 (OMNE):
    长期记忆是AI自我进化的基础
    灵感来源: 人类大脑皮层柱状结构
    
    三层架构:
    1. 情景记忆 (Episodic) - 具体交互事件
    2. 语义记忆 (Semantic) - 抽象知识
    3. 程序记忆 (Procedural) - 技能模式
    """
    
    CONSOLIDATION_THRESHOLD = 3
    IMPORTANCE_DECAY = 0.95
    MAX_EPISODIC_MEMORY = 1000
    MAX_SEMANTIC_MEMORY = 500
    MAX_PROCEDURAL_MEMORY = 100
    
    def __init__(self, memory_dir: str = None):
        if memory_dir:
            self.memory_dir = Path(memory_dir)
        else:
            self.memory_dir = Path("自动化工作流组件库/memory/ltm")
        
        self.storage = MemoryStorage(self.memory_dir)
        
        # Load memory from storage
        self.episodic_memory: List[EpisodicMemory] = self.storage.load_episodic()
        self.semantic_memory: Dict[str, SemanticMemory] = self.storage.load_semantic()
        self.procedural_memory: Dict[str, ProceduralMemory] = self.storage.load_procedural()
        self.world_model: WorldModel = self.storage.load_world_model()
    
    def _save_memory(self):
        """持久化记忆"""
        self.storage.save_episodic(self.episodic_memory, self.MAX_EPISODIC_MEMORY)
        self.storage.save_semantic(self.semantic_memory, self.MAX_SEMANTIC_MEMORY)
        self.storage.save_procedural(self.procedural_memory, self.MAX_PROCEDURAL_MEMORY)
        self.storage.save_world_model(self.world_model)
    
    def store_interaction(self, interaction: Dict[str, Any]) -> str:
        """
        存储交互数据
        
        核心能力: 从交互中学习
        """
        episode_id = self._generate_episode_id()
        
        emotional_valence = self._calculate_emotional_valence(interaction)
        importance_score = self._calculate_importance(interaction)
        
        episode = EpisodicMemory(
            episode_id=episode_id,
            timestamp=datetime.now().isoformat(),
            interaction_type=InteractionType(
                interaction.get("type", "task_execution")
            ),
            context=interaction.get("context", {}),
            action=interaction.get("action", ""),
            outcome=interaction.get("outcome", ""),
            success=interaction.get("success", True),
            emotional_valence=emotional_valence,
            importance_score=importance_score,
        )
        
        self.episodic_memory.append(episode)
        
        self._consolidate_to_semantic(episode)
        
        if episode.success:
            self._extract_procedure(episode)
        
        self._update_world_model(episode)
        
        if len(self.episodic_memory) % 10 == 0:
            self._save_memory()
        
        return episode_id
    
    def _generate_episode_id(self) -> str:
        """生成情景ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        return f"EP_{timestamp}"
    
    def _calculate_emotional_valence(self, interaction: Dict) -> float:
        """计算情感效价"""
        if interaction.get("success", True):
            return 0.7 + 0.3 * min(1.0, interaction.get("quality_score", 0.5))
        else:
            return -0.5 - 0.5 * min(1.0, interaction.get("severity", 0.5))
    
    def _calculate_importance(self, interaction: Dict) -> float:
        """计算重要性分数"""
        score = 0.5
        
        if not interaction.get("success", True):
            score += 0.3
        
        if interaction.get("type") == "error_resolution":
            score += 0.2
        
        complexity = interaction.get("complexity", 1)
        score += min(0.2, complexity * 0.05)
        
        if interaction.get("novel", False):
            score += 0.2
        
        return min(1.0, score)
    
    def _consolidate_to_semantic(self, episode: EpisodicMemory):
        """
        整合为语义知识
        
        核心能力: 从具体经验中抽象通用知识
        """
        if not episode.success:
            return
        
        concepts = self._extract_concepts(episode)
        
        for concept, definition in concepts.items():
            knowledge_id = self._generate_knowledge_id(concept)
            
            if knowledge_id in self.semantic_memory:
                existing = self.semantic_memory[knowledge_id]
                existing.source_episodes.append(episode.episode_id)
                existing.access_count += 1
                existing.confidence = min(1.0, existing.confidence + 0.05)
            else:
                self.semantic_memory[knowledge_id] = SemanticMemory(
                    knowledge_id=knowledge_id,
                    domain=self._detect_domain(episode),
                    concept=concept,
                    definition=definition,
                    relationships={},
                    confidence=0.6,
                    source_episodes=[episode.episode_id],
                    last_accessed=datetime.now().isoformat(),
                    access_count=1,
                )
        
        episode.consolidated = True
    
    def _extract_concepts(self, episode: EpisodicMemory) -> Dict[str, str]:
        """从情景中提取概念"""
        concepts = {}
        
        action = episode.action.lower()
        
        patterns = {
            r"使用\s+(\w+)\s+实现": lambda m: (f"技术:{m.group(1)}", f"使用{m.group(1)}技术实现功能"),
            r"创建\s+(\w+)\s+(组件|模块|类)": lambda m: (f"组件:{m.group(1)}", f"{m.group(1)}{m.group(2)}的创建方法"),
            r"修复\s+(\w+)\s+错误": lambda m: (f"错误修复:{m.group(1)}", f"{m.group(1)}类型错误的修复方法"),
            r"优化\s+(\w+)": lambda m: (f"优化策略:{m.group(1)}", f"{m.group(1)}的优化方法"),
        }
        
        for pattern, extractor in patterns.items():
            match = re.search(pattern, action)
            if match:
                concept, definition = extractor(match)
                concepts[concept] = definition
        
        if episode.success and episode.interaction_type == InteractionType.TASK_EXECUTION:
            concepts["成功模式"] = f"在{episode.context.get('task_type', '未知')}任务中的成功模式"
        
        return concepts
    
    def _detect_domain(self, episode: EpisodicMemory) -> str:
        """检测领域"""
        context = episode.context
        if "domain" in context:
            return context["domain"]
        
        action = episode.action.lower()
        domain_keywords = {
            "frontend": ["react", "vue", "css", "html", "组件", "页面"],
            "backend": ["api", "数据库", "服务", "接口"],
            "devops": ["部署", "docker", "ci", "cd", "k8s"],
            "testing": ["测试", "test", "pytest", "jest"],
        }
        
        for domain, keywords in domain_keywords.items():
            if any(kw in action for kw in keywords):
                return domain
        
        return "general"
    
    def _generate_knowledge_id(self, concept: str) -> str:
        """生成知识ID"""
        return hashlib.md5(concept.encode()).hexdigest()[:12]
    
    def _extract_procedure(self, episode: EpisodicMemory):
        """
        提取程序记忆
        
        核心能力: 从成功经验中提取可重复的技能模式
        """
        if not episode.success:
            return
        
        procedure_name = self._generate_procedure_name(episode)
        procedure_id = self._generate_knowledge_id(procedure_name)
        
        trigger_conditions = self._extract_triggers(episode)
        action_sequence = self._extract_action_sequence(episode)
        
        if procedure_id in self.procedural_memory:
            existing = self.procedural_memory[procedure_id]
            existing.execution_count += 1
            existing.success_rate = (
                existing.success_rate * 0.9 + 1.0 * 0.1
            )
            existing.last_used = datetime.now().isoformat()
        else:
            self.procedural_memory[procedure_id] = ProceduralMemory(
                procedure_id=procedure_id,
                name=procedure_name,
                trigger_conditions=trigger_conditions,
                action_sequence=action_sequence,
                success_rate=1.0,
                execution_count=1,
                last_used=datetime.now().isoformat(),
            )
    
    def _generate_procedure_name(self, episode: EpisodicMemory) -> str:
        """生成程序名称"""
        task_type = episode.context.get("task_type", "general")
        skill_name = episode.context.get("skill_name", "unknown")
        return f"{task_type}_{skill_name}"

    def get_skill_stats(self, task_type: str) -> Dict[str, Dict[str, Any]]:
        """
        获取技能使用统计
        
        用于自适应专精: 返回 {skill_name: {count, success_rate, last_used}}
        """
        stats = {}
        # Iterate through values of the procedural_memory dictionary
        for proc in self.procedural_memory.values():
            if proc.name.startswith(f"{task_type}_"):
                # Extract skill name from procedure name (e.g., "web_development_react_app" -> "react_app")
                # Careful: skill names might contain underscores.
                # Assuming format is {task_type}_{skill_name}
                prefix = f"{task_type}_"
                skill_name = proc.name[len(prefix):]
                stats[skill_name] = {
                    "count": proc.execution_count,
                    "success_rate": proc.success_rate,
                    "last_used": proc.last_used
                }
        return stats
    
    def _extract_triggers(self, episode: EpisodicMemory) -> List[str]:
        """提取触发条件"""
        triggers = []
        
        context = episode.context
        if "task_type" in context:
            triggers.append(f"任务类型为{context['task_type']}")
        
        if "keywords" in context:
            triggers.extend([f"包含关键词: {kw}" for kw in context["keywords"][:3]])
        
        return triggers
    
    def _extract_action_sequence(self, episode: EpisodicMemory) -> List[Dict[str, Any]]:
        """提取动作序列"""
        return [
            {
                "step": 1,
                "action": episode.action,
                "context": episode.context,
            }
        ]
    
    def _update_world_model(self, episode: EpisodicMemory):
        """
        更新世界模型
        
        核心能力: 形成对世界的内部表征
        """
        entities = self._extract_entities(episode)
        for entity_name, entity_data in entities.items():
            if entity_name in self.world_model.entities:
                self.world_model.entities[entity_name]["encounter_count"] += 1
                self.world_model.entities[entity_name]["last_seen"] = episode.timestamp
            else:
                self.world_model.entities[entity_name] = {
                    "type": entity_data.get("type", "unknown"),
                    "encounter_count": 1,
                    "first_seen": episode.timestamp,
                    "last_seen": episode.timestamp,
                }
        
        relations = self._extract_relations(episode)
        for relation_type, pairs in relations.items():
            if relation_type not in self.world_model.relations:
                self.world_model.relations[relation_type] = []
            for pair in pairs:
                if pair not in self.world_model.relations[relation_type]:
                    self.world_model.relations[relation_type].append(pair)
        
        if episode.success:
            rule = self._extract_rule(episode)
            if rule:
                rule_id = hashlib.md5(rule.encode()).hexdigest()[:8]
                self.world_model.rules[rule_id] = {
                    "content": rule,
                    "confidence": 0.7,
                    "source_episode": episode.episode_id,
                }
        
        self.world_model.last_updated = datetime.now().isoformat()
    
    def _extract_entities(self, episode: EpisodicMemory) -> Dict[str, Dict]:
        """提取实体"""
        entities = {}
        
        tech_keywords = re.findall(
            r'\b(python|javascript|react|vue|docker|api|sql|git)\b',
            episode.action.lower()
        )
        for kw in tech_keywords:
            entities[kw] = {"type": "technology"}
        
        for key, value in episode.context.items():
            if isinstance(value, str) and len(value) < 50:
                entities[value] = {"type": "context_entity"}
        
        return entities
    
    def _extract_relations(self, episode: EpisodicMemory) -> Dict[str, List[Tuple[str, str]]]:
        """提取关系"""
        relations = {}
        
        action = episode.action.lower()
        
        uses_matches = re.findall(r'使用\s+(\w+)\s+(实现|创建|构建)\s+(\w+)', action)
        for match in uses_matches:
            if "uses" not in relations:
                relations["uses"] = []
            relations["uses"].append((match[0], match[2]))
        
        return relations
    
    def _extract_rule(self, episode: EpisodicMemory) -> Optional[str]:
        """提取规则"""
        if episode.interaction_type == InteractionType.ERROR_RESOLUTION:
            return f"遇到{episode.context.get('error_type', '未知')}错误时，可以尝试{episode.action}"
        return None
    
    def retrieve_relevant(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        检索相关记忆
        
        核心能力: 向量检索 + 语义匹配
        """
        results = {
            "episodic": [],
            "semantic": [],
            "procedural": [],
        }
        
        query_lower = query.lower()
        query_keywords = set(re.findall(r'\w+', query_lower))
        
        episodic_scores = []
        for episode in self.episodic_memory:
            score = 0.0
            
            action_keywords = set(re.findall(r'\w+', episode.action.lower()))
            keyword_overlap = len(query_keywords & action_keywords)
            score += keyword_overlap * 0.3
            
            if episode.importance_score > 0.7:
                score += 0.2
            
            if episode.success:
                score += 0.1
            
            if score > 0:
                episodic_scores.append((episode, score))
        
        episodic_scores.sort(key=lambda x: x[1], reverse=True)
        results["episodic"] = [
            {
                "episode_id": e.episode_id,
                "action": e.action,
                "outcome": e.outcome,
                "success": e.success,
                "relevance": s,
            }
            for e, s in episodic_scores[:top_k]
        ]
        
        semantic_scores = []
        for knowledge_id, knowledge in self.semantic_memory.items():
            score = 0.0
            
            concept_keywords = set(re.findall(r'\w+', knowledge.concept.lower()))
            keyword_overlap = len(query_keywords & concept_keywords)
            score += keyword_overlap * 0.4
            
            score += knowledge.confidence * 0.3
            
            if score > 0:
                semantic_scores.append((knowledge, score))
        
        semantic_scores.sort(key=lambda x: x[1], reverse=True)
        results["semantic"] = [
            {
                "concept": k.concept,
                "definition": k.definition,
                "confidence": k.confidence,
                "relevance": s,
            }
            for k, s in semantic_scores[:top_k]
        ]
        
        procedural_scores = []
        for proc_id, procedure in self.procedural_memory.items():
            score = 0.0
            
            for trigger in procedure.trigger_conditions:
                trigger_keywords = set(re.findall(r'\w+', trigger.lower()))
                keyword_overlap = len(query_keywords & trigger_keywords)
                score += keyword_overlap * 0.3
            
            score += procedure.success_rate * 0.3
            
            if score > 0:
                procedural_scores.append((procedure, score))
        
        procedural_scores.sort(key=lambda x: x[1], reverse=True)
        results["procedural"] = [
            {
                "name": p.name,
                "trigger_conditions": p.trigger_conditions,
                "success_rate": p.success_rate,
                "relevance": s,
            }
            for p, s in procedural_scores[:top_k]
        ]
        
        return results
    
    def get_world_model_summary(self) -> Dict[str, Any]:
        """获取世界模型摘要"""
        return {
            "entities_count": len(self.world_model.entities),
            "relations_count": sum(len(v) for v in self.world_model.relations.values()),
            "rules_count": len(self.world_model.rules),
            "episodic_count": len(self.episodic_memory),
            "semantic_count": len(self.semantic_memory),
            "procedural_count": len(self.procedural_memory),
            "last_updated": self.world_model.last_updated,
            "top_entities": sorted(
                self.world_model.entities.items(),
                key=lambda x: x[1].get("encounter_count", 0),
                reverse=True
            )[:10],
        }
    
    def evolve(self, new_interaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        自我进化: 从新交互中学习
        
        核心能力: 模型在推理时持续进化，而非重新训练
        """
        episode_id = self.store_interaction(new_interaction)
        
        self._prune_memory()
        
        self._save_memory()
        
        return {
            "episode_id": episode_id,
            "memory_stats": {
                "episodic": len(self.episodic_memory),
                "semantic": len(self.semantic_memory),
                "procedural": len(self.procedural_memory),
            },
            "world_model": self.get_world_model_summary(),
        }
    
    def _prune_memory(self):
        """记忆修剪 - 移除不重要的旧记忆"""
        if len(self.episodic_memory) > self.MAX_EPISODIC_MEMORY:
            self.episodic_memory.sort(key=lambda x: x.importance_score, reverse=True)
            self.episodic_memory = self.episodic_memory[:self.MAX_EPISODIC_MEMORY]
        
        for knowledge in self.semantic_memory.values():
            knowledge.confidence *= self.IMPORTANCE_DECAY
        
        low_confidence = [
            k for k, v in self.semantic_memory.items()
            if v.confidence < 0.3
        ]
        for k in low_confidence:
            del self.semantic_memory[k]
    
    def get_memory_report(self) -> Dict[str, Any]:
        """获取记忆报告"""
        return {
            "summary": {
                "episodic_memory": len(self.episodic_memory),
                "semantic_memory": len(self.semantic_memory),
                "procedural_memory": len(self.procedural_memory),
                "world_model_entities": len(self.world_model.entities),
            },
            "recent_episodes": [
                {
                    "id": e.episode_id,
                    "type": e.interaction_type.value,
                    "success": e.success,
                    "importance": e.importance_score,
                }
                for e in self.episodic_memory[-5:]
            ],
            "top_knowledge": sorted(
                self.semantic_memory.values(),
                key=lambda x: x.confidence,
                reverse=True
            )[:5],
            "top_procedures": sorted(
                self.procedural_memory.values(),
                key=lambda x: x.success_rate * x.execution_count,
                reverse=True
            )[:5],
            "world_model": self.get_world_model_summary(),
        }
