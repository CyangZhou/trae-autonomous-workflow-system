"""
Unified Kernel Base Mixin
"""
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from core.memory import MemoryManager
from core.execution_tracker import ExecutionTracker, get_tracker
from core.ltm import LongTermMemory

class KernelBaseMixin:
    """
    基础内核Mixin - 提供共享状态
    """
    def __init__(self):
        # State
        self.session_id = None
        self.current_scenario = None
        self.execution_result = {}
        
        # Core components
        self.memory = MemoryManager()
        self.ltm = LongTermMemory()
        self.tracker = None
        
    def init(self):
        """初始化内核"""
        print(json.dumps({
            "status": "success",
            "message": "Kernel v2.0 initialized (Modular)",
            "timestamp": datetime.now().isoformat(),
            "modules": [
                "intelligence", "swarm", "workflow", "reflexion", "memory",
                "quality_gate", "scenario_selector", "skill_discovery", "delivery_doc",
                "execution_tracker"
            ],
            "version": "2.0"
        }, ensure_ascii=False, indent=2))
