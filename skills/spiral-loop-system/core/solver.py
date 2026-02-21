import time
from typing import Dict, List, Optional
from .memory import SpiralMemory

class SpiralLoopSolver:
    def __init__(self, memory_dir: str = ".trae/memory/spiral"):
        self.memory = SpiralMemory(memory_dir)
        self.path_graph = {} # Ephemeral for now, or persist if needed
        self.last_jump_ts = 0

    def detect_interruption(self, current_state: str) -> str:
        """检测任务中断节点（空气墙）"""
        # Simple loop detection: check if current state matches recent nodes
        recent_nodes = self.memory.get_recent_nodes(limit=10)
        
        # Check for repetition in content (simplistic hash or direct compare)
        # In real usage, this might be embeddings, but let's stick to text for now.
        content_hashes = [hash(n['content']) for n in recent_nodes]
        current_hash = hash(current_state)
        
        if current_hash in content_hashes:
            return "linear_loop"
        
        # Check for 'stuck' pattern (e.g., error messages repeating)
        error_count = sum(1 for n in recent_nodes if "Error" in n['content'])
        if error_count > 3:
             return "stuck_error"

        return "normal"

    def connect_nodes(self, prev_node_id: str, new_node_id: str, edge_weight: float = 1.0):
        """建立节点连接（修复断连）"""
        # This function is conceptual in the doc, practically it logs the transition
        transition = {
            "from": prev_node_id,
            "to": new_node_id,
            "weight": edge_weight,
            "timestamp": time.time()
        }
        # In a full graph implementation, we'd add edges.
        # Here we just log it to memory as a transition event
        self.memory.add_instant_node(f"Transition: {prev_node_id} -> {new_node_id}", metadata=transition)

    def node_jump(self, from_node: str, jump_strategy: str = "spiral") -> Dict:
        """节点跳跃策略"""
        strategies = {
            "spiral": self._spiral_jump, # 螺旋上升
            "lateral": self._lateral_jump, # 横向跳跃
            "quantum": self._quantum_jump # 量子跳跃
        }
        strategy_func = strategies.get(jump_strategy, self._spiral_jump)
        return strategy_func(from_node)

    def _spiral_jump(self, from_node: str) -> Dict:
        return {
            "strategy": "spiral",
            "action": "elevate_abstraction",
            "description": "尝试提升抽象层级，从更高维度重新审视问题，寻找新路径。",
            "suggestion": "总结当前困境的模式，尝试完全不同的切入点。"
        }

    def _lateral_jump(self, from_node: str) -> Dict:
        return {
            "strategy": "lateral",
            "action": "try_alternative",
            "description": "尝试平行方案，寻找同维度的替代路径。",
            "suggestion": "列出3个替代方案，选择未尝试过的一个。"
        }

    def _quantum_jump(self, from_node: str) -> Dict:
        return {
            "strategy": "quantum",
            "action": "break_context",
            "description": "完全跳出当前上下文，引入随机性或外部知识。",
            "suggestion": "引入一个完全不相关的概念或工具，强制打破当前思维定势。"
        }
