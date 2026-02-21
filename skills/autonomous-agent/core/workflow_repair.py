"""
Workflow Repair Engine v1.0 - 自动维修工作流引擎
功能：
1. 组件扫描器 - 检测所有Python模块、技能、工作流
2. 调用关系验证器 - 检查组件间依赖是否一致
3. 项目规则同步器 - 自动更新project_rules.md
4. 维修报告生成器 - 生成详细维修报告
"""

import ast
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

from .paths import (
    resolve_project_root, get_trae_dir, get_skills_dir, 
    get_workflows_dir, get_memory_dir, ensure_dir
)


class ComponentType(Enum):
    PYTHON_MODULE = "python_module"
    SKILL = "skill"
    WORKFLOW = "workflow"
    RULES_FILE = "rules_file"
    CONFIG_FILE = "config_file"
    WORKER = "worker"


class IssueSeverity(Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


@dataclass
class Component:
    name: str
    component_type: ComponentType
    path: str
    imports: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Issue:
    issue_type: str
    severity: IssueSeverity
    component: str
    description: str
    suggestion: str
    auto_fixable: bool = False
    fixed: bool = False


@dataclass
class RepairReport:
    scan_time: str
    components_scanned: int
    issues_found: List[Issue]
    issues_fixed: List[Issue]
    new_components: List[Component]
    rules_updated: bool
    summary: str


class ComponentScanner:
    """
    组件扫描器 - 扫描自动化工作流的所有组件
    """
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else resolve_project_root()
        self.trae_dir = get_trae_dir()
        self.skills_dir = get_skills_dir()
        self.workflows_dir = get_workflows_dir()
        
        self.components: Dict[str, Component] = {}
        self.import_graph: Dict[str, Set[str]] = {}
    
    def scan_all(self) -> Dict[str, Component]:
        """扫描所有组件"""
        self._scan_autonomous_agent()
        self._scan_skills()
        self._scan_workflows()
        self._scan_rules()
        self._scan_configs()
        self._build_import_graph()
        return self.components
    
    def _scan_autonomous_agent(self):
        """扫描 autonomous-agent 核心模块"""
        agent_dir = self.skills_dir / 'autonomous-agent'
        if not agent_dir.exists():
            return
        
        agent_py = agent_dir / 'agent.py'
        if agent_py.exists():
            self.components['agent.py'] = self._parse_python_file(
                agent_py, 
                ComponentType.PYTHON_MODULE,
                'autonomous-agent入口'
            )
        
        core_dir = agent_dir / 'core'
        if core_dir.exists():
            for py_file in core_dir.glob('*.py'):
                if py_file.name == '__init__.py':
                    continue
                comp = self._parse_python_file(
                    py_file,
                    ComponentType.PYTHON_MODULE,
                    f'核心模块: {py_file.stem}'
                )
                self.components[f'core/{py_file.name}'] = comp
        
        workers_dir = core_dir / 'workers'
        if workers_dir.exists():
            for py_file in workers_dir.glob('*.py'):
                if py_file.name == '__init__.py':
                    continue
                comp = self._parse_python_file(
                    py_file,
                    ComponentType.WORKER,
                    f'Worker: {py_file.stem}'
                )
                self.components[f'core/workers/{py_file.name}'] = comp
    
    def _scan_skills(self):
        """扫描所有技能"""
        if not self.skills_dir.exists():
            return
        
        for skill_dir in self.skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            
            skill_yaml = skill_dir / 'skill.yaml'
            skill_md = skill_dir / 'SKILL.md'
            
            metadata = {}
            if skill_yaml.exists():
                try:
                    import yaml
                    with open(skill_yaml, 'r', encoding='utf-8') as f:
                        metadata = yaml.safe_load(f) or {}
                except:
                    pass
            
            py_files = list(skill_dir.glob('*.py'))
            exports = []
            for py_file in py_files:
                comp = self._parse_python_file(py_file, ComponentType.SKILL, f'技能: {skill_dir.name}')
                exports.extend(comp.exports)
            
            self.components[f'skills/{skill_dir.name}'] = Component(
                name=skill_dir.name,
                component_type=ComponentType.SKILL,
                path=str(skill_dir.relative_to(self.project_root)),
                exports=exports,
                metadata=metadata
            )
    
    def _scan_workflows(self):
        """扫描所有工作流"""
        if not self.workflows_dir.exists():
            return
        
        for workflow_file in self.workflows_dir.glob('*.yaml'):
            metadata = {}
            try:
                import yaml
                with open(workflow_file, 'r', encoding='utf-8') as f:
                    metadata = yaml.safe_load(f) or {}
            except:
                pass
            
            self.components[f'workflows/{workflow_file.name}'] = Component(
                name=workflow_file.stem,
                component_type=ComponentType.WORKFLOW,
                path=str(workflow_file.relative_to(self.project_root)),
                metadata=metadata
            )
        
        for py_file in self.workflows_dir.glob('*.py'):
            comp = self._parse_python_file(py_file, ComponentType.WORKFLOW, f'工作流脚本: {py_file.stem}')
            self.components[f'workflows/{py_file.name}'] = comp
    
    def _scan_rules(self):
        """扫描项目规则文件"""
        rules_file = self.trae_dir / 'rules' / 'project_rules.md'
        if rules_file.exists():
            with open(rules_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            version_match = re.search(r'v(\d+\.\d+)', content)
            version = version_match.group(1) if version_match else "unknown"
            
            self.components['rules/project_rules.md'] = Component(
                name='project_rules.md',
                component_type=ComponentType.RULES_FILE,
                path=str(rules_file.relative_to(self.project_root)),
                metadata={'version': version, 'size': len(content)}
            )
    
    def _scan_configs(self):
        """扫描配置文件"""
        config_files = [
            self.trae_dir / 'config' / 'skill-registry.json',
            self.trae_dir / 'swarm' / 'agent_registry.json',
            self.trae_dir / 'memory' / 'index.json',
        ]
        
        for config_file in config_files:
            if config_file.exists():
                self.components[f'config/{config_file.name}'] = Component(
                    name=config_file.name,
                    component_type=ComponentType.CONFIG_FILE,
                    path=str(config_file.relative_to(self.project_root))
                )
    
    def _parse_python_file(self, file_path: Path, comp_type: ComponentType, description: str = "") -> Component:
        """解析Python文件，提取导入、类、函数"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        imports.append(f"{module}.{alias.name}" if module else alias.name)
            
            classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            
            local_imports = [i for i in imports if i.startswith('core.') or i.startswith('.')]
            
            return Component(
                name=file_path.stem,
                component_type=comp_type,
                path=str(file_path.relative_to(self.project_root)),
                imports=imports,
                exports=classes + [f for f in functions if not f.startswith('_')],
                classes=classes,
                functions=functions,
                dependencies=local_imports,
                metadata={'description': description}
            )
        except Exception as e:
            return Component(
                name=file_path.stem,
                component_type=comp_type,
                path=str(file_path.relative_to(self.project_root)),
                metadata={'error': str(e)}
            )
    
    def _build_import_graph(self):
        """构建导入依赖图"""
        for name, comp in self.components.items():
            self.import_graph[name] = set()
            for imp in comp.dependencies:
                for other_name, other_comp in self.components.items():
                    if other_comp.name in imp or imp in other_comp.name:
                        self.import_graph[name].add(other_name)
    
    def detect_new_components(self, known_components: List[str] = None) -> List[Component]:
        """检测新增组件"""
        if known_components is None:
            known_components = self._load_known_components()
        
        new_components = []
        for name, comp in self.components.items():
            if name not in known_components:
                new_components.append(comp)
        
        return new_components
    
    def _load_known_components(self) -> List[str]:
        """加载已知组件列表"""
        known_file = get_memory_dir() / 'known_components.json'
        if known_file.exists():
            try:
                with open(known_file, 'r', encoding='utf-8') as f:
                    return json.load(f).get('components', [])
            except:
                pass
        return list(self.components.keys())
    
    def save_known_components(self):
        """保存已知组件列表"""
        known_file = get_memory_dir() / 'known_components.json'
        ensure_dir(known_file.parent)
        
        with open(known_file, 'w', encoding='utf-8') as f:
            json.dump({
                'updated_at': datetime.now().isoformat(),
                'components': list(self.components.keys())
            }, f, ensure_ascii=False, indent=2)


class DependencyValidator:
    """
    调用关系验证器 - 检查组件间依赖是否一致
    """
    
    def __init__(self, components: Dict[str, Component], import_graph: Dict[str, Set[str]], project_root: str = None):
        self.components = components
        self.import_graph = import_graph
        self.project_root = Path(project_root) if project_root else resolve_project_root()
        self.issues: List[Issue] = []
    
    def validate_all(self) -> List[Issue]:
        """执行所有验证"""
        self.issues = []
        self._validate_imports()
        self._validate_exports()
        self._validate_agent_entry()
        self._validate_init_exports()
        self._validate_skill_configs()
        return self.issues
    
    def _validate_imports(self):
        """验证导入是否有效"""
        for name, comp in self.components.items():
            if comp.component_type != ComponentType.PYTHON_MODULE:
                continue
            
            for imp in comp.dependencies:
                if imp.startswith('core.'):
                    module_name = imp.replace('core.', '')
                    found = any(
                        f'core/{module_name}.py' in other_name or 
                        f'core/{module_name.split(".")[0]}.py' in other_name
                        for other_name in self.components
                    )
                    if not found:
                        self.issues.append(Issue(
                            issue_type="missing_import",
                            severity=IssueSeverity.WARNING,
                            component=name,
                            description=f"导入 '{imp}' 可能找不到对应模块",
                            suggestion=f"检查模块路径是否正确，或创建缺失的模块",
                            auto_fixable=False
                        ))
    
    def _validate_exports(self):
        """验证导出是否被使用"""
        all_imports = set()
        for comp in self.components.values():
            all_imports.update(comp.imports)
        
        for name, comp in self.components.items():
            for export in comp.exports:
                if export.startswith('_'):
                    continue
                
                used = any(export in imp for imp in all_imports)
                if not used and comp.component_type == ComponentType.PYTHON_MODULE:
                    self.issues.append(Issue(
                        issue_type="unused_export",
                        severity=IssueSeverity.INFO,
                        component=name,
                        description=f"导出 '{export}' 可能未被使用",
                        suggestion=f"考虑是否需要保留此导出",
                        auto_fixable=False
                    ))
    
    def _validate_agent_entry(self):
        """验证agent.py入口是否正确导入所有模块"""
        agent_comp = self.components.get('agent.py')
        if not agent_comp:
            self.issues.append(Issue(
                issue_type="missing_entry",
                severity=IssueSeverity.CRITICAL,
                component="agent.py",
                description="找不到agent.py入口文件",
                suggestion="确保agent.py存在于autonomous-agent目录",
                auto_fixable=False
            ))
            return
        
        required_imports = [
            'IntelligentAssistant', 'SwarmOrchestrator', 'WorkflowRunner',
            'ReflexionCore', 'MemoryManager', 'TokenTracker', 'QualityGate',
            'ScenarioSelector', 'SkillDiscovery', 'DeliveryDocGenerator',
            'ExecutionTracker'
        ]
        
        for req in required_imports:
            found = any(req in imp for imp in agent_comp.imports)
            if not found:
                self.issues.append(Issue(
                    issue_type="missing_required_import",
                    severity=IssueSeverity.WARNING,
                    component="agent.py",
                    description=f"缺少必要导入: {req}",
                    suggestion=f"在agent.py中添加 from core.xxx import {req}",
                    auto_fixable=True
                ))
    
    def _validate_init_exports(self):
        """验证__init__.py是否正确导出"""
        init_path = get_skills_dir() / 'autonomous-agent' / 'core' / '__init__.py'
        if not init_path.exists():
            self.issues.append(Issue(
                issue_type="missing_init",
                severity=IssueSeverity.WARNING,
                component="core/__init__.py",
                description="缺少__init__.py文件",
                suggestion="创建__init__.py并导出所有公共接口",
                auto_fixable=True
            ))
            return
        
        try:
            with open(init_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            init_comp = self.components.get('core/__init__.py')
            if init_comp:
                __all__ = init_comp.exports
                for comp_name, comp in self.components.items():
                    if comp_name.startswith('core/') and comp_name != 'core/__init__.py':
                        for cls in comp.classes:
                            if cls not in __all__ and not cls.startswith('_'):
                                self.issues.append(Issue(
                                    issue_type="missing_init_export",
                                    severity=IssueSeverity.INFO,
                                    component="core/__init__.py",
                                    description=f"类 '{cls}' 未在__init__.py中导出",
                                    suggestion=f"在__all__中添加 '{cls}'",
                                    auto_fixable=True
                                ))
        except:
            pass
    
    def _validate_skill_configs(self):
        """验证技能配置"""
        for name, comp in self.components.items():
            if comp.component_type != ComponentType.SKILL:
                continue
            
            skill_dir = Path(comp.path)
            skill_yaml = self.project_root / skill_dir / 'skill.yaml'
            skill_md = self.project_root / skill_dir / 'SKILL.md'
            
            if not skill_yaml.exists():
                self.issues.append(Issue(
                    issue_type="missing_skill_config",
                    severity=IssueSeverity.WARNING,
                    component=name,
                    description="缺少skill.yaml配置文件",
                    suggestion=f"在 {skill_dir} 中创建skill.yaml",
                    auto_fixable=False
                ))
            
            if not skill_md.exists():
                self.issues.append(Issue(
                    issue_type="missing_skill_doc",
                    severity=IssueSeverity.INFO,
                    component=name,
                    description="缺少SKILL.md文档文件",
                    suggestion=f"在 {skill_dir} 中创建SKILL.md",
                    auto_fixable=False
                ))


class RulesSynchronizer:
    """
    项目规则同步器 - 自动更新project_rules.md
    """
    
    RULES_TEMPLATE = '''# Agent 执行核心指令 v{version} (真实验证版)

---

## 🎯 快速理解：什么是自动化工作流

**一句话定义**：
> 自动化工作流 = 触发词 → 自主执行 → 闭环交付

**核心价值**：
- 用户只需说一句话，Agent 自动完成从需求到交付的全流程
- 无需人工干预，自动规划、执行、验证、交付
- 错误自动修复，成功自动沉淀为可复用记忆
- **真实验证**：运行实际 lint/test/typecheck，而非形式主义检查

**执行本质**：
```
用户输入触发词 → Agent 立即调用 autonomous-agent 技能 →
自动解析任务 → 自动选择策略 → 自动执行 → 真实验证 → 自动交付
```

---

## 📁 项目架构全景图

```
.trae/
├── 🎯 核心引擎
│   └── autonomous-agent/        # 自主执行总调度器 v{version}
│       └── agent.py             # 【入口文件】一切从这里开始
│       └── core/
{core_modules}│
├── 🔧 技能系统 (.trae/skills/)
{skills_list}│
├── 📋 工作流系统
│   ├── workflow_manager_v2.py   # 自验证闭环工作流管理器
│   ├── smart_router.py          # 智能路由系统
│   └── *.yaml                   # {workflow_count}+ 预定义工作流模板
│
├── 🧠 记忆系统
│   ├── memory/                  # 会话记忆存储
│   │   ├── token_usage.json     # Token使用记录
│   │   ├── execution_tracks/    # 执行追踪记录 🆕
│   │   └── quality/             # 质量检查报告 🆕
│   └── knowledge/               # 知识库沉淀
│
├── 📦 交付系统
│   └── delivery/                # 交付文档存储
│       └── *_delivery.json/md   # 交付文档
│
└── 🐝 蜂群系统
    └── swarm/                   # 多智能体编排
```

**关键路径**：
- **入口**：`./.trae/skills/autonomous-agent/agent.py`
- **记忆**：`./自动化工作流组件库/memory/`
- **工作流**：`./自动化工作流组件库/workflows/`
- **交付**：`./自动化工作流组件库/delivery/`
- **执行追踪**：`./自动化工作流组件库/memory/execution_tracks/`

---

## 🚨🚨🚨 超级强制规则 (最高优先级)

### 1. ⚡ 强制触发协议 (MANDATORY TRIGGER PROTOCOL)

**检测到以下任意触发词时，必须立即执行 autonomous-agent 技能，无例外：**

| 触发词 | 立即动作 | 绝对禁止 |
|:---:|:---|:---|
| **开始** | 调用 `autonomous-agent` 技能 | 闲聊、解释、计划 |
| **继续** | 调用 `autonomous-agent` 技能 | 等待更多上下文 |
| **自主执行** | 调用 `autonomous-agent` 技能 | 询问确认 |
| **自动执行** | 调用 `autonomous-agent` 技能 | 任何延迟 |
| **自动规划** | 调用 `autonomous-agent` 技能 | 选择不执行 |
| **自动修复** | 调用 `autonomous-agent` 技能 | 中途停止 |
| **autonomous** | 调用 `autonomous-agent` 技能 | - |
| **蜂群** | 调用 `autonomous-agent` 技能 | - |
| **swarm** | 调用 `autonomous-agent` 技能 | - |

**执行公式**：
```
检测触发词 → 立即调用 Skill 工具 → 执行 agent.py → 完成所有检查点 → 交付
```

**违规判定**：
- 检测到触发词后未立即调用 Skill = **执行失败**
- 调用 Skill 后停止执行 = **执行失败**
- 未完成所有检查点 = **执行失败**

### 2. 🔄 强制连续执行协议 (MANDATORY CONTINUOUS EXECUTION)

**获得执行计划后必须遵守：**

| 规则 | 描述 | 违规后果 |
|:---:|:---|:---|
| **禁止中途停止** | 必须一口气执行完所有步骤 | 执行失败 |
| **禁止伪并行** | Swarm 模式在一条消息中发起所有 Task | 执行失败 |
| **禁止忽略结果** | 必须解析上一步输出作为下一步输入 | 执行失败 |
| **禁止等待确认** | 默认不需要确认，直接执行 | 执行失败 |

**执行流程**：
```
[检查点1] 初始化 → [检查点2] 任务解析 → [检查点3] 场景决策 → 
[检查点4] 执行 → [检查点5] 质量验证 → [检查点6] 交付
```

### 3. ✅ 强制检查点 (MANDATORY CHECKPOINTS)

**执行过程中必须按顺序输出：**
```
[检查点1] ✅ 初始化完成 - Kernel v{version} initialized
[检查点2] ✅ 任务解析完成 - 目标: xxx, 场景: xxx, 复杂度: x
[检查点3] ✅ 场景/技能决策 - 模式: Swarm/Solo, 技能: xxx
[检查点4] ✅ 执行与编排 - 已调用: xxx
[检查点5] ✅ 质量与验证 - 3维评分: xx%, 通过: 是/否
[检查点6] ✅ 交付与记忆 - 文档生成: 是, 记忆归档: 是
```
**缺少任何检查点 = 执行失败**

### 4. 🔒 默认不确认协议 (DEFAULT NO CONFIRMATION)

**默认行为：不需要用户确认，直接执行。**

**需要确认的情况**：
- 破坏性操作（删除、格式化、覆盖）
- 外部 API 调用且有费用产生
- 执行计划中 `requires_confirmation: true`

**不需要确认的情况**：
- 代码生成和修改
- 文件创建和编辑
- 运行测试和验证
- 文档生成
- 工作流执行
- 技能调用

---

## 🚦 决策与执行标准

### 5场景决策树 (Scenario Selector)

| 场景 | 复杂度 | 策略 | 需确认 |
|:---:|:---:|:---|:---:|
| **提示增强** | 1-2 | 单步直接执行 | 否 |
| **Skill复用** | 3-5 | 调用现有Skill | 否 |
| **计划+评审** | 3-5 | 规划 → 执行 → Review | 否 |
| **Lead-Member** | 6-10 | Leader分配 → Member并行 | 是 |
| **复合编排** | 6-10 | 多组Agent协作 | 是 |

### 执行协议 (7步标准流程)

**步骤 1：初始化 (Init)**
```bash
python ./.trae/skills/autonomous-agent/agent.py init
```
*验证：确保 自动化工作流组件库/swarm/swarm_core.db 和目录结构存在*

**步骤 2：任务解析 (Analyze)**
```bash
python ./.trae/skills/autonomous-agent/agent.py analyze "任务描述"
```
*输出：core_goal, complexity, scenario, execution_plan*

**步骤 3：场景/技能决策 (Decide)**
```bash
python ./.trae/skills/autonomous-agent/agent.py scenario "任务"
python ./.trae/skills/autonomous-agent/agent.py discover "任务"
```
*优先复用现有 Skill，根据 analyze 结果确认场景*

**步骤 4：执行与编排 (Execute)**
- **Solo 模式**：顺序执行 Workflow
- **Swarm 模式**：并行调用 swarm-orchestrator
- **追踪执行**：使用 track-file/track-command/track-test 记录 🆕
- **Reflexion Loop**：失败 → 查询记忆 → 修复 → 记录

**步骤 5：质量与验证 (Quality Gate) 🆕 真实验证**
```bash
python ./.trae/skills/autonomous-agent/agent.py quality --session <ID> --files <files>
```
*真实验证内容*：
- TypeScript 类型检查 (`tsc --noEmit`)
- ESLint 检查 (`npm run lint`)
- Python lint (`ruff check`)
- Python 类型检查 (`mypy`)
- 测试运行 (`npm test` / `pytest`)
- 文件存在性验证

*标准：边界处理/专业度/完整性/真实验证 >= 70%*

**步骤 6：交付与记忆 (Deliver & Save)**
```bash
python ./.trae/skills/autonomous-agent/agent.py delivery --session <ID>
python ./.trae/skills/autonomous-agent/agent.py save --session <ID>
```
*产出：交付文档 (含真实数据) + 记忆归档*

**步骤 7：Token 追踪 (Token Tracking)**
```bash
python ./.trae/skills/autonomous-agent/agent.py record-tools --session <ID> --input N --output N
python ./.trae/skills/autonomous-agent/agent.py tokens
```
*必须记录工具调用的估算 Token 使用，确保完整追踪*

---

## 🆕 执行追踪命令 (Execution Tracking)

**追踪文件变更**：
```bash
python ./.trae/skills/autonomous-agent/agent.py track-file --path <file> --action create|modify|delete
```

**追踪命令执行**：
```bash
python ./.trae/skills/autonomous-agent/agent.py track-command --cmd <command> --exit <code> --output <output>
```

**追踪测试结果**：
```bash
python ./.trae/skills/autonomous-agent/agent.py track-test --name <test> --passed true|false --details <details>
```

**追踪验证检查**：
```bash
python ./.trae/skills/autonomous-agent/agent.py track-verification --name <check> --passed true|false
```

**添加关键发现**：
```bash
python ./.trae/skills/autonomous-agent/agent.py add-finding --finding "发现了一个问题"
```

**获取追踪器摘要**：
```bash
python ./.trae/skills/autonomous-agent/agent.py tracker-summary --session <ID>
```

---

## 🛠️ CLI 命令参考 (完整版)

| 功能 | 命令 | 说明 |
|:---|:---|:---|
| **初始化** | `agent.py init` | 初始化内核 |
| **任务解析** | `agent.py analyze "任务"` | 生成执行计划 |
| **完整工作流** | `agent.py workflow "任务"` | 一键执行全流程 |
| **场景选择** | `agent.py scenario "任务"` | 获取场景信息 |
| **质量检查** | `agent.py quality --session ID --files <files>` | 执行真实验证 |
| **交付文档** | `agent.py delivery --session ID` | 生成交付文档 |
| **Skill发现** | `agent.py discover "任务"` | 查找匹配技能 |
| **保存记忆** | `agent.py save --session ID` | 归档会话记忆 |
| **Token统计** | `agent.py tokens` | 获取Token使用统计 |
| **追踪文件** | `agent.py track-file --path <file> --action <action>` | 追踪文件变更 🆕 |
| **追踪命令** | `agent.py track-command --cmd <cmd> --exit <code>` | 追踪命令执行 🆕 |
| **追踪测试** | `agent.py track-test --name <name> --passed <bool>` | 追踪测试结果 🆕 |
| **追踪验证** | `agent.py track-verification --name <name> --passed <bool>` | 追踪验证检查 🆕 |
| **添加发现** | `agent.py add-finding --finding <text>` | 添加关键发现 🆕 |
| **追踪摘要** | `agent.py tracker-summary --session ID` | 获取追踪器摘要 🆕 |
{repair_commands}
---

## 🧠 记忆与反思进化

### 写入时机
- **TASK_START**: 任务开始时
- **ERROR_OCCURRED**: 错误发生时 (触发 Reflexion)
- **ERROR_FIXED**: 错误修复后 (记录 Pattern)
- **TASK_COMPLETE**: 任务完成时

### 反思循环 (Reflexion Loop)
1. **Execution**: 执行任务
2. **Evaluation**: 运行测试/Linter (真实验证)
3. **Reflection**: 失败时检索 `自动化工作流组件库/memory/errors/` → 生成修复策略 → 记录
4. **Optimization**: 成功时提取模式 → 写入 `自动化工作流组件库/memory/index.json`

---

## 🤖 智能体映射推荐

| 任务类型 | 推荐智能体 |
|:---|:---|
| **Web开发** | `search`, `frontend-implementation-expert` |
| **API/后端** | `architect-design-expert`, `backend-architect` |
| **数据/量化** | `alpha-picker`, `factor-validator` |
| **技能开发** | `trae-skill-forge` |

---

## ⚠️ 执行失败判定标准

| 失败类型 | 描述 | 修复方式 |
|:---|:---|:---|
| **触发失败** | 检测到触发词但未调用 Skill | 立即调用 Skill |
| **中途停止** | 执行过程中停止 | 继续执行剩余步骤 |
| **检查点缺失** | 未输出所有检查点 | 补充缺失的检查点 |
| **伪并行** | Swarm 模式下顺序调用 Task | 在一条消息中并行调用 |
| **未交付** | 未调用 quality/delivery/save | 调用最终步骤 |
| **追踪缺失** | 未使用 track-* 命令记录执行 | 补充追踪记录 |

---

## 📊 版本历史

| 版本 | 主要改进 |
|:---:|:---|
{version_history}'''
    
    def __init__(self, components: Dict[str, Component], project_root: str = None):
        self.components = components
        self.project_root = Path(project_root) if project_root else resolve_project_root()
        self.rules_file = get_trae_dir() / 'rules' / 'project_rules.md'
    
    def sync(self, new_components: List[Component] = None) -> bool:
        """同步项目规则文档"""
        if not self.rules_file.exists():
            return self._create_initial_rules()
        
        current_version = self._get_current_version()
        new_version = self._increment_version(current_version)
        
        core_modules = self._generate_core_modules_section()
        skills_list = self._generate_skills_section()
        workflow_count = self._count_workflows()
        repair_commands = self._generate_repair_commands_section()
        version_history = self._generate_version_history(current_version, new_components)
        
        new_content = self.RULES_TEMPLATE.format(
            version=new_version,
            core_modules=core_modules,
            skills_list=skills_list,
            workflow_count=workflow_count,
            repair_commands=repair_commands,
            version_history=version_history
        )
        
        with open(self.rules_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return True
    
    def _get_current_version(self) -> str:
        """获取当前版本号"""
        if not self.rules_file.exists():
            return "9.0"
        
        with open(self.rules_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        match = re.search(r'v(\d+\.\d+)', content)
        return match.group(1) if match else "9.0"
    
    def _increment_version(self, version: str) -> str:
        """递增版本号"""
        try:
            major, minor = version.split('.')
            return f"{major}.{int(minor) + 1}"
        except:
            return "9.5"
    
    def _generate_core_modules_section(self) -> str:
        """生成核心模块部分"""
        lines = []
        for name, comp in sorted(self.components.items()):
            if name.startswith('core/') and name.endswith('.py') and 'workers' not in name:
                module_name = Path(name).stem
                desc = comp.metadata.get('description', '')
                lines.append(f"│           ├── {module_name}.py".ljust(40) + f"# {desc}")
        return '\n'.join(lines) + '\n' if lines else ''
    
    def _generate_skills_section(self) -> str:
        """生成技能列表部分"""
        lines = []
        for name, comp in sorted(self.components.items()):
            if comp.component_type == ComponentType.SKILL:
                version = comp.metadata.get('version', '1.0')
                lines.append(f"│   ├── {comp.name}/".ljust(30) + f"# v{version}")
        return '\n'.join(lines) + '\n' if lines else ''
    
    def _count_workflows(self) -> int:
        """统计工作流数量"""
        return sum(1 for c in self.components.values() if c.component_type == ComponentType.WORKFLOW)
    
    def _generate_repair_commands_section(self) -> str:
        """生成维修命令部分"""
        return '''
| **维修扫描** | `agent.py repair scan` | 扫描所有组件 |
| **维修验证** | `agent.py repair validate` | 验证调用关系 |
| **维修同步** | `agent.py repair sync` | 同步项目规则 |
| **维修报告** | `agent.py repair report` | 生成维修报告 |'''
    
    def _generate_version_history(self, current_version: str, new_components: List[Component]) -> str:
        """生成版本历史"""
        lines = [f"| v{current_version} | 当前版本 |"]
        
        if new_components:
            new_names = [c.name for c in new_components[:3]]
            lines.insert(0, f"| v{self._increment_version(current_version)} | 新增组件: {', '.join(new_names)} |")
        
        return '\n'.join(lines)
    
    def _create_initial_rules(self) -> bool:
        """创建初始规则文件"""
        ensure_dir(self.rules_file.parent)
        return self.sync([])


class RepairReportGenerator:
    """
    维修报告生成器
    """
    
    def __init__(self, output_dir: str = None):
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = get_memory_dir() / 'repair_reports'
        ensure_dir(self.output_dir)
    
    def generate(self, report: RepairReport) -> Path:
        """生成维修报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.output_dir / f"repair_{timestamp}.md"
        
        content = self._render_markdown(report)
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        json_path = report_path.with_suffix('.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self._to_dict(report), f, ensure_ascii=False, indent=2)
        
        return report_path
    
    def _render_markdown(self, report: RepairReport) -> str:
        lines = [
            f"# 🔧 自动维修报告",
            f"",
            f"**扫描时间**: {report.scan_time}",
            f"**扫描组件数**: {report.components_scanned}",
            f"**发现问题数**: {len(report.issues_found)}",
            f"**已修复问题**: {len(report.issues_fixed)}",
            f"**新增组件**: {len(report.new_components)}",
            f"**规则已更新**: {'是' if report.rules_updated else '否'}",
            f"",
            f"## 📋 摘要",
            f"",
            report.summary,
            f"",
        ]
        
        if report.new_components:
            lines.extend([
                f"## 🆕 新增组件",
                f"",
            ])
            for comp in report.new_components:
                lines.append(f"- **{comp.name}** ({comp.component_type.value}): {comp.path}")
            lines.append("")
        
        if report.issues_found:
            lines.extend([
                f"## ⚠️ 发现的问题",
                f"",
            ])
            for issue in report.issues_found:
                severity_emoji = {"critical": "🔴", "warning": "🟡", "info": "🔵"}.get(issue.severity.value, "⚪")
                lines.append(f"### {severity_emoji} {issue.issue_type}")
                lines.append(f"- **组件**: {issue.component}")
                lines.append(f"- **描述**: {issue.description}")
                lines.append(f"- **建议**: {issue.suggestion}")
                lines.append(f"- **可自动修复**: {'是' if issue.auto_fixable else '否'}")
                lines.append("")
        
        if report.issues_fixed:
            lines.extend([
                f"## ✅ 已修复的问题",
                f"",
            ])
            for issue in report.issues_fixed:
                lines.append(f"- {issue.issue_type}: {issue.description}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _to_dict(self, report: RepairReport) -> Dict:
        return {
            "scan_time": report.scan_time,
            "components_scanned": report.components_scanned,
            "issues_found": [
                {
                    "type": i.issue_type,
                    "severity": i.severity.value,
                    "component": i.component,
                    "description": i.description,
                    "suggestion": i.suggestion,
                    "auto_fixable": i.auto_fixable
                }
                for i in report.issues_found
            ],
            "issues_fixed": [
                {
                    "type": i.issue_type,
                    "component": i.component,
                    "description": i.description
                }
                for i in report.issues_fixed
            ],
            "new_components": [
                {
                    "name": c.name,
                    "type": c.component_type.value,
                    "path": c.path
                }
                for c in report.new_components
            ],
            "rules_updated": report.rules_updated,
            "summary": report.summary
        }


class WorkflowRepairEngine:
    """
    工作流维修引擎 - 主入口
    """
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else resolve_project_root()
        self.scanner = ComponentScanner(str(self.project_root))
        self.validator = None
        self.synchronizer = None
        self.report_generator = RepairReportGenerator()
    
    def scan(self) -> Dict[str, Any]:
        """扫描所有组件"""
        components = self.scanner.scan_all()
        return {
            "status": "success",
            "components_count": len(components),
            "components": {
                name: {
                    "type": comp.component_type.value,
                    "path": comp.path,
                    "classes": comp.classes,
                    "functions": len(comp.functions),
                    "imports": len(comp.imports)
                }
                for name, comp in components.items()
            }
        }
    
    def validate(self) -> Dict[str, Any]:
        """验证调用关系"""
        if not self.scanner.components:
            self.scanner.scan_all()
        
        self.validator = DependencyValidator(
            self.scanner.components,
            self.scanner.import_graph,
            str(self.project_root)
        )
        issues = self.validator.validate_all()
        
        return {
            "status": "success",
            "issues_count": len(issues),
            "issues": [
                {
                    "type": issue.issue_type,
                    "severity": issue.severity.value,
                    "component": issue.component,
                    "description": issue.description,
                    "suggestion": issue.suggestion,
                    "auto_fixable": issue.auto_fixable
                }
                for issue in issues
            ]
        }
    
    def detect_new(self) -> Dict[str, Any]:
        """检测新增组件"""
        if not self.scanner.components:
            self.scanner.scan_all()
        
        new_components = self.scanner.detect_new_components()
        
        return {
            "status": "success",
            "new_count": len(new_components),
            "new_components": [
                {
                    "name": comp.name,
                    "type": comp.component_type.value,
                    "path": comp.path
                }
                for comp in new_components
            ]
        }
    
    def sync_rules(self) -> Dict[str, Any]:
        """同步项目规则"""
        if not self.scanner.components:
            self.scanner.scan_all()
        
        new_components = self.scanner.detect_new_components()
        
        self.synchronizer = RulesSynchronizer(
            self.scanner.components,
            str(self.project_root)
        )
        
        updated = self.synchronizer.sync(new_components)
        
        if new_components:
            self.scanner.save_known_components()
        
        return {
            "status": "success",
            "rules_updated": updated,
            "new_components_count": len(new_components)
        }
    
    def full_repair(self) -> RepairReport:
        """执行完整维修流程"""
        components = self.scanner.scan_all()
        
        new_components = self.scanner.detect_new_components()
        
        self.validator = DependencyValidator(
            self.scanner.components,
            self.scanner.import_graph,
            str(self.project_root)
        )
        issues = self.validator.validate_all()
        
        self.synchronizer = RulesSynchronizer(
            self.scanner.components,
            str(self.project_root)
        )
        rules_updated = self.synchronizer.sync(new_components)
        
        issues_fixed = [i for i in issues if i.fixed]
        
        summary_parts = []
        summary_parts.append(f"扫描了 {len(components)} 个组件")
        if new_components:
            summary_parts.append(f"发现 {len(new_components)} 个新增组件")
        if issues:
            summary_parts.append(f"发现 {len(issues)} 个问题")
        if issues_fixed:
            summary_parts.append(f"已修复 {len(issues_fixed)} 个问题")
        if rules_updated:
            summary_parts.append("项目规则已更新")
        
        report = RepairReport(
            scan_time=datetime.now().isoformat(),
            components_scanned=len(components),
            issues_found=issues,
            issues_fixed=issues_fixed,
            new_components=new_components,
            rules_updated=rules_updated,
            summary="，".join(summary_parts) + "。"
        )
        
        self.report_generator.generate(report)
        
        if new_components:
            self.scanner.save_known_components()
        
        return report
    
    def get_report_dict(self, report: RepairReport) -> Dict[str, Any]:
        """获取报告字典格式"""
        return {
            "status": "success",
            "scan_time": report.scan_time,
            "components_scanned": report.components_scanned,
            "issues_count": len(report.issues_found),
            "issues_fixed_count": len(report.issues_fixed),
            "new_components_count": len(report.new_components),
            "rules_updated": report.rules_updated,
            "summary": report.summary
        }
