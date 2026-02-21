"""
Unified Kernel Repair Mixin
"""
import json
from typing import Dict, Any, List, Optional

from core.workflow_repair import WorkflowRepairEngine

class KernelRepairMixin:
    """
    维修内核Mixin - 负责工作流维修和安全性检查
    """
    def check_safety(self, action: str, target: str) -> Dict[str, Any]:
        """
        M3: 确认协议 - 检查操作安全性
        """
        destructive_keywords = ['delete', 'remove', 'format', 'drop', 'truncate', 'rm', 'del']
        action_lower = action.lower()
        
        is_destructive = any(k == action_lower for k in destructive_keywords)
        
        if is_destructive:
            # Check if target is critical
            critical_paths = ['.git', '.env', 'secrets', 'config']
            is_critical = any(p in target for p in critical_paths)
            
            return {
                "safe": False,
                "requires_confirmation": True,
                "risk_level": "high" if is_critical else "medium",
                "message": f"⚠️ Destructive action detected: {action} {target}. Confirmation required (Timeout=60s)."
            }
            
        return {"safe": True, "requires_confirmation": False, "risk_level": "low"}

    def repair_scan(self):
        """扫描所有组件"""
        engine = WorkflowRepairEngine()
        result = engine.scan()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    def repair_validate(self):
        """验证调用关系"""
        engine = WorkflowRepairEngine()
        result = engine.validate()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    def repair_detect_new(self):
        """检测新增组件"""
        engine = WorkflowRepairEngine()
        result = engine.detect_new()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    def repair_sync(self):
        """同步项目规则"""
        engine = WorkflowRepairEngine()
        result = engine.sync_rules()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    def repair_full(self):
        """执行完整维修"""
        engine = WorkflowRepairEngine()
        report = engine.full_repair()
        result = engine.get_report_dict(report)
        print(json.dumps(result, ensure_ascii=False, indent=2))
