"""
Intelligent Monitor v1.0 - 智能监控系统
集成到 autonomous-agent 核心模块
主动感知上下文并推荐工作流
"""

import os
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field

from .paths import resolve_project_root, get_workflows_dir, get_skills_dir


@dataclass
class ContextAnalysis:
    """上下文分析结果"""
    project_type: Optional[str] = None
    files_changed: List[str] = field(default_factory=list)
    git_status: Dict = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class WorkflowRecommendation:
    """工作流推荐"""
    workflow_name: str
    confidence: float
    reason: str
    triggers: List[str] = field(default_factory=list)


class IntelligentMonitor:
    """
    智能监控器
    
    功能:
    1. 分析项目上下文
    2. 检测文件变更
    3. 推荐合适的工作流
    4. 监控项目健康状态
    """
    
    PROJECT_TYPE_INDICATORS = {
        'python': ['requirements.txt', 'setup.py', 'pyproject.toml', 'Pipfile'],
        'nodejs': ['package.json', 'package-lock.json', 'yarn.lock', 'node_modules'],
        'rust': ['Cargo.toml', 'Cargo.lock'],
        'go': ['go.mod', 'go.sum'],
        'java': ['pom.xml', 'build.gradle'],
        'docker': ['Dockerfile', 'docker-compose.yml', '.dockerignore'],
    }
    
    WORKFLOW_CONTEXT_MAP = {
        'python-ci-local': {
            'project_types': ['python'],
            'file_patterns': ['.py', 'requirements.txt'],
            'description': 'Python项目CI检查'
        },
        'docker-build-local': {
            'project_types': ['docker'],
            'file_patterns': ['Dockerfile'],
            'description': 'Docker镜像构建'
        },
        'security-scan-local': {
            'project_types': ['python', 'nodejs'],
            'file_patterns': ['.py', '.js', 'requirements.txt', 'package.json'],
            'description': '安全漏洞扫描'
        },
        'dependency-check': {
            'project_types': ['python', 'nodejs', 'rust', 'go'],
            'file_patterns': ['requirements.txt', 'package.json', 'Cargo.toml', 'go.mod'],
            'description': '依赖安全检查'
        },
        'code-coverage-report': {
            'project_types': ['python', 'nodejs'],
            'file_patterns': ['test_', '_test.py', '.spec.js', '.test.js'],
            'description': '代码覆盖率报告'
        },
        'performance-benchmark': {
            'project_types': ['python', 'nodejs', 'rust', 'go'],
            'file_patterns': ['.py', '.js', '.rs', '.go'],
            'description': '性能基准测试'
        },
        'backup-project': {
            'project_types': [],  # 所有项目类型
            'file_patterns': [],  # 所有文件
            'description': '项目备份'
        },
    }
    
    def __init__(self, project_path: str = None):
        self.project_root = Path(project_path) if project_path else resolve_project_root()
        self.workflows_dir = get_workflows_dir()
        self.last_check = {}
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
    
    def analyze_context(self) -> ContextAnalysis:
        """分析项目上下文"""
        analysis = ContextAnalysis()
        
        # 检测项目类型
        analysis.project_type = self._detect_project_type()
        
        # 获取Git状态
        analysis.git_status = self._get_git_status()
        
        # 检测文件变更
        analysis.files_changed = self._get_recent_changes()
        
        # 检测潜在问题
        analysis.issues = self._detect_issues()
        
        # 生成推荐
        analysis.recommendations = self._generate_context_recommendations(analysis)
        
        return analysis
    
    def _detect_project_type(self) -> Optional[str]:
        """检测项目类型"""
        for project_type, indicators in self.PROJECT_TYPE_INDICATORS.items():
            for indicator in indicators:
                if (self.project_root / indicator).exists():
                    return project_type
        return None
    
    def _get_git_status(self) -> Dict:
        """获取Git状态"""
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return {'error': 'Not a git repository'}
            
            changed_files = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    changed_files.append(line[3:])  # 去掉状态前缀
            
            return {
                'changed_files': changed_files,
                'has_changes': len(changed_files) > 0
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _get_recent_changes(self, minutes: int = 30) -> List[str]:
        """获取最近变更的文件"""
        try:
            result = subprocess.run(
                ['git', 'diff', '--name-only', f'--since="{minutes} minutes ago"'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
            return []
        except:
            return []
    
    def _detect_issues(self) -> List[str]:
        """检测潜在问题"""
        issues = []
        
        # 检查是否有未提交的变更
        git_status = self._get_git_status()
        if git_status.get('has_changes'):
            issues.append(f"有 {len(git_status['changed_files'])} 个未提交的文件")
        
        # 检查是否有日志文件过大
        log_files = list(self.project_root.glob('**/*.log'))
        for log_file in log_files[:3]:  # 只检查前3个
            try:
                size_mb = log_file.stat().st_size / (1024 * 1024)
                if size_mb > 10:  # 大于10MB
                    issues.append(f"日志文件过大: {log_file.name} ({size_mb:.1f}MB)")
            except:
                pass
        
        # 检查是否有临时文件
        temp_patterns = ['*.tmp', '*.temp', '*~', '.DS_Store', 'Thumbs.db']
        for pattern in temp_patterns:
            temp_files = list(self.project_root.glob(f'**/{pattern}'))
            if len(temp_files) > 5:
                issues.append(f"临时文件过多: 发现 {len(temp_files)} 个 {pattern} 文件")
                break
        
        return issues
    
    def _generate_context_recommendations(self, analysis: ContextAnalysis) -> List[str]:
        """基于上下文生成推荐"""
        recommendations = []
        
        if analysis.project_type:
            recommendations.append(f"📁 检测到项目类型: {analysis.project_type}")
        
        if analysis.git_status.get('has_changes'):
            changed_count = len(analysis.git_status['changed_files'])
            recommendations.append(f"📝 有 {changed_count} 个文件变更未提交")
            recommendations.append("💡 建议执行: git commit 或 代码审查工作流")
        
        if analysis.issues:
            recommendations.append(f"⚠️ 发现 {len(analysis.issues)} 个潜在问题")
        
        return recommendations
    
    def recommend_workflows(self) -> List[WorkflowRecommendation]:
        """推荐工作流"""
        context = self.analyze_context()
        recommendations = []
        
        for workflow_name, config in self.WORKFLOW_CONTEXT_MAP.items():
            # 检查工作流是否存在
            if workflow_name not in self.available_workflows:
                continue
            
            score = 0.0
            reasons = []
            
            # 项目类型匹配
            if not config['project_types'] or context.project_type in config['project_types']:
                score += 0.4
                if context.project_type:
                    reasons.append(f"项目类型匹配: {context.project_type}")
            
            # 文件变更匹配
            if context.files_changed:
                for file_path in context.files_changed:
                    for pattern in config['file_patterns']:
                        if pattern in file_path:
                            score += 0.2
                            reasons.append(f"文件变更匹配: {pattern}")
                            break
            
            # 问题检测匹配
            if context.issues and 'security' in workflow_name:
                score += 0.3
                reasons.append("安全问题检测")
            
            if score > 0.3:  # 阈值
                recommendations.append(WorkflowRecommendation(
                    workflow_name=workflow_name,
                    confidence=min(1.0, score),
                    reason="; ".join(reasons[:2]),  # 最多2个原因
                    triggers=self.available_workflows.get(workflow_name, {}).get('triggers', [])
                ))
        
        # 按置信度排序
        recommendations.sort(key=lambda x: x.confidence, reverse=True)
        return recommendations
    
    def get_monitoring_report(self) -> Dict[str, Any]:
        """获取监控报告"""
        context = self.analyze_context()
        workflow_recommendations = self.recommend_workflows()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'project_root': str(self.project_root),
            'project_type': context.project_type,
            'git_status': context.git_status,
            'files_changed_recently': context.files_changed[:10],  # 最多10个
            'issues': context.issues,
            'context_recommendations': context.recommendations,
            'workflow_recommendations': [
                {
                    'workflow': r.workflow_name,
                    'confidence': r.confidence,
                    'reason': r.reason,
                    'triggers': r.triggers
                }
                for r in workflow_recommendations[:5]  # 最多5个
            ]
        }
    
    def auto_execute_recommended(self, min_confidence: float = 0.7) -> Optional[str]:
        """自动执行高置信度推荐的工作流"""
        recommendations = self.recommend_workflows()
        
        for rec in recommendations:
            if rec.confidence >= min_confidence:
                workflow_path = self.workflows_dir / f"{rec.workflow_name}.yaml"
                if workflow_path.exists():
                    return f"🚀 自动执行工作流: {rec.workflow_name} (置信度: {rec.confidence:.0%})"
        
        return None


# 便捷函数
def get_context_report() -> Dict[str, Any]:
    """获取上下文报告"""
    monitor = IntelligentMonitor()
    return monitor.get_monitoring_report()


def recommend_for_current_context() -> List[Dict]:
    """为当前上下文推荐工作流"""
    monitor = IntelligentMonitor()
    recommendations = monitor.recommend_workflows()
    
    return [
        {
            'workflow': r.workflow_name,
            'confidence': r.confidence,
            'reason': r.reason
        }
        for r in recommendations
    ]
