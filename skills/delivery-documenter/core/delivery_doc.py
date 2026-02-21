"""
Delivery Doc v1.1 - 智能交付文档生成模块
改进: 
1. 使用 ExecutionTracker 数据填充实际内容
2. 根据任务类型生成针对性验证方法
3. 基于真实验证结果计算质量评分
4. 集成 Token 追踪功能
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from .paths import get_delivery_dir, ensure_dir
from .token_tracker import record_session_tokens, estimate_tokens, estimate_tokens_for_dict


@dataclass
class DeploymentStep:
    order: int
    action: str
    command: str = ""
    description: str = ""
    expected_result: str = ""
    troubleshooting: str = ""


@dataclass
class VerificationMethod:
    name: str
    description: str
    steps: List[str] = field(default_factory=list)
    expected_output: str = ""
    automated: bool = True
    passed: bool = None


@dataclass
class Limitation:
    category: str
    description: str
    impact: str = ""
    workaround: str = ""


@dataclass
class FutureTask:
    priority: str
    task: str
    estimated_effort: str = ""
    dependencies: List[str] = field(default_factory=list)


@dataclass
class DeliveryDocument:
    session_id: str
    task_description: str
    generated_at: str
    scenario_used: str = ""
    
    summary: str = ""
    files_created: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    
    deployment_steps: List[DeploymentStep] = field(default_factory=list)
    verification_methods: List[VerificationMethod] = field(default_factory=list)
    limitations: List[Limitation] = field(default_factory=list)
    future_tasks: List[FutureTask] = field(default_factory=list)
    
    key_findings: List[str] = field(default_factory=list)
    quality_score: float = 0.0
    
    test_summary: Dict[str, int] = field(default_factory=dict)
    command_summary: Dict[str, int] = field(default_factory=dict)
    errors: List[Dict[str, str]] = field(default_factory=list)


class SmartDeliveryGenerator:
    """
    智能交付文档生成器 v1.0
    
    改进:
    1. 从 ExecutionTracker 获取真实数据
    2. 根据任务类型生成针对性验证方法
    3. 包含真实验证结果
    """
    
    TASK_TYPE_VERIFICATION_MAP = {
        "skill_development": [
            {"name": "Skill文件验证", "steps": ["检查 SKILL.md 存在", "验证 skill.json 格式正确"], "automated": True},
            {"name": "触发词测试", "steps": ["测试触发词响应", "验证 Skill 正确加载"], "automated": False},
            {"name": "依赖检查", "steps": ["检查 requirements.txt", "验证依赖安装"], "automated": True},
        ],
        "api_development": [
            {"name": "API启动验证", "steps": ["启动 API 服务", "检查健康检查端点"], "automated": True},
            {"name": "接口测试", "steps": ["测试主要 API 端点", "验证响应格式正确"], "automated": True},
            {"name": "文档生成", "steps": ["检查 API 文档生成", "验证 Swagger/OpenAPI"], "automated": True},
        ],
        "frontend_development": [
            {"name": "构建验证", "steps": ["运行 npm run build", "检查无编译错误"], "automated": True},
            {"name": "类型检查", "steps": ["运行 tsc --noEmit", "检查无类型错误"], "automated": True},
            {"name": "页面渲染", "steps": ["启动开发服务器", "验证页面正常渲染"], "automated": False},
        ],
        "bug_fix": [
            {"name": "问题复现", "steps": ["确认原始问题已修复", "验证修复不影响其他功能"], "automated": False},
            {"name": "回归测试", "steps": ["运行相关测试用例", "检查无新增失败"], "automated": True},
            {"name": "代码审查", "steps": ["检查修复代码质量", "确认无引入新问题"], "automated": False},
        ],
        "refactoring": [
            {"name": "功能验证", "steps": ["运行完整测试套件", "验证功能未受影响"], "automated": True},
            {"name": "性能检查", "steps": ["对比重构前后性能", "确认无性能退化"], "automated": False},
            {"name": "代码质量", "steps": ["运行 lint 检查", "检查代码复杂度"], "automated": True},
        ],
        "general": [
            {"name": "功能验证", "steps": ["运行主程序或测试脚本", "检查输出是否符合预期", "验证关键功能点"], "automated": True},
            {"name": "质量验证", "steps": ["运行代码检查工具", "检查是否有警告或错误", "确认代码风格一致"], "automated": True},
        ]
    }
    
    DEPLOYMENT_TEMPLATES = {
        'python': [
            DeploymentStep(1, "安装依赖", "pip install -r requirements.txt", "安装项目所需的所有Python包"),
            DeploymentStep(2, "配置环境变量", "cp .env.example .env", "复制环境变量模板并配置"),
            DeploymentStep(3, "运行应用", "python main.py", "启动应用程序"),
        ],
        'web': [
            DeploymentStep(1, "安装依赖", "npm install", "安装Node.js依赖"),
            DeploymentStep(2, "构建项目", "npm run build", "构建生产版本"),
            DeploymentStep(3, "启动服务", "npm start", "启动Web服务器"),
        ],
        'skill': [
            DeploymentStep(1, "复制Skill目录", "cp -r skill_name .trae/skills/", "将Skill复制到.trae/skills目录"),
            DeploymentStep(2, "验证安装", "检查SKILL.md是否存在", "确认Skill正确安装"),
            DeploymentStep(3, "测试Skill", "使用触发词测试", "验证Skill功能正常"),
        ],
        'api': [
            DeploymentStep(1, "安装依赖", "pip install -r requirements.txt", "安装API所需依赖"),
            DeploymentStep(2, "配置数据库", "python init_db.py", "初始化数据库"),
            DeploymentStep(3, "启动API服务", "uvicorn main:app --reload", "启动API服务器"),
            DeploymentStep(4, "验证API", "curl http://localhost:8000/health", "检查API健康状态"),
        ],
        'general': [
            DeploymentStep(1, "检查环境", "确认运行环境满足要求", "验证系统配置"),
            DeploymentStep(2, "执行程序", "按照具体说明执行", "运行主要功能"),
            DeploymentStep(3, "验证结果", "检查输出是否符合预期", "确认功能正常"),
        ]
    }
    
    def __init__(self, output_dir: str = None):
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = get_delivery_dir()
        
        ensure_dir(self.output_dir)
    
    def generate(self, session_id: str, task_description: str, 
                 execution_result: Dict[str, Any] = None,
                 quality_report: Dict[str, Any] = None,
                 task_type: str = "general") -> DeliveryDocument:
        """
        生成交付文档
        
        改进:
        1. 使用 execution_result 填充真实数据
        2. 根据 task_type 生成针对性验证方法
        3. 包含 quality_report 的真实验证结果
        4. Token 追踪记录
        """
        input_text = f"session:{session_id} task:{task_description[:100]}"
        
        doc = DeliveryDocument(
            session_id=session_id,
            task_description=task_description,
            generated_at=datetime.now().isoformat()
        )
        
        if execution_result:
            doc.scenario_used = execution_result.get('scenario', 'unknown')
            doc.files_created = execution_result.get('files_created', [])
            doc.files_modified = execution_result.get('files_modified', [])
            doc.key_findings = execution_result.get('key_findings', [])
            doc.test_summary = execution_result.get('test_summary', {})
            doc.command_summary = execution_result.get('command_summary', {})
            doc.errors = execution_result.get('errors', [])
            doc.summary = self._generate_smart_summary(execution_result, task_description)
        else:
            doc.summary = f"任务: {task_description}"
        
        if quality_report:
            doc.quality_score = quality_report.get('overall_score', 0)
        
        doc.deployment_steps = self._generate_deployment_steps(execution_result, task_type)
        doc.verification_methods = self._generate_smart_verification_methods(
            task_type, execution_result, quality_report
        )
        doc.limitations = self._generate_limitations(execution_result)
        doc.future_tasks = self._generate_future_tasks(task_description, execution_result)
        
        self._save_document(doc)
        
        output_text = f"delivery_doc:{session_id} files:{len(doc.files_created)+len(doc.files_modified)}"
        record_session_tokens(
            session_id, 
            input_text, 
            output_text, 
            "delivery_generation"
        )
        
        return doc
    
    def _generate_smart_summary(self, execution_result: Dict, task_description: str) -> str:
        """生成智能摘要 - 基于实际执行结果"""
        parts = []
        
        created = execution_result.get('files_created', [])
        modified = execution_result.get('files_modified', [])
        test_summary = execution_result.get('test_summary', {})
        command_summary = execution_result.get('command_summary', {})
        key_findings = execution_result.get('key_findings', [])
        
        if created:
            parts.append(f"创建了 {len(created)} 个文件")
            if len(created) <= 5:
                parts[-1] += f" ({', '.join([Path(f).name for f in created])})"
        
        if modified:
            parts.append(f"修改了 {len(modified)} 个文件")
            if len(modified) <= 5:
                parts[-1] += f" ({', '.join([Path(f).name for f in modified])})"
        
        if test_summary and test_summary.get('total', 0) > 0:
            passed = test_summary.get('passed', 0)
            total = test_summary.get('total', 0)
            parts.append(f"运行了 {total} 个测试 ({passed} 通过)")
        
        if command_summary and command_summary.get('total', 0) > 0:
            successful = command_summary.get('successful', 0)
            total = command_summary.get('total', 0)
            parts.append(f"执行了 {total} 个命令 ({successful} 成功)")
        
        if key_findings:
            parts.append(f"发现 {len(key_findings)} 个关键问题")
        
        if parts:
            return "，".join(parts) + "。"
        
        return f"已完成任务: {task_description[:100]}..."
    
    def _generate_deployment_steps(self, execution_result: Dict, task_type: str) -> List[DeploymentStep]:
        """生成部署步骤 - 根据实际文件和项目类型"""
        if not execution_result:
            return self.DEPLOYMENT_TEMPLATES.get(task_type, self.DEPLOYMENT_TEMPLATES['general'])
        
        detected_type = self._detect_project_type(execution_result, task_type)
        base_steps = self.DEPLOYMENT_TEMPLATES.get(detected_type, self.DEPLOYMENT_TEMPLATES['general'])
        
        files_created = execution_result.get('files_created', [])
        if files_created:
            custom_steps = []
            for i, f in enumerate(files_created[:3], 1):
                file_name = Path(f).name
                custom_steps.append(DeploymentStep(
                    order=i,
                    action=f"验证 {file_name}",
                    command=f"检查 {f} 存在",
                    description=f"确认文件 {file_name} 已正确创建"
                ))
            if len(base_steps) > 0:
                return custom_steps + base_steps[len(custom_steps):]
        
        return base_steps
    
    def _detect_project_type(self, execution_result: Dict, task_type: str) -> str:
        """检测项目类型"""
        files = execution_result.get('files_created', []) + execution_result.get('files_modified', [])
        file_str = ' '.join(files).lower()
        
        if '.trae/skills' in file_str or 'skill' in file_str or task_type == 'skill_development':
            return 'skill'
        if 'package.json' in file_str or 'npm' in file_str or task_type == 'frontend_development':
            return 'web'
        if 'api' in file_str or 'fastapi' in file_str or 'flask' in file_str or task_type == 'api_development':
            return 'api'
        if '.py' in file_str or 'requirements' in file_str:
            return 'python'
        
        return 'general'
    
    def _generate_smart_verification_methods(self, task_type: str, 
                                              execution_result: Dict,
                                              quality_report: Dict) -> List[VerificationMethod]:
        """生成智能验证方法 - 根据任务类型和实际结果"""
        methods = []
        
        files_created = execution_result.get('files_created', []) if execution_result else []
        files_modified = execution_result.get('files_modified', []) if execution_result else []
        all_files = files_created + files_modified
        
        if all_files:
            steps = [f"检查文件 {Path(f).name} 是否存在" for f in all_files[:5]]
            if len(all_files) > 5:
                steps.append(f"... 以及其他 {len(all_files) - 5} 个文件")
            
            file_verification = VerificationMethod(
                name="文件验证",
                description="验证创建和修改的文件是否正确",
                steps=steps,
                expected_output="所有文件已正确创建/修改",
                automated=True
            )
            methods.append(file_verification)
        
        task_methods = self.TASK_TYPE_VERIFICATION_MAP.get(task_type, 
                         self.TASK_TYPE_VERIFICATION_MAP['general'])
        
        for method_template in task_methods[:3]:
            method = VerificationMethod(
                name=method_template['name'],
                description=method_template.get('description', ''),
                steps=method_template['steps'],
                expected_output=method_template.get('expected_output', '验证通过'),
                automated=method_template.get('automated', True)
            )
            methods.append(method)
        
        if quality_report and quality_report.get('real_validation_summary'):
            real_summary = quality_report['real_validation_summary']
            real_method = VerificationMethod(
                name="真实验证结果",
                description="已运行的真实验证检查",
                steps=[
                    f"Lint检查: {'通过' if real_summary.get('lint_passed') else '未通过'}",
                    f"类型检查: {'通过' if real_summary.get('typecheck_passed') else '未通过'}",
                    f"测试运行: {'通过' if real_summary.get('tests_passed') else '未通过'}"
                ],
                expected_output=f"通过率: {real_summary.get('pass_rate', 0):.0%}",
                automated=True,
                passed=real_summary.get('pass_rate', 0) >= 0.7
            )
            methods.append(real_method)
        
        return methods
    
    def _generate_limitations(self, execution_result: Dict) -> List[Limitation]:
        """生成限制说明 - 基于实际发现"""
        limitations = []
        
        limitations.append(Limitation(
            category="环境限制",
            description="需要Python 3.8+环境",
            impact="低版本Python可能无法运行",
            workaround="升级Python版本或使用虚拟环境"
        ))
        
        if execution_result:
            errors = execution_result.get('errors', [])
            if errors:
                limitations.append(Limitation(
                    category="已知问题",
                    description=f"执行过程中发现 {len(errors)} 个问题",
                    impact="部分功能可能受影响",
                    workaround="查看错误详情并修复"
                ))
            
            test_summary = execution_result.get('test_summary', {})
            if test_summary.get('failed', 0) > 0:
                limitations.append(Limitation(
                    category="测试限制",
                    description=f"{test_summary['failed']} 个测试未通过",
                    impact="部分功能可能存在问题",
                    workaround="检查失败测试并修复"
                ))
        
        return limitations
    
    def _generate_future_tasks(self, task_description: str, execution_result: Dict) -> List[FutureTask]:
        """生成后续建议任务 - 基于实际发现"""
        tasks = []
        
        if execution_result:
            test_summary = execution_result.get('test_summary', {})
            if test_summary.get('total', 0) == 0:
                tasks.append(FutureTask(
                    priority="high",
                    task="添加单元测试",
                    estimated_effort="2-4小时",
                    dependencies=["确定测试框架", "编写测试用例"]
                ))
            
            errors = execution_result.get('errors', [])
            if errors:
                tasks.append(FutureTask(
                    priority="high",
                    task="修复已知错误",
                    estimated_effort="1-2小时",
                    dependencies=[]
                ))
            
            files_created = execution_result.get('files_created', [])
            if files_created:
                tasks.append(FutureTask(
                    priority="medium",
                    task="完善文档",
                    estimated_effort="1小时",
                    dependencies=[]
                ))
        
        if not tasks:
            tasks = [
                FutureTask(
                    priority="medium",
                    task="添加单元测试",
                    estimated_effort="1-2小时",
                    dependencies=["确定测试框架"]
                ),
                FutureTask(
                    priority="low",
                    task="优化性能",
                    estimated_effort="2-4小时",
                    dependencies=["性能测试"]
                )
            ]
        
        return tasks
    
    def _save_document(self, doc: DeliveryDocument):
        """保存交付文档"""
        md_path = self.output_dir / f"{doc.session_id}_delivery.md"
        json_path = self.output_dir / f"{doc.session_id}_delivery.json"
        
        md_content = self._render_markdown(doc)
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        json_content = self._render_json(doc)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_content, f, ensure_ascii=False, indent=2)
    
    def _render_markdown(self, doc: DeliveryDocument) -> str:
        """渲染Markdown格式"""
        lines = [
            f"# 📦 交付文档",
            f"",
            f"**会话ID**: {doc.session_id}",
            f"**生成时间**: {doc.generated_at}",
            f"**使用场景**: {doc.scenario_used}",
            f"",
            f"## 📋 任务摘要",
            f"",
            doc.summary,
            f"",
        ]
        
        if doc.files_created:
            lines.extend([
                f"### 📁 创建的文件 ({len(doc.files_created)})",
                f"",
            ])
            for f in doc.files_created:
                lines.append(f"- `{f}`")
            lines.append("")
        
        if doc.files_modified:
            lines.extend([
                f"### ✏️ 修改的文件 ({len(doc.files_modified)})",
                f"",
            ])
            for f in doc.files_modified:
                lines.append(f"- `{f}`")
            lines.append("")
        
        lines.extend([
            f"## 🚀 部署说明",
            f"",
        ])
        for step in doc.deployment_steps:
            lines.extend([
                f"### 步骤 {step.order}: {step.action}",
                f"",
                f"{step.description}",
                f"",
            ])
            if step.command:
                lines.extend([
                    f"```bash",
                    f"{step.command}",
                    f"```",
                    f"",
                ])
        
        lines.extend([
            f"## ✅ 验证方法",
            f"",
        ])
        for method in doc.verification_methods:
            status = "✅" if method.passed is True else ("❌" if method.passed is False else "⏳")
            auto_tag = " [自动]" if method.automated else " [手动]"
            lines.extend([
                f"### {status} {method.name}{auto_tag}",
                f"",
                f"{method.description}",
                f"",
            ])
            for i, step in enumerate(method.steps, 1):
                lines.append(f"{i}. {step}")
            lines.extend([
                f"",
                f"**预期输出**: {method.expected_output}",
                f"",
            ])
        
        lines.extend([
            f"## ⚠️ 限制说明",
            f"",
        ])
        for limit in doc.limitations:
            lines.extend([
                f"### {limit.category}",
                f"",
                f"- **描述**: {limit.description}",
                f"- **影响**: {limit.impact}",
                f"- **解决方案**: {limit.workaround}",
                f"",
            ])
        
        lines.extend([
            f"## 📝 后续建议",
            f"",
            f"| 优先级 | 任务 | 预估工时 | 依赖项 |",
            f"|--------|------|----------|--------|",
        ])
        for task in doc.future_tasks:
            deps = ", ".join(task.dependencies) if task.dependencies else "-"
            priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(task.priority, "")
            lines.append(f"| {priority_emoji} {task.priority} | {task.task} | {task.estimated_effort} | {deps} |")
        
        if doc.key_findings:
            lines.extend([
                f"",
                f"## 🔍 关键发现",
                f"",
            ])
            for finding in doc.key_findings:
                lines.append(f"- {finding}")
        
        if doc.test_summary and doc.test_summary.get('total', 0) > 0:
            lines.extend([
                f"",
                f"## 🧪 测试摘要",
                f"",
                f"- **总测试数**: {doc.test_summary.get('total', 0)}",
                f"- **通过**: {doc.test_summary.get('passed', 0)}",
                f"- **失败**: {doc.test_summary.get('failed', 0)}",
            ])
        
        if doc.errors:
            lines.extend([
                f"",
                f"## ⚠️ 错误记录 ({len(doc.errors)})",
                f"",
            ])
            for error in doc.errors[:5]:
                lines.append(f"- **{error.get('type', 'Unknown')}**: {error.get('message', '')}")
        
        if doc.quality_score > 0:
            lines.extend([
                f"",
                f"## 📊 质量评分",
                f"",
                f"**总分**: {doc.quality_score:.0%}",
                f"",
            ])
        
        return "\n".join(lines)
    
    def _render_json(self, doc: DeliveryDocument) -> Dict:
        """渲染JSON格式"""
        return {
            "session_id": doc.session_id,
            "task_description": doc.task_description,
            "generated_at": doc.generated_at,
            "scenario_used": doc.scenario_used,
            "summary": doc.summary,
            "files_created": doc.files_created,
            "files_modified": doc.files_modified,
            "deployment_steps": [
                {
                    "order": s.order,
                    "action": s.action,
                    "command": s.command,
                    "description": s.description
                }
                for s in doc.deployment_steps
            ],
            "verification_methods": [
                {
                    "name": m.name,
                    "description": m.description,
                    "steps": m.steps,
                    "expected_output": m.expected_output,
                    "automated": m.automated,
                    "passed": m.passed
                }
                for m in doc.verification_methods
            ],
            "limitations": [
                {
                    "category": l.category,
                    "description": l.description,
                    "impact": l.impact,
                    "workaround": l.workaround
                }
                for l in doc.limitations
            ],
            "future_tasks": [
                {
                    "priority": t.priority,
                    "task": t.task,
                    "estimated_effort": t.estimated_effort,
                    "dependencies": t.dependencies
                }
                for t in doc.future_tasks
            ],
            "key_findings": doc.key_findings,
            "quality_score": doc.quality_score,
            "test_summary": doc.test_summary,
            "command_summary": doc.command_summary,
            "errors": doc.errors
        }
    
    def get_summary(self, doc: DeliveryDocument) -> str:
        """获取交付文档摘要"""
        lines = [
            f"📦 交付文档摘要 - {doc.session_id}",
            f"{'='*50}",
            f"",
            doc.summary,
            f"",
        ]
        
        if doc.files_created:
            lines.append(f"📁 创建文件: {len(doc.files_created)} 个")
        if doc.files_modified:
            lines.append(f"📝 修改文件: {len(doc.files_modified)} 个")
        
        lines.extend([
            f"",
            f"🚀 部署步骤: {len(doc.deployment_steps)} 步",
            f"✅ 验证方法: {len(doc.verification_methods)} 种",
            f"⚠️ 限制说明: {len(doc.limitations)} 项",
            f"📝 后续建议: {len(doc.future_tasks)} 条",
        ])
        
        if doc.quality_score > 0:
            lines.append(f"")
            lines.append(f"📊 质量评分: {doc.quality_score:.0%}")
        
        return "\n".join(lines)


DeliveryDocGenerator = SmartDeliveryGenerator
