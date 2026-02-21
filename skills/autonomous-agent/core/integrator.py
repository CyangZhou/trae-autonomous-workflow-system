"""
Integrator Agent v1.0 - 整合智能体
核心功能:
1. 整合各蜂群子智能体的产出
2. 执行"打结"逻辑，确保内容连贯
3. 检测并解决冲突
4. 生成完整可用的成品
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class IntegrationStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CONFLICT_DETECTED = "conflict_detected"


class ConflictType(Enum):
    DUPLICATE_CONTENT = "duplicate_content"
    INCONSISTENT_INTERFACE = "inconsistent_interface"
    MISSING_DEPENDENCY = "missing_dependency"
    VERSION_MISMATCH = "version_mismatch"
    LOGIC_CONFLICT = "logic_conflict"


@dataclass
class Conflict:
    conflict_id: str
    conflict_type: ConflictType
    source_tasks: List[str]
    description: str
    severity: str
    resolution: str = ""
    resolved: bool = False


@dataclass
class IntegrationResult:
    session_id: str
    status: IntegrationStatus
    integrated_files: List[str]
    conflicts: List[Conflict]
    quality_score: float
    summary: str
    delivery_artifacts: Dict[str, Any]
    timestamp: str


class IntegratorAgent:
    """
    整合智能体
    
    职责:
    1. 收集所有子任务的产出
    2. 检测并解决冲突
    3. 执行"打结"逻辑
    4. 生成最终交付物
    """
    
    INTEGRATION_RULES = {
        "code_files": {
            "strategy": "merge_with_imports",
            "conflict_resolution": "prefer_newer",
            "validation": ["syntax_check", "import_check"]
        },
        "documentation": {
            "strategy": "concatenate_with_toc",
            "conflict_resolution": "merge_sections",
            "validation": ["link_check", "format_check"]
        },
        "tests": {
            "strategy": "collect_all",
            "conflict_resolution": "rename_duplicates",
            "validation": ["syntax_check", "execution_check"]
        },
        "config": {
            "strategy": "deep_merge",
            "conflict_resolution": "prefer_explicit",
            "validation": ["schema_check", "dependency_check"]
        }
    }
    
    def __init__(self, output_dir: str = None):
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path("自动化工作流组件库/memory/integration")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.task_doc_dir = Path("自动化工作流组件库/memory/task_docs")
    
    def integrate(self, session_id: str, task_results: Dict[str, Any]) -> IntegrationResult:
        """
        主入口: 整合所有子任务产出
        
        流程:
        1. 加载任务文档
        2. 收集所有产出
        3. 检测冲突
        4. 解决冲突
        5. 执行打结
        6. 生成交付物
        7. 验证完整性
        """
        task_doc = self._load_task_document(session_id)
        
        if not task_doc:
            return IntegrationResult(
                session_id=session_id,
                status=IntegrationStatus.FAILED,
                integrated_files=[],
                conflicts=[],
                quality_score=0.0,
                summary="无法加载任务文档",
                delivery_artifacts={},
                timestamp=datetime.now().isoformat()
            )
        
        collected_outputs = self._collect_outputs(task_results)
        
        conflicts = self._detect_conflicts(collected_outputs, task_doc)
        
        resolved_outputs = self._resolve_conflicts(collected_outputs, conflicts)
        
        integrated = self._execute_integration(resolved_outputs, task_doc)
        
        delivery_artifacts = self._generate_delivery_artifacts(integrated, task_doc)
        
        quality_score = self._calculate_quality_score(integrated, conflicts, task_doc)
        
        summary = self._generate_summary(integrated, conflicts, quality_score)
        
        result = IntegrationResult(
            session_id=session_id,
            status=IntegrationStatus.COMPLETED if quality_score >= 0.7 else IntegrationStatus.FAILED,
            integrated_files=list(integrated.keys()),
            conflicts=conflicts,
            quality_score=quality_score,
            summary=summary,
            delivery_artifacts=delivery_artifacts,
            timestamp=datetime.now().isoformat()
        )
        
        self._save_result(result)
        
        return result
    
    def _load_task_document(self, session_id: str) -> Optional[Dict]:
        """加载任务文档"""
        doc_path = self.task_doc_dir / f"{session_id}_task_doc.json"
        
        if not doc_path.exists():
            return None
        
        with open(doc_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _collect_outputs(self, task_results: Dict[str, Any]) -> Dict[str, Any]:
        """收集所有子任务产出"""
        collected = {
            "code_files": [],
            "documentation": [],
            "tests": [],
            "config": [],
            "other": []
        }
        
        for task_id, result in task_results.items():
            if not isinstance(result, dict):
                continue
            
            output_type = result.get("output_type", "other")
            files = result.get("files", [])
            content = result.get("content", "")
            
            if output_type in collected:
                collected[output_type].append({
                    "task_id": task_id,
                    "files": files,
                    "content": content,
                    "metadata": result.get("metadata", {})
                })
            else:
                collected["other"].append({
                    "task_id": task_id,
                    "files": files,
                    "content": content,
                    "metadata": result.get("metadata", {})
                })
        
        return collected
    
    def _detect_conflicts(self, outputs: Dict[str, Any], task_doc: Dict) -> List[Conflict]:
        """检测冲突"""
        conflicts = []
        conflict_id = 0
        
        file_owners = {}
        for output_type, items in outputs.items():
            for item in items:
                for file_path in item.get("files", []):
                    if file_path in file_owners:
                        conflicts.append(Conflict(
                            conflict_id=f"CONFLICT_{conflict_id:03d}",
                            conflict_type=ConflictType.DUPLICATE_CONTENT,
                            source_tasks=[file_owners[file_path], item["task_id"]],
                            description=f"文件 {file_path} 被多个任务修改",
                            severity="high"
                        ))
                        conflict_id += 1
                    else:
                        file_owners[file_path] = item["task_id"]
        
        for output_type, items in outputs.items():
            contents = [item.get("content", "") for item in items]
            for i, c1 in enumerate(contents):
                for j, c2 in enumerate(contents[i+1:], i+1):
                    if c1 and c2 and self._calculate_similarity(c1, c2) > 0.8:
                        conflicts.append(Conflict(
                            conflict_id=f"CONFLICT_{conflict_id:03d}",
                            conflict_type=ConflictType.DUPLICATE_CONTENT,
                            source_tasks=[items[i]["task_id"], items[j]["task_id"]],
                            description=f"检测到高度相似的内容",
                            severity="medium"
                        ))
                        conflict_id += 1
        
        return conflicts
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        if not text1 or not text2:
            return 0.0
        
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0
    
    def _resolve_conflicts(self, outputs: Dict[str, Any], conflicts: List[Conflict]) -> Dict[str, Any]:
        """解决冲突"""
        resolved = outputs.copy()
        
        for conflict in conflicts:
            if conflict.conflict_type == ConflictType.DUPLICATE_CONTENT:
                if len(conflict.source_tasks) >= 2:
                    task_to_keep = conflict.source_tasks[-1]
                    
                    for output_type in resolved:
                        items_to_remove = []
                        for item in resolved[output_type]:
                            if item["task_id"] in conflict.source_tasks and item["task_id"] != task_to_keep:
                                items_to_remove.append(item)
                        
                        for item in items_to_remove:
                            resolved[output_type].remove(item)
                    
                    conflict.resolution = f"保留任务 {task_to_keep} 的产出"
                    conflict.resolved = True
        
        return resolved
    
    def _execute_integration(self, outputs: Dict[str, Any], task_doc: Dict) -> Dict[str, Any]:
        """执行整合逻辑"""
        integrated = {}
        
        for output_type, items in outputs.items():
            if not items:
                continue
            
            rules = self.INTEGRATION_RULES.get(output_type, {})
            strategy = rules.get("strategy", "collect_all")
            
            if strategy == "merge_with_imports":
                integrated[output_type] = self._merge_code_files(items)
            elif strategy == "concatenate_with_toc":
                integrated[output_type] = self._concatenate_docs(items)
            elif strategy == "collect_all":
                integrated[output_type] = self._collect_all_items(items)
            elif strategy == "deep_merge":
                integrated[output_type] = self._deep_merge_configs(items)
            else:
                integrated[output_type] = items
        
        return integrated
    
    def _merge_code_files(self, items: List[Dict]) -> Dict[str, Any]:
        """合并代码文件"""
        merged = {
            "files": {},
            "imports": set(),
            "main_content": []
        }
        
        for item in items:
            for file_path in item.get("files", []):
                if file_path not in merged["files"]:
                    merged["files"][file_path] = item.get("content", "")
            
            content = item.get("content", "")
            import_lines = [line for line in content.split('\n') if line.strip().startswith(('import ', 'from '))]
            merged["imports"].update(import_lines)
        
        merged["imports"] = list(merged["imports"])
        return merged
    
    def _concatenate_docs(self, items: List[Dict]) -> Dict[str, Any]:
        """拼接文档"""
        sections = []
        toc = ["# 目录\n"]
        
        for i, item in enumerate(items, 1):
            content = item.get("content", "")
            task_name = item.get("metadata", {}).get("task_name", f"第{i}部分")
            
            section_title = f"## {task_name}\n"
            sections.append(section_title + content + "\n")
            toc.append(f"{i}. [{task_name}](#{task_name.lower().replace(' ', '-')})\n")
        
        return {
            "toc": "".join(toc),
            "content": "\n".join(sections),
            "sections_count": len(sections)
        }
    
    def _collect_all_items(self, items: List[Dict]) -> Dict[str, Any]:
        """收集所有项目"""
        return {
            "items": items,
            "count": len(items),
            "files": [f for item in items for f in item.get("files", [])]
        }
    
    def _deep_merge_configs(self, items: List[Dict]) -> Dict[str, Any]:
        """深度合并配置"""
        merged = {}
        
        for item in items:
            content = item.get("content", "")
            try:
                config = json.loads(content) if content else {}
                merged = self._deep_merge(merged, config)
            except:
                pass
        
        return merged
    
    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """深度合并字典"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _generate_delivery_artifacts(self, integrated: Dict[str, Any], task_doc: Dict) -> Dict[str, Any]:
        """生成交付物"""
        artifacts = {
            "main_task": task_doc.get("main_task", ""),
            "created_at": datetime.now().isoformat(),
            "files": [],
            "documentation": "",
            "summary": ""
        }
        
        if "code_files" in integrated:
            artifacts["files"].extend(integrated["code_files"].get("files", {}).keys())
        
        if "documentation" in integrated:
            artifacts["documentation"] = integrated["documentation"].get("content", "")
        
        summary_parts = []
        for output_type, data in integrated.items():
            if isinstance(data, dict):
                if "count" in data:
                    summary_parts.append(f"{output_type}: {data['count']} 项")
                elif "files" in data:
                    summary_parts.append(f"{output_type}: {len(data['files'])} 个文件")
        
        artifacts["summary"] = " | ".join(summary_parts)
        
        return artifacts
    
    def _calculate_quality_score(self, integrated: Dict[str, Any], conflicts: List[Conflict], task_doc: Dict) -> float:
        """计算质量分数"""
        score = 1.0
        
        unresolved_conflicts = [c for c in conflicts if not c.resolved]
        high_severity = len([c for c in unresolved_conflicts if c.severity == "high"])
        medium_severity = len([c for c in unresolved_conflicts if c.severity == "medium"])
        
        score -= high_severity * 0.3
        score -= medium_severity * 0.1
        
        total_tasks = task_doc.get("total_tasks", 1)
        completed_outputs = sum(len(items) for items in integrated.values() if isinstance(items, list))
        completion_ratio = completed_outputs / max(total_tasks, 1)
        
        score = score * 0.7 + completion_ratio * 0.3
        
        return max(0.0, min(1.0, score))
    
    def _generate_summary(self, integrated: Dict[str, Any], conflicts: List[Conflict], quality_score: float) -> str:
        """生成整合摘要"""
        lines = [
            f"# 整合报告",
            f"",
            f"## 概览",
            f"- 整合状态: {'成功' if quality_score >= 0.7 else '需要修复'}",
            f"- 质量分数: {quality_score:.1%}",
            f"- 检测到冲突: {len(conflicts)} 个",
            f"- 已解决冲突: {len([c for c in conflicts if c.resolved])} 个",
            f"",
            f"## 整合内容",
        ]
        
        for output_type, data in integrated.items():
            if isinstance(data, dict):
                if "count" in data:
                    lines.append(f"- {output_type}: {data['count']} 项")
                elif "files" in data:
                    lines.append(f"- {output_type}: {len(data['files'])} 个文件")
                elif "sections_count" in data:
                    lines.append(f"- {output_type}: {data['sections_count']} 个章节")
        
        if conflicts:
            lines.extend([
                f"",
                f"## 冲突详情",
            ])
            for conflict in conflicts:
                status = "✅ 已解决" if conflict.resolved else "⚠️ 待处理"
                lines.append(f"- [{status}] {conflict.description}")
        
        return "\n".join(lines)
    
    def _save_result(self, result: IntegrationResult):
        """保存整合结果"""
        result_path = self.output_dir / f"{result.session_id}_integration.json"
        
        result_dict = {
            "session_id": result.session_id,
            "status": result.status.value,
            "integrated_files": result.integrated_files,
            "conflicts": [
                {
                    "conflict_id": c.conflict_id,
                    "type": c.conflict_type.value,
                    "source_tasks": c.source_tasks,
                    "description": c.description,
                    "severity": c.severity,
                    "resolution": c.resolution,
                    "resolved": c.resolved
                }
                for c in result.conflicts
            ],
            "quality_score": result.quality_score,
            "summary": result.summary,
            "delivery_artifacts": result.delivery_artifacts,
            "timestamp": result.timestamp
        }
        
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(result_dict, f, ensure_ascii=False, indent=2)
    
    def get_integration_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取整合状态"""
        result_path = self.output_dir / f"{session_id}_integration.json"
        
        if not result_path.exists():
            return None
        
        with open(result_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_tying_instruction(self, session_id: str) -> Dict[str, Any]:
        """获取打结指令 - 供 Agent 执行"""
        task_doc = self._load_task_document(session_id)
        
        if not task_doc:
            return {"error": f"No task document found for session {session_id}"}
        
        integration_plan = task_doc.get("integration_plan", {})
        
        return {
            "session_id": session_id,
            "instruction": """
# 整合任务指令

## 目标
将所有子任务的产出整合为完整可用的成品。

## 整合策略
1. **代码文件**: 合并导入，保留最新版本
2. **文档**: 按章节拼接，生成目录
3. **测试**: 收集所有测试用例
4. **配置**: 深度合并，优先显式配置

## 质量要求
- 无冲突或重复内容
- 逻辑连贯
- 可直接使用

## 输出格式
生成完整的交付文档，包含:
- 所有整合后的文件
- 使用说明
- 部署指南
""",
            "integration_plan": integration_plan,
            "expected_outputs": [
                "整合后的代码文件",
                "完整的文档",
                "测试套件",
                "配置文件",
                "交付说明"
            ]
        }
