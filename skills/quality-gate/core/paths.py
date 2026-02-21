"""
Paths v3.1 - 统一路径解析模块
所有组件共享的路径解析函数，确保跨项目移植的一致性

路径架构 v3.1:
- .trae/                    核心配置 (只读/版本控制)
  - rules/                  项目规则
  - skills/                 技能定义
- 自动化工作流组件库/        运行时数据 (可修改)
  - config/                 配置文件
  - memory/                 记忆存储
  - delivery/               交付文档
  - knowledge/              知识库
  - workflows/              工作流定义
  - swarm/                  Swarm配置
  - templates/              模板文件
  - logs/                   日志文件
"""

from pathlib import Path
from typing import Optional


RUNTIME_DIR_NAME = "自动化工作流组件库"


def resolve_project_root() -> Path:
    """
    动态解析项目根目录
    
    解析策略:
    1. 从当前文件位置向上回溯
    2. 查找 .trae 目录作为项目根标识
    
    Returns:
        Path: 项目根目录的绝对路径
    """
    current_file = Path(__file__).resolve()
    
    strategy_1 = current_file.parent.parent.parent.parent.parent.parent
    if (strategy_1 / '.trae').exists():
        return strategy_1
    
    parent = current_file.parent
    while parent != parent.parent:
        if (parent / '.trae').exists():
            return parent
        parent = parent.parent
    
    if Path('.trae').exists():
        return Path('.').resolve()
    
    return strategy_1


def get_trae_dir() -> Path:
    """获取 .trae 目录路径 (核心配置，只读)"""
    return resolve_project_root() / '.trae'


def get_runtime_dir() -> Path:
    """获取运行时数据目录路径 (可修改)"""
    return resolve_project_root() / RUNTIME_DIR_NAME


def get_config_dir() -> Path:
    """获取 config 目录路径"""
    return get_runtime_dir() / 'config'


def get_memory_dir() -> Path:
    """获取 memory 目录路径"""
    return get_runtime_dir() / 'memory'


def get_skills_dir() -> Path:
    """获取 skills 目录路径"""
    return get_trae_dir() / 'skills'


def get_workflows_dir() -> Path:
    """获取 workflows 目录路径"""
    return get_runtime_dir() / 'workflows'


def get_swarm_dir() -> Path:
    """获取 swarm 目录路径"""
    return get_runtime_dir() / 'swarm'


def get_delivery_dir() -> Path:
    """获取 delivery 目录路径"""
    return get_runtime_dir() / 'delivery'


def get_knowledge_dir() -> Path:
    """获取 knowledge 目录路径"""
    return get_runtime_dir() / 'knowledge'


def get_logs_dir() -> Path:
    """获取 logs 目录路径"""
    return get_runtime_dir() / 'logs'


def get_templates_dir() -> Path:
    """获取 templates 目录路径"""
    return get_runtime_dir() / 'templates'


def get_rules_dir() -> Path:
    """获取 rules 目录路径"""
    return get_trae_dir() / 'rules'


def get_skill_registry_path() -> Path:
    """获取技能注册表文件路径"""
    return get_config_dir() / 'skill-registry.json'


def get_agent_registry_path() -> Path:
    """获取智能体注册表文件路径"""
    return get_swarm_dir() / 'agent_registry.json'


def ensure_dir(path: Path) -> Path:
    """确保目录存在，不存在则创建"""
    path.mkdir(parents=True, exist_ok=True)
    return path


def init_runtime_directories() -> dict:
    """
    初始化运行时数据目录结构
    返回创建的目录列表
    """
    created = []
    dirs = [
        get_runtime_dir(),
        get_config_dir(),
        get_memory_dir(),
        get_memory_dir() / 'ltm',
        get_memory_dir() / 'sessions',
        get_memory_dir() / 'tasks',
        get_memory_dir() / 'errors',
        get_memory_dir() / 'quality',
        get_memory_dir() / 'repair_reports',
        get_memory_dir() / 'closed_loop',
        get_memory_dir() / 'task_docs',
        get_memory_dir() / 'reflexion',
        get_memory_dir() / 'integration',
        get_memory_dir() / 'distillation',
        get_memory_dir() / 'execution_tracks',
        get_delivery_dir(),
        get_knowledge_dir(),
        get_workflows_dir(),
        get_swarm_dir(),
        get_templates_dir(),
        get_templates_dir() / 'validation_scripts',
        get_logs_dir(),
    ]
    
    for d in dirs:
        if not d.exists():
            ensure_dir(d)
            created.append(str(d))
    
    return {"initialized": len(created), "directories": created}


def get_relative_path(absolute_path: Path) -> str:
    """将绝对路径转换为相对于项目根目录的相对路径"""
    try:
        return str(absolute_path.relative_to(resolve_project_root()))
    except ValueError:
        return str(absolute_path)


# 兼容旧版本的别名
get_agent_dir = get_runtime_dir
init_agent_directories = init_runtime_directories
