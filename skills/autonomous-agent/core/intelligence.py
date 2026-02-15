"""
智能分析引擎 v3.1
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


class IntelligentAssistant:
    def __init__(self, knowledge_dir='.trae/knowledge', workflows_dir='.trae/workflows', agent_registry='.trae/swarm/agent_registry.json'):
        self.knowledge_dir = Path(knowledge_dir)
        self.workflows_dir = Path(workflows_dir)
        self.agent_registry_path = Path(agent_registry)
        self._load_patterns()
        self._load_agent_registry()
    
    def _load_patterns(self):
        self.task_patterns = {
            'web_development': {'keywords': ['网页', '网站', '前端', 'html', 'css', 'javascript', 'react', 'vue'], 'complexity_base': 4},
            'api_development': {'keywords': ['api', '接口', '后端', '服务端', 'rest', 'graphql'], 'complexity_base': 5},
            'data_analysis': {'keywords': ['数据分析', '可视化', '报表', '统计', '爬虫', 'etl'], 'complexity_base': 5},
            'automation': {'keywords': ['自动化', '脚本', '批量', '定时', '工作流'], 'complexity_base': 4},
            'mobile_app': {'keywords': ['app', '移动端', 'android', 'ios', 'flutter', 'react native'], 'complexity_base': 6},
            'quantitative_trading': {'keywords': ['量化', '选股', '因子', '回测', '股票', '涨停', 'a股'], 'complexity_base': 6},
            'content_creation': {'keywords': ['小说', '故事', '写作', '大纲', '人物', '世界观'], 'complexity_base': 4},
            'devops': {'keywords': ['部署', '发布', 'ci', 'cd', '运维', '监控'], 'complexity_base': 5},
            'skill_development': {'keywords': ['技能', 'skill', 'mcp', '工具开发', '智能体'], 'complexity_base': 5}
        }
    
    def _load_agent_registry(self):
        if self.agent_registry_path.exists():
            with open(self.agent_registry_path, 'r', encoding='utf-8') as f:
                self.agent_registry = json.load(f)
        else:
            self.agent_registry = {'builtin_agents': {}, 'custom_agents': {}, 'task_type_mapping': {}}
    
    def get_agent_info(self, agent_type: str) -> Optional[Dict]:
        builtin = self.agent_registry.get('builtin_agents', {})
        custom = self.agent_registry.get('custom_agents', {})
        return builtin.get(agent_type) or custom.get(agent_type)
    
    def recommend_agents(self, task_type: str, task_description: str) -> List[Dict]:
        task_mapping = self.agent_registry.get('task_type_mapping', {})
        builtin_agents = self.agent_registry.get('builtin_agents', {})
        recommended = []
        
        if task_type in task_mapping:
            for agent_type in task_mapping[task_type]:
                agent_info = self.get_agent_info(agent_type)
                if agent_info:
                    recommended.append({'type': agent_type, 'name': agent_info.get('name', agent_type), 'description': agent_info.get('description', ''), 'score': 80, 'priority': 'high', 'source': 'builtin'})
        
        task_lower = task_description.lower()
        for agent_type, agent_info in builtin_agents.items():
            if agent_type not in [r['type'] for r in recommended]:
                for keyword in agent_info.get('best_for', []):
                    if keyword.lower() in task_lower:
                        recommended.append({'type': agent_type, 'name': agent_info.get('name', agent_type), 'description': agent_info.get('description', ''), 'score': 60, 'priority': 'medium', 'source': 'builtin'})
                        break
        
        recommended.sort(key=lambda x: x['score'], reverse=True)
        return recommended[:5]
    
    def analyze(self, task_description: str, project_root: str = '.', preferred_agents: List[str] = None) -> Dict[str, Any]:
        task_lower = task_description.lower()
        task_type = self._identify_task_type(task_lower)
        complexity = self._calculate_complexity(task_description, task_type)
        execution_mode = 'swarm' if complexity >= 6 else 'single_agent'
        confidence = self._calculate_confidence(task_description, task_type)
        
        if preferred_agents:
            agents = [{'type': t, 'name': t, 'description': '', 'score': 100, 'priority': 'high', 'source': 'user_specified'} for t in preferred_agents if self.get_agent_info(t)]
        else:
            agents = self.recommend_agents(task_type, task_description)
        
        result = {
            'execution_mode': execution_mode, 'complexity_score': complexity, 'confidence': confidence,
            'task_type': task_type, 'recommended_workflows': [], 'recommended_skills': self._recommend_skills(task_type),
            'recommended_agents': agents
        }
        
        if execution_mode == 'swarm':
            result['subtasks'] = self._split_task_with_agents(task_description, task_type, complexity, agents)
        
        return result
    
    def _identify_task_type(self, task_lower: str) -> str:
        for task_type, pattern in self.task_patterns.items():
            for keyword in pattern['keywords']:
                if keyword in task_lower:
                    return task_type
        return 'general'
    
    def _calculate_complexity(self, task: str, task_type: str) -> int:
        base = self.task_patterns.get(task_type, {}).get('complexity_base', 3)
        modifiers = 0
        if '集成' in task or '整合' in task: modifiers += 1
        if '多' in task and ('模块' in task or '功能' in task or '系统' in task): modifiers += 2
        if '高并发' in task or '性能' in task: modifiers += 1
        if '安全' in task: modifiers += 1
        if '测试' in task: modifiers += 1
        if '部署' in task or '上线' in task: modifiers += 1
        if len(task) > 100: modifiers += 1
        if len(task) > 200: modifiers += 1
        return min(10, base + modifiers)
    
    def _calculate_confidence(self, task: str, task_type: str) -> float:
        if task_type == 'general': return 0.5
        base = 0.7
        if (self.knowledge_dir / task_type).exists(): base += 0.1
        if len(task) > 50: base += 0.1
        return min(1.0, base)
    
    def _recommend_skills(self, task_type: str) -> List[str]:
        mapping = {
            'web_development': ['static-webpage-dev', 'neuro-bridge'],
            'api_development': ['neuro-bridge', 'duckduckgo-search'],
            'data_analysis': ['duckduckgo-search', 'ai-pdf-builder'],
            'automation': ['autonomous-agent', 'neuro-bridge'],
            'quantitative_trading': ['alpha-picker', 'factor-validator'],
            'content_creation': ['priest-style-architect', 'prompt-crafter'],
            'skill_development': ['trae-skill-forge', 'agent-forge-master']
        }
        return mapping.get(task_type, ['autonomous-agent'])
    
    def _split_task_with_agents(self, task: str, task_type: str, complexity: int, recommended_agents: List[Dict]) -> List[Dict[str, Any]]:
        templates = {
            'web_development': [
                {'role': 'researcher', 'goal': '调研技术方案和最佳实践'},
                {'role': 'coder', 'goal': '实现核心功能代码'},
                {'role': 'frontend', 'goal': '实现前端界面'},
                {'role': 'tester', 'goal': '编写测试用例并验证'}
            ],
            'api_development': [
                {'role': 'architect', 'goal': '设计API规范'},
                {'role': 'coder', 'goal': '实现API端点'},
                {'role': 'tester', 'goal': '编写API测试'}
            ],
            'data_analysis': [
                {'role': 'researcher', 'goal': '调研数据源和分析方法'},
                {'role': 'coder', 'goal': '实现数据处理逻辑'},
                {'role': 'visualizer', 'goal': '实现可视化界面'}
            ],
            'quantitative_trading': [
                {'role': 'researcher', 'goal': '调研市场数据和因子'},
                {'role': 'analyst', 'goal': '因子有效性分析'},
                {'role': 'coder', 'goal': '实现选股策略'},
                {'role': 'tester', 'goal': '回测验证'}
            ],
            'content_creation': [
                {'role': 'architect', 'goal': '设计大纲和世界观'},
                {'role': 'writer', 'goal': '撰写正文内容'},
                {'role': 'reviewer', 'goal': '审核和优化'}
            ],
            'general': [
                {'role': 'researcher', 'goal': '调研相关信息'},
                {'role': 'coder', 'goal': '实现核心功能'}
            ]
        }
        
        base_subtasks = templates.get(task_type, templates['general'])
        agent_type_mapping = {
            'researcher': 'search', 'coder': 'backend-architect', 'frontend': 'frontend-implementation-expert',
            'tester': 'testing-validation-expert', 'architect': 'architect-design-expert',
            'visualizer': 'frontend-implementation-expert', 'analyst': 'factor-validator',
            'writer': 'priest-style-architect', 'reviewer': 'testing-validation-expert'
        }
        
        for i, subtask in enumerate(base_subtasks):
            if i < len(recommended_agents):
                subtask['type'] = recommended_agents[i]['type']
            else:
                subtask['type'] = agent_type_mapping.get(subtask['role'], 'search')
            subtask['context'] = task
            subtask['created_at'] = datetime.now().isoformat()
        
        if complexity >= 8:
            base_subtasks.append({'type': 'release-ops-expert', 'role': 'devops', 'goal': '准备部署和发布流程', 'context': task, 'created_at': datetime.now().isoformat()})
        
        return base_subtasks
