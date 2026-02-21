from typing import Dict, Any, List
from .memory import SpiralMemory
import time

class CheckpointManager:
    def __init__(self, memory: SpiralMemory):
        self.memory = memory

    def create_checkpoint(self, state_desc: str, metadata: Dict = None) -> str:
        """创建智能检查点"""
        checkpoint = {
            'state_desc': state_desc,
            'metadata': metadata or {},
            'timestamp': time.time(),
            # In a real system, we might serialize file contents here, but for now just description
        }
        ckpt_id = self.memory.add_checkpoint(checkpoint)
        return ckpt_id

    def list_checkpoints(self) -> List[Dict]:
        """列出所有检查点"""
        return self.memory.working_memory

    def restore_from_checkpoint(self, checkpoint_id: str = None) -> Dict:
        """从检查点恢复并跳跃"""
        # If no ID provided, use latest
        if not checkpoint_id:
            ckpt = self.memory.get_latest_checkpoint()
        else:
            # Find by ID
            ckpt = next((c for c in self.memory.working_memory if c['id'] == checkpoint_id), None)
        
        if not ckpt:
            return {"error": "No checkpoint found"}

        return {
            'restored_state': ckpt['data'],
            'message': f"Restored from {ckpt['id']} created at {ckpt['data']['timestamp']}"
        }
