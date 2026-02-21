"""
智能分析引擎 v1.0
增强版：5场景决策树 + 增强复杂度计算 + Skill发现集成
使用统一路径模块
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from .scenario_selector import ScenarioSelector, ScenarioType
from .skill_discovery import SkillDiscovery
from .paths import resolve_project_root, get_knowledge_dir, get_workflows_dir, get_swarm_dir


class IntelligentAssistant:
    """
    智能分析引擎 v1.0
    
    新增功能:
    - 5场景决策树
    - 增强复杂度计算
    - Skill自动发现
    - 用户确认节点
    """
    
    def __init__(self, knowledge_dir=None, workflows_dir=None, agent_registry=None):
        if knowledge_dir:
            self.knowledge_dir = Path(knowledge_dir)
        else:
            self.knowledge_dir = get_knowledge_dir()
        
        if workflows_dir:
            self.workflows_dir = Path(workflows_dir)
        else:
            self.workflows_dir = get_workflows_dir()
        
        if agent_registry:
            self.agent_registry_path = Path(agent_registry)
        else:
            self.agent_registry_path = get_swarm_dir() / 'agent_registry.json'
        
        self.scenario_selector = ScenarioSelector()
        self.skill_discovery = SkillDiscovery()
        
        self._load_patterns()
        self._load_agent_registry()
    
    def _load_patterns(self):
        self.task_patterns = {
            'web_development': {
                'keywords': ['网页', '网站', '前端', 'html', 'css', 'javascript', 'react', 'vue', '页面', 'ui'],
                'complexity_base': 4,
                'typical_steps': 3
            },
            'api_development': {
                'keywords': ['api', '接口', '后端', '服务端', 'rest', 'graphql', '微服务'],
                'complexity_base': 5,
                'typical_steps': 4
            },
            'data_analysis': {
                'keywords': ['数据分析', '可视化', '报表', '统计', '爬虫', 'etl', 'excel'],
                'complexity_base': 5,
                'typical_steps': 4
            },
            'automation': {
                'keywords': ['自动化', '脚本', '批量', '定时', '工作流', '批处理'],
                'complexity_base': 4,
                'typical_steps': 3
            },
            'mobile_app': {
                'keywords': ['app', '移动端', 'android', 'ios', 'flutter', 'react native', '手机应用'],
                'complexity_base': 6,
                'typical_steps': 5
            },
            'quantitative_trading': {
                'keywords': ['量化', '选股', '因子', '回测', '股票', '涨停', 'a股', '交易策略'],
                'complexity_base': 6,
                'typical_steps': 5
            },
            'content_creation': {
                'keywords': ['小说', '故事', '写作', '大纲', '人物', '世界观', '文章', '公众号', '博客'],
                'complexity_base': 4,
                'typical_steps': 3
            },
            'devops': {
                'keywords': ['部署', '发布', 'ci', 'cd', '运维', '监控', 'docker', 'k8s'],
                'complexity_base': 5,
                'typical_steps': 4
            },
            'skill_development': {
                'keywords': ['技能', 'skill', 'mcp', '工具开发', '智能体', 'agent', '插件'],
                'complexity_base': 5,
                'typical_steps': 4
            },
            'testing': {
                'keywords': ['测试', '单元测试', '集成测试', '自动化测试', 'qa'],
                'complexity_base': 4,
                'typical_steps': 3
            },
            'documentation': {
                'keywords': ['文档', '飞书', 'pdf', '知识库', 'wiki', 'readme'],
                'complexity_base': 3,
                'typical_steps': 2
            }
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
                    recommended.append({
                        'type': agent_type,
                        'name': agent_info.get('name', agent_type),
                        'description': agent_info.get('description', ''),
                        'score': 80,
                        'priority': 'high',
                        'source': 'builtin'
                    })
        
        task_lower = task_description.lower()
        for agent_type, agent_info in builtin_agents.items():
            if agent_type not in [r['type'] for r in recommended]:
                for keyword in agent_info.get('best_for', []):
                    if keyword.lower() in task_lower:
                        recommended.append({
                            'type': agent_type,
                            'name': agent_info.get('name', agent_type),
                            'description': agent_info.get('description', ''),
                            'score': 60,
                            'priority': 'medium',
                            'source': 'builtin'
                        })
                        break
        
        recommended.sort(key=lambda x: x['score'], reverse=True)
        return recommended[:5]
    
    def analyze(self, task_description: str, project_root: str = '.', preferred_agents: List[str] = None, ltm: Any = None) -> Dict[str, Any]:
        """
        增强版任务分析
        
        新增输出:
        - scenario: 场景类型
        - scenario_info: 场景详细信息
        - requires_confirmation: 是否需要用户确认
        - skill_discovery: Skill发现结果
        - execution_plan: 执行计划
        """
        task_lower = task_description.lower()
        task_type = self._identify_task_type(task_lower)
        
        complexity = self._calculate_complexity_enhanced(task_description, task_type)
        
        # Pass LTM for Adaptive Specialization
        skill_result = self.skill_discovery.discover(task_description, task_type, ltm=ltm)
        has_matching_skill = skill_result.best_match is not None and skill_result.best_match.source.value != 'fallback'
        
        scenario = self.scenario_selector.select(complexity, task_description, has_matching_skill)
        
        execution_mode = self._determine_execution_mode(complexity)
        confidence = self._calculate_confidence(task_description, task_type)
        thinking_mode = self._determine_thinking_mode(confidence)
        
        if preferred_agents:
            agents = [{
                'type': t,
                'name': t,
                'description': '',
                'score': 100,
                'priority': 'high',
                'source': 'user_specified'
            } for t in preferred_agents if self.get_agent_info(t)]
        else:
            agents = self.recommend_agents_agents(task_type, task_description)
        
        execution_plan = self.scenario_selector.get_execution_plan(scenario, task_description)
        
        # 匹配工作流
        recommended_workflows = self._match_workflows(task_description)
        
        result = {
            'execution_mode': execution_mode,
            'thinking_mode': thinking_mode,
            'complexity_score': complexity,
            'confidence': confidence,
            'task_type': task_type,
            
            'scenario': scenario.scenario_type.value,
            'scenario_name': scenario.name,
            'scenario_info': {
                'name': scenario.name,
                'description': scenario.description,
                'requires_confirmation': scenario.requires_confirmation,
                'max_agents': scenario.max_agents,
                'estimated_steps': scenario.estimated_steps
            },
            'requires_confirmation': scenario.requires_confirmation,
            
            'skill_discovery': {
                'best_match': skill_result.best_match.name if skill_result.best_match else None,
                'source': skill_result.best_match.source.value if skill_result.best_match else None,
                'all_matches': [{'name': m.name, 'score': m.relevance_score} for m in skill_result.all_matches[:5]],
                'recommendations': skill_result.recommendations
            },
            
            'recommended_workflows': recommended_workflows,
            'recommended_skills': [skill_result.best_match.name] if skill_result.best_match else [],
            'recommended_agents': agents,
            
            'execution_plan': execution_plan
        }
        
        if execution_mode in ['parallel', 'hybrid']:
            result['subtasks'] = self._split_task_with_agents(task_description, task_type, complexity, agents)
        
        return result
    
    def _determine_execution_mode(self, complexity: int) -> str:
        """根据复杂度决定执行模式 (M2: 决策树)"""
        if complexity <= 2:
            return 'one-shot'
        elif complexity <= 5:
            return 'sequential'
        elif complexity <= 7:
            return 'parallel'
        else:
            return 'hybrid'

    def _determine_thinking_mode(self, confidence: float) -> str:
        """根据置信度决定思考模式 (M1: 思考模式)"""
        if confidence >= 0.85:
            return 'Fast'
        elif confidence >= 0.5:
            return 'Slow'
        else:
            return 'Knowledge'

    def _match_workflows(self, task_description: str) -> List[Dict]:
        """匹配本地工作流 - 增强版"""
        matches = []
        if not self.workflows_dir.exists():
            return matches
            
        task_lower = task_description.lower()
        
        workflow_keywords = {
            'static-webpage-development': ['网页', '网站', '前端', 'html', 'css', '静态页面', 'webpage', 'landing'],
            'api-documentation': ['api文档', '接口文档', 'api documentation', 'swagger', 'openapi'],
            'code-review': ['代码审查', 'code review', '代码评审', 'review'],
            'code-refactor': ['重构', 'refactor', '优化代码', '代码优化'],
            'test-automation': ['测试', 'test', '单元测试', '自动化测试', 'pytest'],
            'docker-build-local': ['docker', '容器', 'container', '镜像'],
            'python-ci-local': ['ci', '持续集成', 'python', '构建'],
            'security-scan-local': ['安全', 'security', '漏洞', '扫描'],
            'release-notes': ['发布', 'release', '版本', '更新日志'],
            'git-commit-summary': ['git', 'commit', '提交', '版本控制'],
            'pr-review-assistant': ['pr', 'pull request', '合并请求'],
            'data-processing': ['数据', 'data', '处理', 'etl', '转换'],
            'content-publisher': ['发布', 'publish', '内容', '文章'],
            'smart-release': ['发布', 'release', '部署', 'deploy'],
            'swarm-execution': ['swarm', '蜂群', '并行', '多任务'],
            'skill-invoke-workflow': ['skill', '技能', '调用', 'invoke'],
            'intelligent-trigger': ['智能', '触发', '自动'],
            'backup-project': ['备份', 'backup', '项目'],
            'project-stats': ['统计', 'stats', '项目信息'],
            'changelog-generator': ['changelog', '变更日志', '更新记录'],
            'dependency-check': ['依赖', 'dependency', '检查'],
            'performance-benchmark': ['性能', 'performance', '基准测试', 'benchmark'],
            'log-anomaly-detection': ['日志', 'log', '异常', 'anomaly'],
            'meeting-minutes-auto': ['会议', 'meeting', '纪要', 'minutes'],
            'email-automation': ['邮件', 'email', '自动化'],
            'invoice-processing': ['发票', 'invoice', '财务'],
            'sales-lead-nurturing': ['销售', 'sales', '线索', 'lead'],
            'support-ticket-automation': ['工单', 'ticket', '客服', 'support'],
            'youtube-research': ['youtube', '视频', '研究', 'research'],
            'resume-screening': ['简历', 'resume', '招聘', 'hr'],
            'debt-recovery': ['债务', 'debt', '催收', 'recovery'],
            'slack-message-classifier': ['slack', '消息', '分类', 'classifier'],
            'smart-router': ['路由', 'router', '智能路由'],
            'html': ['html', '页面', '标记'],
            'android-bookkeeping': ['android', '记账', 'bookkeeping', 'app'],
            'create-readme': ['readme', '文档', '说明'],
            'daily-standup': ['站会', 'standup', '每日', 'daily'],
            'doc-sync-check': ['文档同步', 'sync', '检查'],
            'disk-cleanup-analysis': ['磁盘', 'disk', '清理', 'cleanup'],
            'license-compliance': ['许可证', 'license', '合规', 'compliance'],
            'issue-stale-manager': ['issue', '过期', 'stale', '管理'],
            'pr-size-labeler': ['pr', 'label', '标签', '大小'],
            'dependency-auto-update': ['依赖', 'update', '自动更新'],
            'workflow-system-optimization': ['工作流', 'workflow', '优化', 'optimization']
        }
        
        for workflow_file in self.workflows_dir.glob('*.yaml'):
            name = workflow_file.stem
            score = 0
            matched_keywords = []
            
            name_parts = name.replace('-', ' ').replace('_', ' ').split()
            for part in name_parts:
                if len(part) >= 3 and part in task_lower:
                    score += 15
                    matched_keywords.append(part)
            
            if name in workflow_keywords:
                for keyword in workflow_keywords[name]:
                    if keyword in task_lower:
                        score += 25
                        matched_keywords.append(keyword)
            
            try:
                with open(workflow_file, 'r', encoding='utf-8') as f:
                    content = f.read(1000).lower()
                    for keyword in task_lower.split():
                        if len(keyword) >= 2 and keyword in content:
                            score += 5
            except:
                pass
            
            if score > 0:
                matches.append({
                    'name': name,
                    'path': str(workflow_file),
                    'score': score,
                    'matched_keywords': matched_keywords[:5],
                    'description': f"Workflow: {name}"
                })
        
        matches.sort(key=lambda x: x['score'], reverse=True)
        return matches[:5]

    def recommend_agents_agents(self, task_type: str, task_description: str) -> List[Dict]:
        """推荐Agent（使用Skill发现结果）"""
        skill_result = self.skill_discovery.discover(task_description, task_type)
        
        agents = []
        for match in skill_result.all_matches:
            if match.source.value in ['builtin', 'local']:
                agents.append({
                    'type': match.name,
                    'name': match.name,
                    'description': match.description,
                    'score': int(match.relevance_score * 100),
                    'priority': 'high' if match.relevance_score > 0.7 else 'medium',
                    'source': match.source.value
                })
        
        if not agents:
            agents = self.recommend_agents(task_type, task_description)
        
        return agents[:5]
    
    def _identify_task_type(self, task_lower: str) -> str:
        for task_type, pattern in self.task_patterns.items():
            for keyword in pattern['keywords']:
                if keyword in task_lower:
                    return task_type
        return 'general'
    
    def _calculate_complexity_enhanced(self, task: str, task_type: str) -> int:
        """
        增强版复杂度计算
        
        考虑因素:
        - 任务类型基础复杂度
        - 步骤数量
        - 依赖关系
        - 集成需求
        - 性能要求
        - 安全要求
        - 任务长度
        """
        base = self.task_patterns.get(task_type, {}).get('complexity_base', 3)
        modifiers = 0
        
        step_indicators = ['然后', '接着', '再', '之后', '最后', '第一步', '第二步', '第三步', '第四步', '第五步']
        step_count = sum(1 for ind in step_indicators if ind in task)
        if step_count >= 1: modifiers += 1
        if step_count >= 3: modifiers += 1
        if step_count >= 5: modifiers += 1
        
        if '集成' in task or '整合' in task: modifiers += 1
        if '多' in task and ('模块' in task or '功能' in task or '系统' in task): modifiers += 2
        if '高并发' in task or '性能' in task: modifiers += 1
        if '安全' in task or '加密' in task: modifiers += 1
        if '测试' in task and ('完整' in task or '全面' in task): modifiers += 1
        if '部署' in task or '上线' in task: modifiers += 1
        if '文档' in task: modifiers += 0.5
        
        if '从零' in task or '从0' in task or '完整' in task: modifiers += 2
        if '重构' in task: modifiers += 1
        if '优化' in task: modifiers += 1
        
        if len(task) > 100: modifiers += 1
        if len(task) > 200: modifiers += 1
        if len(task) > 400: modifiers += 1
        
        return min(10, max(1, int(base + modifiers)))
    
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
            'researcher': 'search',
            'coder': 'backend-architect',
            'frontend': 'frontend-implementation-expert',
            'tester': 'testing-validation-expert',
            'architect': 'architect-design-expert',
            'visualizer': 'frontend-implementation-expert',
            'analyst': 'factor-validator',
            'writer': 'priest-style-architect',
            'reviewer': 'testing-validation-expert'
        }
        
        for i, subtask in enumerate(base_subtasks):
            if i < len(recommended_agents):
                subtask['type'] = recommended_agents[i]['type']
            else:
                subtask['type'] = agent_type_mapping.get(subtask['role'], 'search')
            subtask['context'] = task
            subtask['created_at'] = datetime.now().isoformat()
        
        if complexity >= 8:
            base_subtasks.append({
                'type': 'release-ops-expert',
                'role': 'devops',
                'goal': '准备部署和发布流程',
                'context': task,
                'created_at': datetime.now().isoformat()
            })
        
        return base_subtasks
    
    def get_scenario_for_task(self, task_description: str) -> Dict[str, Any]:
        """快速获取任务场景"""
        task_type = self._identify_task_type(task_description.lower())
        complexity = self._calculate_complexity_enhanced(task_description, task_type)
        skill_result = self.skill_discovery.discover(task_description, task_type)
        has_skill = skill_result.best_match is not None
        
        scenario = self.scenario_selector.select(complexity, task_description, has_skill)
        
        return {
            'task_type': task_type,
            'complexity': complexity,
            'scenario': scenario.scenario_type.value,
            'scenario_name': scenario.name,
            'requires_confirmation': scenario.requires_confirmation,
            'best_skill': skill_result.best_match.name if skill_result.best_match else None
        }
