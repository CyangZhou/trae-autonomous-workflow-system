"""
Skill Discovery v1.0 - Skill自动发现模块
参考 agent-teams-playbook 的 find-skills 设计
使用统一路径模块

回退链:
检测find-skills是否可用
    ↓ 可用
搜索匹配当前任务的Skill
    ↓ 找到
调用匹配的Skill执行
    ↓ 没找到或不可用
回退到本地已安装的Skill
    ↓ 本地也没有
使用通用流程（general-purpose agent）
"""

import json
import re
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from .paths import get_skills_dir, resolve_project_root


class SkillSource(Enum):
    LOCAL = "local"
    COMMUNITY = "community"
    BUILTIN = "builtin"
    FALLBACK = "fallback"


@dataclass
class SkillMatch:
    name: str
    source: SkillSource
    path: Optional[str] = None
    description: str = ""
    relevance_score: float = 0.0
    trigger_keywords: List[str] = field(default_factory=list)
    task_types: List[str] = field(default_factory=list)


@dataclass
class DiscoveryResult:
    task_description: str
    task_type: str
    best_match: Optional[SkillMatch] = None
    all_matches: List[SkillMatch] = field(default_factory=list)
    fallback_used: bool = False
    recommendations: List[str] = field(default_factory=list)


class SkillDiscovery:
    """
    Skill自动发现器
    
    支持三种来源:
    1. 本地已安装的Skill (.trae/skills/)
    2. 内置Agent映射
    3. 通用流程回退
    """
    
    TASK_TYPE_SKILL_MAPPING = {
        'web_development': {
            'skills': ['static-webpage-dev', 'neuro-bridge', 'local-browser'],
            'agents': ['search', 'frontend-implementation-expert'],
            'keywords': ['网页', '网站', '前端', 'html', 'css', 'javascript', 'react', 'vue', '页面']
        },
        'api_development': {
            'skills': ['neuro-bridge', 'duckduckgo-search'],
            'agents': ['architect-design-expert', 'backend-architect', 'api-specification-expert'],
            'keywords': ['api', '接口', '后端', '服务端', 'rest', 'graphql', '微服务']
        },
        'data_analysis': {
            'skills': ['duckduckgo-search', 'ai-pdf-builder'],
            'agents': ['search', 'backend-architect'],
            'keywords': ['数据分析', '可视化', '报表', '统计', '爬虫', 'etl', 'excel']
        },
        'automation': {
            'skills': ['autonomous-agent', 'neuro-bridge', 'skill-creator'],
            'agents': ['search', 'backend-architect'],
            'keywords': ['自动化', '脚本', '批量', '定时', '工作流', '批处理']
        },
        'mobile_app': {
            'skills': ['neuro-bridge'],
            'agents': ['search', 'frontend-implementation-expert'],
            'keywords': ['app', '移动端', 'android', 'ios', 'flutter', 'react native', '手机']
        },
        'quantitative_trading': {
            'skills': ['alpha-picker', 'factor-validator', 'a-share-market-analyzer'],
            'agents': ['alpha-picker', 'factor-validator', 'a-share-market-analyzer', 'stock-ranker'],
            'keywords': ['量化', '选股', '因子', '回测', '股票', '涨停', 'a股', '交易']
        },
        'content_creation': {
            'skills': ['novel-automation', 'priest-style-architect', 'prompt-crafter'],
            'agents': ['priest-style-architect', 'prompt-crafter'],
            'keywords': ['小说', '故事', '写作', '大纲', '人物', '世界观', '文章', '公众号', '博客']
        },
        'devops': {
            'skills': ['neuro-bridge', 'release-ops-expert'],
            'agents': ['release-ops-expert', 'performance-diagnostic-expert'],
            'keywords': ['部署', '发布', 'ci', 'cd', '运维', '监控', 'docker', 'k8s']
        },
        'skill_development': {
            'skills': ['trae-skill-forge', 'skill-creator', 'skill-creator-omega', 'agent-forge-master'],
            'agents': ['trae-skill-forge', 'agent-forge-master'],
            'keywords': ['技能', 'skill', 'mcp', '工具开发', '智能体', 'agent', '插件']
        },
        'testing': {
            'skills': ['neuro-bridge'],
            'agents': ['testing-validation-expert'],
            'keywords': ['测试', '单元测试', '集成测试', '自动化测试', 'qa']
        },
        'documentation': {
            'skills': ['feishu-doc-master', 'ai-pdf-builder', 'smart-navigation'],
            'agents': ['search', 'frontend-implementation-expert'],
            'keywords': ['文档', '飞书', 'pdf', '知识库', 'wiki', 'readme']
        },
        'general': {
            'skills': ['autonomous-agent', 'duckduckgo-search'],
            'agents': ['search'],
            'keywords': []
        }
    }
    
    BUILTIN_AGENTS = {
        'search': {'name': 'Researcher', 'description': '搜索和调研智能体', 'best_for': ['搜索', '调研', '查找', '分析']},
        'architect-design-expert': {'name': 'Architect', 'description': '架构设计智能体', 'best_for': ['架构', '设计', '规划', '系统']},
        'backend-architect': {'name': 'Backend Architect', 'description': '后端架构和代码实现', 'best_for': ['后端', 'api', '服务', '代码']},
        'frontend-implementation-expert': {'name': 'Frontend Expert', 'description': '前端实现智能体', 'best_for': ['前端', '界面', 'ui', '页面']},
        'testing-validation-expert': {'name': 'Testing Expert', 'description': '测试和验证智能体', 'best_for': ['测试', '验证', 'qa', '质量']},
        'trae-skill-forge': {'name': 'Skill Forge', 'description': 'Skill开发智能体', 'best_for': ['skill', '技能', '工具', 'mcp']},
        'priest-style-architect': {'name': 'Novel Architect', 'description': '小说创作智能体', 'best_for': ['小说', '故事', '写作', '创作']},
        'alpha-picker': {'name': 'Alpha Picker', 'description': '选股智能体', 'best_for': ['选股', '涨停', '股票']},
        'factor-validator': {'name': 'Factor Validator', 'description': '因子验证智能体', 'best_for': ['因子', '回测', '验证']},
        'a-share-market-analyzer': {'name': 'Market Analyzer', 'description': '市场分析智能体', 'best_for': ['市场', '行情', '分析']},
        'release-ops-expert': {'name': 'Release Expert', 'description': '发布运维智能体', 'best_for': ['发布', '部署', '运维']},
        'performance-diagnostic-expert': {'name': 'Performance Expert', 'description': '性能诊断智能体', 'best_for': ['性能', '优化', '诊断']},
        'api-specification-expert': {'name': 'API Expert', 'description': 'API规范智能体', 'best_for': ['api', '接口', '规范']},
        'prompt-crafter': {'name': 'Prompt Crafter', 'description': '提示词设计智能体', 'best_for': ['提示词', 'prompt', '设计']},
        'agent-forge-master': {'name': 'Agent Forge', 'description': '智能体锻造大师', 'best_for': ['agent', '智能体', '开发']}
    }
    
    def __init__(self, skills_dir: str = None, project_root: str = None):
        if skills_dir:
            self.skills_dir = Path(skills_dir)
        else:
            self.skills_dir = get_skills_dir()
        
        if project_root:
            self.project_root = Path(project_root)
        else:
            self.project_root = resolve_project_root()
        
        self.local_skills = self._scan_local_skills()
        self.skill_cache = {}
    
    def _scan_local_skills(self) -> Dict[str, Dict]:
        """扫描本地已安装的Skills"""
        skills = {}
        
        if not self.skills_dir.exists():
            return skills
        
        for skill_path in self.skills_dir.iterdir():
            if skill_path.is_dir() and not skill_path.name.startswith('_'):
                skill_info = self._parse_skill_metadata(skill_path)
                if skill_info:
                    skills[skill_path.name] = skill_info
        
        return skills
    
    def _parse_skill_metadata(self, skill_path: Path) -> Optional[Dict]:
        """解析Skill元数据"""
        skill_info = {
            'path': str(skill_path),
            'name': skill_path.name,
            'description': '',
            'triggers': [],
            'task_types': []
        }
        
        skill_yaml = skill_path / 'skill.yaml'
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
        
        skill_md = skill_path / 'SKILL.md'
        if skill_md.exists():
            try:
                with open(skill_md, 'r', encoding='utf-8') as f:
                    content = f.read(2000)
                    
                    if '触发词' in content:
                        trigger_match = re.search(r'触发词[：:]\s*([^\n]+)', content)
                        if trigger_match:
                            triggers = trigger_match.group(1)
                            skill_info['triggers'] = [t.strip().strip('`') for t in triggers.split('|')]
                    
                    desc_match = re.search(r'description:\s*(.+?)(?:\n|$)', content)
                    if desc_match:
                        skill_info['description'] = desc_match.group(1).strip()
            except:
                pass
        
        return skill_info
    
    def discover(self, task_description: str, task_type: str = None, ltm: Any = None) -> DiscoveryResult:
        """
        发现匹配的Skill
        
        回退链:
        1. 本地Skill匹配
        2. 任务类型映射
        3. 内置Agent
        4. 通用流程
        """
        if not task_type:
            task_type = self._infer_task_type(task_description)
        
        result = DiscoveryResult(
            task_description=task_description,
            task_type=task_type
        )
        
        local_matches = self._match_local_skills(task_description, task_type)
        result.all_matches.extend(local_matches)
        
        type_matches = self._match_by_task_type(task_description, task_type)
        for match in type_matches:
            if match.name not in [m.name for m in result.all_matches]:
                result.all_matches.append(match)
        
        agent_matches = self._match_builtin_agents(task_description)
        for match in agent_matches:
            if match.name not in [m.name for m in result.all_matches]:
                result.all_matches.append(match)
        
        # Memory-based Re-ranking (Adaptive Specialization)
        if ltm:
            self._rank_with_memory(result.all_matches, ltm, task_type)
        
        result.all_matches.sort(key=lambda x: x.relevance_score, reverse=True)
        
        if result.all_matches:
            result.best_match = result.all_matches[0]
        else:
            result.best_match = self._get_fallback()
            result.fallback_used = True
        
        result.recommendations = self._generate_recommendations(result)
        
        return result

    def _rank_with_memory(self, matches: List[SkillMatch], ltm: Any, task_type: str):
        """使用长期记忆重新排序 (自适应专精核心)"""
        try:
            stats = ltm.get_skill_stats(task_type)
            if not stats:
                return
                
            import math
            for match in matches:
                if match.name in stats:
                    skill_stat = stats[match.name]
                    # Boost score based on success rate and usage count
                    # count: log scale boost (max 0.3)
                    count_boost = min(0.3, math.log(1 + skill_stat['count']) * 0.1)
                    # success: linear boost (max 0.2)
                    success_boost = skill_stat['success_rate'] * 0.2
                    
                    match.relevance_score += (count_boost + success_boost)
                    match.description += f" [历史: {skill_stat['count']}次, {int(skill_stat['success_rate']*100)}%]"
        except Exception as e:
            # Silently fail if LTM interface doesn't match or other error
            pass

    
    def _infer_task_type(self, task_description: str) -> str:
        """推断任务类型"""
        task_lower = task_description.lower()
        
        for task_type, config in self.TASK_TYPE_SKILL_MAPPING.items():
            for keyword in config.get('keywords', []):
                if keyword in task_lower:
                    return task_type
        
        return 'general'
    
    def _match_local_skills(self, task_description: str, task_type: str) -> List[SkillMatch]:
        """匹配本地Skills"""
        matches = []
        task_lower = task_description.lower()
        
        for skill_name, skill_info in self.local_skills.items():
            score = 0.0
            
            for trigger in skill_info.get('triggers', []):
                if trigger.lower() in task_lower:
                    score += 0.5
            
            if task_type != 'general':
                type_config = self.TASK_TYPE_SKILL_MAPPING.get(task_type, {})
                if skill_name in type_config.get('skills', []):
                    score += 0.8
            
            if score > 0:
                matches.append(SkillMatch(
                    name=skill_name,
                    source=SkillSource.LOCAL,
                    path=skill_info.get('path'),
                    description=skill_info.get('description', ''),
                    relevance_score=score,
                    trigger_keywords=skill_info.get('triggers', [])
                ))
        
        return matches
    
    def _match_by_task_type(self, task_description: str, task_type: str) -> List[SkillMatch]:
        """根据任务类型匹配"""
        matches = []
        
        if task_type == 'general':
            return matches
        
        type_config = self.TASK_TYPE_SKILL_MAPPING.get(task_type, {})
        
        for skill_name in type_config.get('skills', []):
            if skill_name not in self.local_skills:
                matches.append(SkillMatch(
                    name=skill_name,
                    source=SkillSource.COMMUNITY,
                    description=f"推荐安装: {skill_name}",
                    relevance_score=0.6,
                    task_types=[task_type]
                ))
        
        return matches
    
    def _match_builtin_agents(self, task_description: str) -> List[SkillMatch]:
        """匹配内置Agents"""
        matches = []
        task_lower = task_description.lower()
        
        for agent_type, agent_info in self.BUILTIN_AGENTS.items():
            score = 0.0
            
            for keyword in agent_info.get('best_for', []):
                if keyword in task_lower:
                    score += 0.4
            
            if score > 0:
                matches.append(SkillMatch(
                    name=agent_type,
                    source=SkillSource.BUILTIN,
                    description=agent_info.get('description', ''),
                    relevance_score=min(0.9, score),
                    trigger_keywords=agent_info.get('best_for', [])
                ))
        
        return matches
    
    def _get_fallback(self) -> SkillMatch:
        """获取回退方案"""
        return SkillMatch(
            name='autonomous-agent',
            source=SkillSource.FALLBACK,
            description='通用自主执行流程',
            relevance_score=0.3
        )
    
    def _generate_recommendations(self, result: DiscoveryResult) -> List[str]:
        """生成推荐"""
        recommendations = []
        
        if result.best_match:
            if result.best_match.source == SkillSource.LOCAL:
                recommendations.append(f"✅ 找到本地Skill: {result.best_match.name}")
            elif result.best_match.source == SkillSource.BUILTIN:
                recommendations.append(f"✅ 推荐使用内置Agent: {result.best_match.name}")
            elif result.best_match.source == SkillSource.COMMUNITY:
                recommendations.append(f"💡 建议安装社区Skill: {result.best_match.name}")
                # 尝试自动安装
                install_result = self._try_install_skill(result.best_match.name)
                if install_result:
                    recommendations.append(f"📥 自动安装结果: {install_result}")
            elif result.best_match.source == SkillSource.FALLBACK:
                recommendations.append("⚠️ 使用通用流程执行")
        
        community_skills = [m for m in result.all_matches if m.source == SkillSource.COMMUNITY]
        if community_skills:
            recommendations.append(f"📦 可安装的社区Skills: {', '.join([s.name for s in community_skills[:3]])}")
        
        return recommendations
    
    def _try_install_skill(self, skill_name: str) -> Optional[str]:
        """尝试通过 skill-manager 安装技能"""
        try:
            skill_manager_path = self.skills_dir / 'skill-manager' / 'skill_manager.py'
            if not skill_manager_path.exists():
                return None
            
            import subprocess
            result = subprocess.run(
                [sys.executable, str(skill_manager_path), 'install', skill_name],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return f"✅ {skill_name} 安装成功"
            else:
                return f"❌ {skill_name} 安装失败: {result.stderr[:100]}"
        except Exception as e:
            return f"⚠️ 安装出错: {str(e)[:100]}"
    
    def search_remote_skills(self, query: str) -> List[Dict]:
        """通过 skill-market-hub 搜索远程技能"""
        try:
            skill_market_path = self.skills_dir / 'skill-market-hub' / 'skill_market_hub.py'
            if not skill_market_path.exists():
                return []
            
            # 动态导入 skill_market_hub
            sys.path.insert(0, str(self.skills_dir / 'skill-market-hub'))
            from skill_market_hub import search_github_skills
            
            return search_github_skills(query)
        except Exception as e:
            return [{"error": f"搜索失败: {str(e)}"}]
    
    def get_skill_info(self, skill_name: str) -> Optional[Dict]:
        """获取Skill详细信息"""
        if skill_name in self.local_skills:
            return self.local_skills[skill_name]
        
        if skill_name in self.BUILTIN_AGENTS:
            return self.BUILTIN_AGENTS[skill_name]
        
        return None
    
    def list_available_skills(self) -> Dict[str, List[str]]:
        """列出所有可用的Skills"""
        return {
            'local': list(self.local_skills.keys()),
            'builtin': list(self.BUILTIN_AGENTS.keys()),
            'recommended_by_task': {
                task_type: config.get('skills', []) 
                for task_type, config in self.TASK_TYPE_SKILL_MAPPING.items()
            }
        }
    
    def get_summary(self, result: DiscoveryResult) -> str:
        """获取发现结果摘要"""
        lines = [
            f"🔍 Skill发现结果",
            f"{'='*50}",
            f"任务: {result.task_description[:50]}...",
            f"类型: {result.task_type}",
            ""
        ]
        
        if result.best_match:
            source_icon = {
                SkillSource.LOCAL: "📁",
                SkillSource.BUILTIN: "🔧",
                SkillSource.COMMUNITY: "🌐",
                SkillSource.FALLBACK: "🔄"
            }.get(result.best_match.source, "❓")
            
            lines.append(f"最佳匹配: {source_icon} {result.best_match.name}")
            lines.append(f"  来源: {result.best_match.source.value}")
            lines.append(f"  相关度: {result.best_match.relevance_score:.0%}")
            lines.append(f"  描述: {result.best_match.description}")
        
        if result.all_matches:
            lines.append("")
            lines.append("所有匹配:")
            for i, match in enumerate(result.all_matches[:5], 1):
                lines.append(f"  {i}. {match.name} ({match.relevance_score:.0%})")
        
        if result.recommendations:
            lines.append("")
            lines.append("推荐:")
            for rec in result.recommendations:
                lines.append(f"  {rec}")
        
        return "\n".join(lines)
