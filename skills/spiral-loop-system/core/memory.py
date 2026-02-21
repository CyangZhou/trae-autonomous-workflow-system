import json
import os
import time
from typing import Dict, List, Any, Optional

class SpiralMemory:
    def __init__(self, memory_dir: str = ".trae/memory/spiral"):
        self.memory_dir = memory_dir
        self.instant_memory_file = os.path.join(memory_dir, "instant_memory.json")
        self.working_memory_file = os.path.join(memory_dir, "working_memory.json")
        self.long_term_memory_file = os.path.join(memory_dir, "long_term_memory.json")
        
        self._ensure_dir()
        self.instant_memory = self._load(self.instant_memory_file, [])
        self.working_memory = self._load(self.working_memory_file, []) # Checkpoints stack
        self.long_term_memory = self._load(self.long_term_memory_file, {}) # Patterns

    def _ensure_dir(self):
        if not os.path.exists(self.memory_dir):
            os.makedirs(self.memory_dir)

    def _load(self, filepath: str, default: Any) -> Any:
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return default
        return default

    def _save(self, filepath: str, data: Any):
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add_instant_node(self, node_content: str, metadata: Dict = None):
        """Level 1: 瞬时记忆 - 记录当前节点"""
        node = {
            "id": f"node_{int(time.time()*1000)}",
            "content": node_content,
            "timestamp": time.time(),
            "metadata": metadata or {}
        }
        self.instant_memory.append(node)
        # Keep only last 50 nodes for instant context
        if len(self.instant_memory) > 50:
            self.instant_memory.pop(0)
        self._save(self.instant_memory_file, self.instant_memory)
        return node["id"]

    def add_checkpoint(self, checkpoint_data: Dict):
        """Level 2: 工作记忆 - 存储检查点"""
        checkpoint = {
            "id": f"ckpt_{int(time.time()*1000)}",
            "data": checkpoint_data,
            "timestamp": time.time()
        }
        self.working_memory.append(checkpoint)
        self._save(self.working_memory_file, self.working_memory)
        return checkpoint["id"]

    def get_latest_checkpoint(self) -> Optional[Dict]:
        if self.working_memory:
            return self.working_memory[-1]
        return None

    def store_pattern(self, pattern_name: str, pattern_data: Dict):
        """Level 3: 长期记忆 - 固化模式"""
        self.long_term_memory[pattern_name] = {
            "data": pattern_data,
            "timestamp": time.time(),
            "hits": 0
        }
        self._save(self.long_term_memory_file, self.long_term_memory)

    def get_pattern(self, pattern_name: str) -> Optional[Dict]:
        if pattern_name in self.long_term_memory:
            self.long_term_memory[pattern_name]["hits"] += 1
            self._save(self.long_term_memory_file, self.long_term_memory)
            return self.long_term_memory[pattern_name]
        return None

    def get_recent_nodes(self, limit: int = 5) -> List[Dict]:
        return self.instant_memory[-limit:]
