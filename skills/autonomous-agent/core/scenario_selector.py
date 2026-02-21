"""
Scenario Selector v1.0 - 5场景决策树模块
参考 agent-teams-playbook 设计理念
使用统一路径模块

决策树:
Q1: 任务复杂度？
├── 简单(1-2步) → 场景1：提示增强
├── 中等(3-5步) → Q2: 有现成Skill可复用？
│   ├── 是 → 场景2：Skill复用
│   └── 否 → 场景3：计划+评审（默认）
└── 复杂(6+步) → Q3: 需要明确团队分工？
    ├── 是 → 场景4：Lead-Member
    └── 否 → 场景5：复合编排
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from .paths import get_skills_dir


class ScenarioType(Enum):
    PROMPT_ENHANCEMENT = "prompt_enhancement"
    SKILL_REUSE = "skill_reuse"
    PLAN_REVIEW = "plan_review"
    LEAD_MEMBER = "lead_member"
    COMPOSITE = "composite"


@dataclass
class ScenarioInfo:
    scenario_type: ScenarioType
    name: str
    description: str
    complexity_range: Tuple[int, int]
    requires_confirmation: bool = True
    requires_skill_discovery: bool = False
    requires_team_coordination: bool = False
    max_agents: int = 1
    estimated_steps: int = 1
    best_practices: List[str] = field(default_factory=list)


class ScenarioSelector:
    """
    5场景决策树选择器
    
    场景1: 提示增强 (Prompt Enhancement)
    - 复杂度: 1-2
    - 特点: 任务简单，不需要组队
    - 示例: "帮我改个函数名"
    
    场景2: Skill复用 (Skill Reuse)
    - 复杂度: 3-5
    - 特点: 有现成Skill能用，直接调用
    - 示例: "帮我写篇公众号" → 调gzh-writer
    
    场景3: 计划+评审 (Plan + Review)
    - 复杂度: 3-5
    - 特点: 出计划→确认→执行→Review
    - 示例: "重构认证模块"（最常用）
    
    场景4: Lead-Member (Lead-Member)
    - 复杂度: 6-10
    - 特点: Leader协调，Member并行干活
    - 示例: "做一个完整的用户系统"
    
    场景5: 复合编排 (Composite)
    - 复杂度: 6-10
    - 特点: 动态组合上面的场景
    - 示例: "从0搭建一个SaaS产品"
    """
    
    SCENARIOS = {
        ScenarioType.PROMPT_ENHANCEMENT: ScenarioInfo(
            scenario_type=ScenarioType.PROMPT_ENHANCEMENT,
            name="提示增强",
            description="任务简单，增强提示后直接执行",
            complexity_range=(1, 2),
            requires_confirmation=False,
            requires_skill_discovery=False,
            requires_team_coordination=False,
            max_agents=1,
            estimated_steps=1,
            best_practices=[
                "明确具体需求",
                "提供上下文",
                "指定输出格式"
            ]
        ),
        ScenarioType.SKILL_REUSE: ScenarioInfo(
            scenario_type=ScenarioType.SKILL_REUSE,
            name="Skill复用",
            description="有现成Skill可用，直接调用执行",
            complexity_range=(3, 5),
            requires_confirmation=False,
            requires_skill_discovery=True,
            requires_team_coordination=False,
            max_agents=1,
            estimated_steps=2,
            best_practices=[
                "先搜索匹配Skill",
                "确认Skill适用范围",
                "按Skill要求提供参数"
            ]
        ),
        ScenarioType.PLAN_REVIEW: ScenarioInfo(
            scenario_type=ScenarioType.PLAN_REVIEW,
            name="计划+评审",
            description="出计划→确认→执行→Review",
            complexity_range=(3, 5),
            requires_confirmation=False,
            requires_skill_discovery=True,
            requires_team_coordination=False,
            max_agents=3,
            estimated_steps=4,
            best_practices=[
                "详细列出任务分解",
                "等待用户确认计划",
                "执行后进行Review",
                "质量把关后交付"
            ]
        ),
        ScenarioType.LEAD_MEMBER: ScenarioInfo(
            scenario_type=ScenarioType.LEAD_MEMBER,
            name="Lead-Member",
            description="Leader协调，Member并行执行",
            complexity_range=(6, 10),
            requires_confirmation=True,
            requires_skill_discovery=True,
            requires_team_coordination=True,
            max_agents=5,
            estimated_steps=5,
            best_practices=[
                "明确Leader职责",
                "定义Member角色",
                "设置检查点",
                "并行执行子任务",
                "汇总整合结果"
            ]
        ),
        ScenarioType.COMPOSITE: ScenarioInfo(
            scenario_type=ScenarioType.COMPOSITE,
            name="复合编排",
            description="动态组合多种场景",
            complexity_range=(6, 10),
            requires_confirmation=True,
            requires_skill_discovery=True,
            requires_team_coordination=True,
            max_agents=10,
            estimated_steps=7,
            best_practices=[
                "分解为多个子项目",
                "为每个子项目选择场景",
                "设置里程碑",
                "分阶段验收",
                "最终整合交付"
            ]
        )
    }
    
    TEAM_COORDINATION_KEYWORDS = [
        "团队", "协作", "分工", "多人", "并行", "同时",
        "系统", "平台", "项目", "产品", "完整", "全栈",
        "前端后端", "数据库", "架构", "微服务", "模块"
    ]
    
    SKILL_KEYWORDS = {
        'web_development': ['网页', '网站', '前端', 'html', 'css', 'react', 'vue'],
        'api_development': ['api', '接口', '后端', '服务端', 'rest'],
        'data_analysis': ['数据分析', '可视化', '报表', '统计'],
        'content_creation': ['公众号', '文章', '博客', '写作', '小说'],
        'automation': ['自动化', '脚本', '批量', '工作流'],
        'quantitative_trading': ['量化', '选股', '因子', '回测'],
        'skill_development': ['技能', 'skill', 'mcp', '工具开发']
    }
    
    def __init__(self, skills_dir: str = None):
        if skills_dir:
            self.skills_dir = Path(skills_dir)
        else:
            self.skills_dir = get_skills_dir()
        
        self.available_skills = self._discover_local_skills()
    
    def _discover_local_skills(self) -> Dict[str, Dict]:
        """发现本地已安装的Skills"""
        skills = {}
        
        if not self.skills_dir.exists():
            return skills
        
        for skill_path in self.skills_dir.iterdir():
            if skill_path.is_dir():
                skill_md = skill_path / 'SKILL.md'
                skill_yaml = skill_path / 'skill.yaml'
                
                skill_info = {'path': str(skill_path), 'name': skill_path.name}
                
                if skill_yaml.exists():
                    try:
                        import yaml
                        with open(skill_yaml, 'r', encoding='utf-8') as f:
                            yaml_content = yaml.safe_load(f)
                            if yaml_content:
                                skill_info['name'] = yaml_content.get('name', skill_path.name)
                                skill_info['description'] = yaml_content.get('description', '')
                    except:
                        pass
                
                if skill_md.exists():
                    try:
                        with open(skill_md, 'r', encoding='utf-8') as f:
                            content = f.read(500)
                            if 'name:' in content:
                                match = re.search(r'name:\s*(\S+)', content)
                                if match:
                                    skill_info['name'] = match.group(1)
                    except:
                        pass
                
                skills[skill_path.name] = skill_info
        
        return skills
    
    def select(self, complexity: int, task_description: str, 
               has_matching_skill: bool = None) -> ScenarioInfo:
        """
        根据复杂度和任务描述选择场景
        
        决策树:
        Q1: 任务复杂度？
        ├── 简单(1-2步) → 场景1：提示增强
        ├── 中等(3-5步) → Q2: 有现成Skill可复用？
        │   ├── 是 → 场景2：Skill复用
        │   └── 否 → 场景3：计划+评审（默认）
        └── 复杂(6+步) → Q3: 需要明确团队分工？
            ├── 是 → 场景4：Lead-Member
            └── 否 → 场景5：复合编排
        """
        if has_matching_skill is None:
            has_matching_skill = self._check_skill_match(task_description)
        
        needs_coordination = self._check_team_coordination(task_description)
        
        if complexity <= 2:
            return self.SCENARIOS[ScenarioType.PROMPT_ENHANCEMENT]
        
        elif complexity <= 5:
            if has_matching_skill:
                return self.SCENARIOS[ScenarioType.SKILL_REUSE]
            else:
                return self.SCENARIOS[ScenarioType.PLAN_REVIEW]
        
        else:
            if needs_coordination:
                return self.SCENARIOS[ScenarioType.LEAD_MEMBER]
            else:
                return self.SCENARIOS[ScenarioType.COMPOSITE]
    
    def _check_skill_match(self, task_description: str) -> bool:
        """检查是否有匹配的Skill"""
        task_lower = task_description.lower()
        
        for skill_type, keywords in self.SKILL_KEYWORDS.items():
            for keyword in keywords:
                if keyword in task_lower:
                    matching_skill = self._find_matching_skill(skill_type)
                    if matching_skill:
                        return True
        
        for skill_name, skill_info in self.available_skills.items():
            if skill_name.lower() in task_lower:
                return True
        
        return False
    
    def _find_matching_skill(self, skill_type: str) -> Optional[str]:
        """查找匹配的Skill"""
        skill_mapping = {
            'web_development': ['static-webpage-dev', 'neuro-bridge'],
            'api_development': ['neuro-bridge', 'backend-architect'],
            'data_analysis': ['duckduckgo-search', 'ai-pdf-builder'],
            'content_creation': ['novel-automation', 'priest-style-architect'],
            'automation': ['autonomous-agent', 'neuro-bridge'],
            'quantitative_trading': ['alpha-picker', 'factor-validator'],
            'skill_development': ['trae-skill-forge', 'skill-creator']
        }
        
        candidates = skill_mapping.get(skill_type, [])
        for candidate in candidates:
            if candidate in self.available_skills:
                return candidate
        
        return None
    
    def _check_team_coordination(self, task_description: str) -> bool:
        """检查是否需要团队协作"""
        for keyword in self.TEAM_COORDINATION_KEYWORDS:
            if keyword in task_description:
                return True
        
        step_indicators = ['然后', '接着', '再', '之后', '最后', '第一步', '第二步', '第三步']
        step_count = sum(1 for ind in step_indicators if ind in task_description)
        
        return step_count >= 3
    
    def get_scenario_by_type(self, scenario_type: ScenarioType) -> ScenarioInfo:
        """根据类型获取场景信息"""
        return self.SCENARIOS.get(scenario_type)
    
    def get_all_scenarios(self) -> Dict[ScenarioType, ScenarioInfo]:
        """获取所有场景"""
        return self.SCENARIOS
    
    def get_execution_plan(self, scenario: ScenarioInfo, task_description: str) -> Dict[str, Any]:
        """生成执行计划"""
        plan = {
            'scenario': scenario.name,
            'scenario_type': scenario.scenario_type.value,
            'task': task_description,
            'requires_confirmation': scenario.requires_confirmation,
            'estimated_steps': scenario.estimated_steps,
            'max_agents': scenario.max_agents,
            'phases': []
        }
        
        if scenario.scenario_type == ScenarioType.PROMPT_ENHANCEMENT:
            plan['phases'] = [
                {'name': '提示增强', 'description': '优化用户提示', 'agents': 1},
                {'name': '直接执行', 'description': '执行增强后的任务', 'agents': 1}
            ]
        
        elif scenario.scenario_type == ScenarioType.SKILL_REUSE:
            plan['phases'] = [
                {'name': 'Skill匹配', 'description': '查找匹配的Skill', 'agents': 1},
                {'name': '用户确认', 'description': '确认使用该Skill', 'agents': 0, 'requires_user': True},
                {'name': 'Skill执行', 'description': '调用Skill执行任务', 'agents': 1}
            ]
        
        elif scenario.scenario_type == ScenarioType.PLAN_REVIEW:
            plan['phases'] = [
                {'name': '任务分析', 'description': '分解任务，制定计划', 'agents': 1},
                {'name': '用户确认', 'description': '确认执行计划', 'agents': 0, 'requires_user': True},
                {'name': '并行执行', 'description': '并行执行子任务', 'agents': scenario.max_agents},
                {'name': '质量Review', 'description': '检查结果质量', 'agents': 1},
                {'name': '交付', 'description': '交付最终结果', 'agents': 1}
            ]
        
        elif scenario.scenario_type == ScenarioType.LEAD_MEMBER:
            plan['phases'] = [
                {'name': '团队组建', 'description': '组建Leader和Member团队', 'agents': 1},
                {'name': '用户确认', 'description': '确认团队配置', 'agents': 0, 'requires_user': True},
                {'name': '任务分配', 'description': 'Leader分配子任务', 'agents': 1},
                {'name': '并行执行', 'description': 'Members并行执行', 'agents': scenario.max_agents},
                {'name': '结果汇总', 'description': 'Leader汇总结果', 'agents': 1},
                {'name': '质量把关', 'description': '质量检查和打磨', 'agents': 1},
                {'name': '交付', 'description': '交付最终结果', 'agents': 1}
            ]
        
        elif scenario.scenario_type == ScenarioType.COMPOSITE:
            plan['phases'] = [
                {'name': '项目分解', 'description': '分解为多个子项目', 'agents': 1},
                {'name': '场景选择', 'description': '为每个子项目选择场景', 'agents': 1},
                {'name': '用户确认', 'description': '确认整体计划', 'agents': 0, 'requires_user': True},
                {'name': '分阶段执行', 'description': '按阶段执行各子项目', 'agents': scenario.max_agents},
                {'name': '里程碑验收', 'description': '各阶段验收', 'agents': 1},
                {'name': '整合优化', 'description': '整合所有结果', 'agents': 1},
                {'name': '最终交付', 'description': '交付完整产品', 'agents': 1}
            ]
        
        return plan
    
    def get_summary(self, scenario: ScenarioInfo) -> str:
        """获取场景摘要"""
        lines = [
            f"📋 场景: {scenario.name}",
            f"{'='*50}",
            f"描述: {scenario.description}",
            f"复杂度范围: {scenario.complexity_range[0]}-{scenario.complexity_range[1]}",
            f"需要确认: {'是' if scenario.requires_confirmation else '否'}",
            f"最大Agent数: {scenario.max_agents}",
            f"预计步骤: {scenario.estimated_steps}",
            "",
            "最佳实践:"
        ]
        
        for i, practice in enumerate(scenario.best_practices, 1):
            lines.append(f"  {i}. {practice}")
        
        return "\n".join(lines)
