"""
Smart Router v1.0 - 智能路由系统
集成到 autonomous-agent 核心模块
自动判断任务类型，选择最优执行方式
"""

import os
import sys
import json
import re
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from .paths import get_workflows_dir, resolve_project_root


class TaskType(Enum):
    STANDARD = "standard"
    REPETITIVE = "repetitive"
    ONE_TIME = "one_time"
    COMPLEX = "complex"
    UNKNOWN = "unknown"


class ExecutionMode(Enum):
    WORKFLOW = "workflow"
    BUILTIN = "builtin"
    HYBRID = "hybrid"


@dataclass
class RouteDecision:
    """路由决策结果"""
    task_type: TaskType
    execution_mode: ExecutionMode
    confidence: float
    matched_workflow: Optional[str] = None
    matched_skill: Optional[str] = None
    reason: str = ""
    recommendations: List[str] = field(default_factory=list)


class SmartRouter:
    """
    智能路由器
    
    功能:
    1. 分析任务描述，识别任务类型
    2. 匹配最佳工作流或技能
    3. 推荐执行策略
    """
    
    TASK_PATTERNS = {
        TaskType.STANDARD: [
            "安全扫描", "代码审查", "测试覆盖率", "依赖检查", "性能测试",
            "security", "review", "test", "coverage", "lint", "备份", "backup"
        ],
        TaskType.REPETITIVE: [
            "每天", "每周", "定时", "自动", "周期", "循环",
            "daily", "weekly", "schedule", "cron", "routine"
        ],
        TaskType.ONE_TIME: [
            "帮我写", "修改这个", "优化一下", "修复", "创建", "生成",
            "write", "modify", "optimize", "fix", "create", "generate"
        ],
        TaskType.COMPLEX: [
            "重构", "架构", "系统设计", "迁移", "集成", "优化系统",
            "refactor", "architecture", "design", "migrate", "integrate", "system"
        ]
    }
    
    WORKFLOW_KEYWORDS = {
        "backup-project": ["备份", "backup", "存档"],
        "code-review": ["代码审查", "code review", "review"],
        "security-scan-local": ["安全扫描", "security", "漏洞"],
        "test-automation": ["测试", "test", "自动化测试"],
        "static-webpage-development": ["网页", "网站", "前端", "html"],
        "api-documentation": ["api文档", "接口文档", "documentation"],
        "smart-release": ["发布", "release", "部署"],
        "performance-benchmark": ["性能", "performance", "benchmark"],
        "dependency-check": ["依赖", "dependency", "检查"],
        "disk-cleanup-analysis": ["清理", "cleanup", "磁盘"],
    }
    
    def __init__(self):
        self.project_root = resolve_project_root()
        self.workflows_dir = get_workflows_dir()
        self.available_workflows = self._scan_workflows()
    
    def _scan_workflows(self) -> Dict[str, Dict]:
        """扫描可用工作流"""
        workflows = {}
        
        if not self.workflows_dir.exists():
            return workflows
        
        for wf_file in self.workflows_dir.glob("*.yaml"):
            try:
                import yaml
                with open(wf_file, 'r', encoding='utf-8') as f:
                    content = yaml.safe_load(f)
                    if content:
                        workflows[wf_file.stem] = {
                            'name': content.get('name', wf_file.stem),
                            'description': content.get('description', ''),
                            'triggers': content.get('triggers', [])
                        }
            except:
                pass
        
        return workflows
    
    def route(self, task_description: str) -> RouteDecision:
        """
        智能路由 - 分析任务并推荐执行方式
        
        Args:
            task_description: 任务描述
            
        Returns:
            RouteDecision: 路由决策结果
        """
        task_lower = task_description.lower()
        
        # 1. 识别任务类型
        task_type, confidence, matched_patterns = self._analyze_task_type(task_lower)
        
        # 2. 匹配工作流
        matched_workflow = self._match_workflow(task_lower)
        
        # 3. 确定执行模式
        execution_mode = self._determine_execution_mode(task_type, matched_workflow)
        
        # 4. 生成推荐
        recommendations = self._generate_recommendations(
            task_type, execution_mode, matched_workflow, matched_patterns
        )
        
        # 5. 生成原因说明
        reason = self._generate_reason(task_type, execution_mode, matched_workflow, matched_patterns)
        
        return RouteDecision(
            task_type=task_type,
            execution_mode=execution_mode,
            confidence=confidence,
            matched_workflow=matched_workflow,
            reason=reason,
            recommendations=recommendations
        )
    
    def _analyze_task_type(self, task_lower: str) -> Tuple[TaskType, float, List[str]]:
        """分析任务类型"""
        best_match = TaskType.UNKNOWN
        best_confidence = 0.0
        matched_patterns = []
        
        for task_type, patterns in self.TASK_PATTERNS.items():
            matches = [p for p in patterns if p.lower() in task_lower]
            if matches:
                confidence = len(matches) / len(patterns) * 1.5  # 加权
                confidence = min(1.0, confidence)
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = task_type
                    matched_patterns = matches
        
        if best_match == TaskType.UNKNOWN:
            best_confidence = 0.3  # 默认置信度
        
        return best_match, best_confidence, matched_patterns
    
    def _match_workflow(self, task_lower: str) -> Optional[str]:
        """匹配工作流"""
        best_match = None
        best_score = 0.0
        
        for wf_name, keywords in self.WORKFLOW_KEYWORDS.items():
            score = 0.0
            for keyword in keywords:
                if keyword.lower() in task_lower:
                    score += 0.5
            
            # 检查工作流是否存在
            if wf_name in self.available_workflows and score > best_score:
                best_score = score
                best_match = wf_name
        
        return best_match if best_score > 0 else None
    
    def _determine_execution_mode(self, task_type: TaskType, matched_workflow: Optional[str]) -> ExecutionMode:
        """确定执行模式"""
        if matched_workflow:
            return ExecutionMode.WORKFLOW
        
        mode_map = {
            TaskType.STANDARD: ExecutionMode.WORKFLOW,
            TaskType.REPETITIVE: ExecutionMode.WORKFLOW,
            TaskType.ONE_TIME: ExecutionMode.BUILTIN,
            TaskType.COMPLEX: ExecutionMode.HYBRID,
            TaskType.UNKNOWN: ExecutionMode.BUILTIN
        }
        
        return mode_map.get(task_type, ExecutionMode.BUILTIN)
    
    def _generate_recommendations(self, task_type: TaskType, 
                                   execution_mode: ExecutionMode,
                                   matched_workflow: Optional[str],
                                   matched_patterns: List[str]) -> List[str]:
        """生成推荐"""
        recommendations = []
        
        if matched_workflow:
            recommendations.append(f"✅ 匹配工作流: {matched_workflow}")
        
        if execution_mode == ExecutionMode.WORKFLOW:
            recommendations.append("📋 建议使用预定义工作流执行")
        elif execution_mode == ExecutionMode.BUILTIN:
            recommendations.append("🔧 建议使用内置工具执行")
        elif execution_mode == ExecutionMode.HYBRID:
            recommendations.append("🔄 建议混合模式执行（工作流+内置工具）")
        
        if matched_patterns:
            recommendations.append(f"🎯 匹配关键词: {', '.join(matched_patterns[:3])}")
        
        return recommendations
    
    def _generate_reason(self, task_type: TaskType,
                         execution_mode: ExecutionMode,
                         matched_workflow: Optional[str],
                         matched_patterns: List[str]) -> str:
        """生成原因说明"""
        if matched_workflow:
            return f"识别为标准化任务，匹配工作流 '{matched_workflow}'"
        
        reasons = {
            TaskType.STANDARD: f"标准化任务，匹配关键词: {matched_patterns}",
            TaskType.REPETITIVE: f"重复性任务，适合使用工作流自动化",
            TaskType.ONE_TIME: f"一次性任务，使用内置工具快速完成",
            TaskType.COMPLEX: f"复杂任务，需要混合执行策略",
            TaskType.UNKNOWN: f"未识别任务类型，使用默认策略"
        }
        
        return reasons.get(task_type, "未知任务类型")
    
    def get_workflow_path(self, workflow_name: str) -> Optional[Path]:
        """获取工作流文件路径"""
        wf_path = self.workflows_dir / f"{workflow_name}.yaml"
        return wf_path if wf_path.exists() else None
    
    def list_available_routes(self) -> Dict[str, Any]:
        """列出所有可用路由"""
        return {
            "workflows": list(self.available_workflows.keys()),
            "task_types": [t.value for t in TaskType],
            "execution_modes": [m.value for m in ExecutionMode],
            "workflow_keywords": self.WORKFLOW_KEYWORDS
        }


# 便捷函数
def route_task(task_description: str) -> Dict[str, Any]:
    """快速路由任务"""
    router = SmartRouter()
    decision = router.route(task_description)
    
    return {
        "task_type": decision.task_type.value,
        "execution_mode": decision.execution_mode.value,
        "confidence": decision.confidence,
        "matched_workflow": decision.matched_workflow,
        "reason": decision.reason,
        "recommendations": decision.recommendations
    }
