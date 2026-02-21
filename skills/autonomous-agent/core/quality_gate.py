"""
Quality Gate v1.1 - 真实验证质量把关模块
改进: 
1. 从正则匹配改为运行真实 lint/test/typecheck
2. 集成 Token 追踪功能
"""

import json
import re
import subprocess
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from .paths import get_memory_dir, ensure_dir
from .token_tracker import record_session_tokens, estimate_tokens, estimate_tokens_for_dict


class QualityDimension(Enum):
    BOUNDARY = "boundary"
    PROFESSIONALISM = "professionalism"
    COMPLETENESS = "completeness"
    REAL_VALIDATION = "real_validation"


@dataclass
class CheckItem:
    name: str
    description: str
    passed: bool = False
    score: float = 0.0
    details: str = ""
    automated: bool = True


@dataclass
class DimensionResult:
    dimension: QualityDimension
    name: str
    items: List[CheckItem] = field(default_factory=list)
    total_score: float = 0.0
    passed: bool = False


@dataclass
class QualityReport:
    session_id: str
    timestamp: str
    dimensions: List[DimensionResult] = field(default_factory=list)
    overall_score: float = 0.0
    passed: bool = False
    retry_count: int = 0
    max_retries: int = 2
    recommendations: List[str] = field(default_factory=list)
    real_validation_results: Dict[str, Any] = field(default_factory=dict)


class RealValidator:
    """
    真实验证执行器 - 运行实际的 lint/test/typecheck
    
    支持的验证类型:
    - TypeScript: tsc --noEmit
    - ESLint: npm run lint
    - Python: ruff, mypy, pytest
    - 通用: 文件存在性检查
    """
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
    
    def detect_project_type(self) -> str:
        """检测项目类型"""
        if (self.project_root / 'package.json').exists():
            return 'node'
        if (self.project_root / 'requirements.txt').exists() or list(self.project_root.glob('*.py')):
            return 'python'
        return 'general'
    
    def run_command(self, cmd: List[str], timeout: int = 60) -> Tuple[int, str, str]:
        """运行命令并返回结果"""
        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out"
        except FileNotFoundError:
            return -1, "", f"Command not found: {cmd[0]}"
        except Exception as e:
            return -1, "", str(e)
    
    def run_typescript_check(self) -> Dict[str, Any]:
        """运行 TypeScript 类型检查"""
        result = {
            "available": False,
            "passed": False,
            "errors": [],
            "warnings": []
        }
        
        if not (self.project_root / 'tsconfig.json').exists():
            result["details"] = "No tsconfig.json found"
            return result
        
        result["available"] = True
        exit_code, stdout, stderr = self.run_command(['npx', 'tsc', '--noEmit'])
        
        result["passed"] = exit_code == 0
        result["raw_output"] = (stdout + stderr)[:2000]
        
        error_lines = re.findall(r'error TS\d+:', stdout + stderr)
        result["errors"] = error_lines[:20]
        
        return result
    
    def run_eslint_check(self) -> Dict[str, Any]:
        """运行 ESLint 检查"""
        result = {
            "available": False,
            "passed": False,
            "errors": 0,
            "warnings": 0
        }
        
        package_json = self.project_root / 'package.json'
        if not package_json.exists():
            result["details"] = "No package.json found"
            return result
        
        try:
            with open(package_json, 'r', encoding='utf-8') as f:
                pkg = json.load(f)
            scripts = pkg.get('scripts', {})
            if 'lint' not in scripts:
                result["details"] = "No lint script in package.json"
                return result
        except:
            result["details"] = "Could not read package.json"
            return result
        
        result["available"] = True
        exit_code, stdout, stderr = self.run_command(['npm', 'run', 'lint'])
        
        result["passed"] = exit_code == 0
        result["raw_output"] = (stdout + stderr)[:2000]
        
        error_match = re.search(r'(\d+)\s+error', stdout + stderr, re.IGNORECASE)
        warning_match = re.search(r'(\d+)\s+warning', stdout + stderr, re.IGNORECASE)
        
        if error_match:
            result["errors"] = int(error_match.group(1))
        if warning_match:
            result["warnings"] = int(warning_match.group(1))
        
        return result
    
    def run_python_lint(self) -> Dict[str, Any]:
        """运行 Python lint 检查 (ruff)"""
        result = {
            "available": False,
            "passed": False,
            "errors": 0,
            "warnings": 0
        }
        
        exit_code, stdout, stderr = self.run_command(['ruff', 'check', '.'])
        
        if "not found" in stderr.lower() or "command not found" in stderr.lower():
            result["details"] = "ruff not installed"
            return result
        
        result["available"] = True
        result["passed"] = exit_code == 0
        result["raw_output"] = (stdout + stderr)[:2000]
        
        lines = (stdout + stderr).strip().split('\n')
        for line in lines:
            if re.match(r'.*:\d+:\d+: [EF]\d+', line):
                result["errors"] += 1
            elif re.match(r'.*:\d+:\d+: [W]\d+', line):
                result["warnings"] += 1
        
        return result
    
    def run_python_typecheck(self) -> Dict[str, Any]:
        """运行 Python 类型检查 (mypy)"""
        result = {
            "available": False,
            "passed": False,
            "errors": 0
        }
        
        exit_code, stdout, stderr = self.run_command(['mypy', '.', '--ignore-missing-imports'])
        
        if "not found" in stderr.lower() or "command not found" in stderr.lower():
            result["details"] = "mypy not installed"
            return result
        
        result["available"] = True
        result["passed"] = exit_code == 0
        result["raw_output"] = (stdout + stderr)[:2000]
        
        error_match = re.search(r'Found (\d+) error', stdout + stderr)
        if error_match:
            result["errors"] = int(error_match.group(1))
        
        return result
    
    def run_tests(self) -> Dict[str, Any]:
        """运行测试"""
        result = {
            "available": False,
            "passed": False,
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0
        }
        
        project_type = self.detect_project_type()
        
        if project_type == 'node':
            exit_code, stdout, stderr = self.run_command(['npm', 'test'], timeout=120)
            result["available"] = True
            result["passed"] = exit_code == 0
            result["raw_output"] = (stdout + stderr)[:2000]
            
            passed_match = re.search(r'(\d+)\s+passed', stdout + stderr, re.IGNORECASE)
            failed_match = re.search(r'(\d+)\s+failed', stdout + stderr, re.IGNORECASE)
            
            if passed_match:
                result["tests_passed"] = int(passed_match.group(1))
            if failed_match:
                result["tests_failed"] = int(failed_match.group(1))
            result["tests_run"] = result["tests_passed"] + result["tests_failed"]
            
        elif project_type == 'python':
            exit_code, stdout, stderr = self.run_command(['pytest', '--tb=short', '-q'], timeout=120)
            result["available"] = True
            result["passed"] = exit_code == 0
            result["raw_output"] = (stdout + stderr)[:2000]
            
            passed_match = re.search(r'(\d+)\s+passed', stdout + stderr)
            failed_match = re.search(r'(\d+)\s+failed', stdout + stderr)
            
            if passed_match:
                result["tests_passed"] = int(passed_match.group(1))
            if failed_match:
                result["tests_failed"] = int(failed_match.group(1))
            result["tests_run"] = result["tests_passed"] + result["tests_failed"]
        
        else:
            result["details"] = "Unknown project type for testing"
        
        return result
    
    def verify_files_exist(self, file_paths: List[str]) -> Dict[str, Any]:
        """验证文件是否存在"""
        result = {
            "total": len(file_paths),
            "exist": 0,
            "missing": [],
            "passed": False
        }
        
        for path in file_paths:
            full_path = self.project_root / path if not Path(path).is_absolute() else Path(path)
            if full_path.exists():
                result["exist"] += 1
            else:
                result["missing"].append(path)
        
        result["passed"] = result["exist"] == result["total"]
        return result
    
    def run_full_validation(self, files_to_verify: List[str] = None) -> Dict[str, Any]:
        """运行完整验证"""
        results = {}
        project_type = self.detect_project_type()
        
        if project_type == 'node':
            results['typescript'] = self.run_typescript_check()
            results['eslint'] = self.run_eslint_check()
        elif project_type == 'python':
            results['python_lint'] = self.run_python_lint()
            results['python_typecheck'] = self.run_python_typecheck()
        
        results['tests'] = self.run_tests()
        
        if files_to_verify:
            results['file_existence'] = self.verify_files_exist(files_to_verify)
        
        passed_count = sum(1 for r in results.values() if r.get('passed', False))
        total_count = sum(1 for r in results.values() if r.get('available', True))
        
        results['summary'] = {
            "passed": passed_count,
            "total": total_count,
            "pass_rate": passed_count / total_count if total_count > 0 else 0
        }
        
        return results


class QualityGate:
    """
    质量把关器 v1.0
    
    改进:
    1. 保留原有正则检查 (快速预检)
    2. 新增真实验证 (运行 lint/test/typecheck)
    3. 基于实际结果计算质量评分
    """
    
    CHECK_ITEMS = {
        QualityDimension.BOUNDARY: [
            {"name": "空值处理", "description": "检查是否处理了None/null值", "weight": 0.25},
            {"name": "异常捕获", "description": "检查是否有try-except错误处理", "weight": 0.25},
            {"name": "输入验证", "description": "检查是否验证了输入参数", "weight": 0.25},
            {"name": "边界条件", "description": "检查是否处理了边界情况", "weight": 0.25},
        ],
        QualityDimension.PROFESSIONALISM: [
            {"name": "命名规范", "description": "检查变量和函数命名是否规范", "weight": 0.25},
            {"name": "错误提示", "description": "检查错误提示是否友好易懂", "weight": 0.25},
            {"name": "代码注释", "description": "检查关键代码是否有注释", "weight": 0.25},
            {"name": "日志记录", "description": "检查是否有适当的日志输出", "weight": 0.25},
        ],
        QualityDimension.COMPLETENESS: [
            {"name": "文档齐全", "description": "检查是否有必要的文档说明", "weight": 0.25},
            {"name": "配置完整", "description": "检查配置文件是否完整", "weight": 0.25},
            {"name": "示例代码", "description": "检查是否提供了使用示例", "weight": 0.25},
            {"name": "测试覆盖", "description": "检查是否有测试用例", "weight": 0.25},
        ],
        QualityDimension.REAL_VALIDATION: [
            {"name": "Lint检查", "description": "运行代码风格检查", "weight": 0.3, "automated": True},
            {"name": "类型检查", "description": "运行类型检查", "weight": 0.25, "automated": True},
            {"name": "测试运行", "description": "运行测试用例", "weight": 0.3, "automated": True},
            {"name": "文件验证", "description": "验证文件存在性", "weight": 0.15, "automated": True},
        ]
    }
    
    PASS_THRESHOLD = 0.7
    
    def __init__(self, memory_dir: str = None, project_root: str = None):
        if memory_dir:
            self.memory_dir = Path(memory_dir)
        else:
            self.memory_dir = get_memory_dir()
        ensure_dir(self.memory_dir)
        self.quality_dir = self.memory_dir / 'quality'
        ensure_dir(self.quality_dir)
        
        self.validator = RealValidator(project_root)
        self.project_root = project_root
    
    def check_boundary(self, code_content: str, artifacts: Dict[str, Any] = None) -> DimensionResult:
        """边界处理维度检查"""
        result = DimensionResult(
            dimension=QualityDimension.BOUNDARY,
            name="边界处理"
        )
        
        items_config = self.CHECK_ITEMS[QualityDimension.BOUNDARY]
        
        for item_config in items_config:
            item = CheckItem(
                name=item_config["name"],
                description=item_config["description"]
            )
            
            if item_config["name"] == "空值处理":
                item.passed, item.score, item.details = self._check_null_handling(code_content)
            elif item_config["name"] == "异常捕获":
                item.passed, item.score, item.details = self._check_exception_handling(code_content)
            elif item_config["name"] == "输入验证":
                item.passed, item.score, item.details = self._check_input_validation(code_content)
            elif item_config["name"] == "边界条件":
                item.passed, item.score, item.details = self._check_boundary_conditions(code_content)
            
            result.items.append(item)
        
        result.total_score = sum(item.score for item in result.items) / len(result.items)
        result.passed = result.total_score >= self.PASS_THRESHOLD
        return result
    
    def _check_null_handling(self, code: str) -> Tuple[bool, float, str]:
        patterns = [
            r'if\s+\w+\s+is\s+None',
            r'if\s+\w+\s+is\s+not\s+None',
            r'if\s+not\s+\w+',
            r'\w+\s+or\s+["\']',
            r'\.get\(["\']\w+["\']\s*,',
            r'if\s+\w+\s*==\s*None',
        ]
        
        matches = 0
        for pattern in patterns:
            if re.search(pattern, code):
                matches += 1
        
        score = min(1.0, matches / 3)
        passed = score >= 0.5
        details = f"发现 {matches} 处空值处理模式"
        return passed, score, details
    
    def _check_exception_handling(self, code: str) -> Tuple[bool, float, str]:
        try_count = len(re.findall(r'\btry\s*:', code))
        except_count = len(re.findall(r'\bexcept\s*', code))
        raise_count = len(re.findall(r'\braise\s+', code))
        
        score = min(1.0, (try_count + except_count + raise_count) / 3)
        passed = try_count > 0 and except_count > 0
        details = f"try块: {try_count}, except块: {except_count}, raise: {raise_count}"
        return passed, score, details
    
    def _check_input_validation(self, code: str) -> Tuple[bool, float, str]:
        patterns = [
            r'assert\s+',
            r'if\s+not\s+isinstance',
            r'type\(\w+\)\s*==',
            r'isinstance\(',
            r'\.validate\(',
            r'if\s+len\(',
        ]
        
        matches = sum(1 for p in patterns if re.search(p, code))
        score = min(1.0, matches / 3)
        passed = matches >= 2
        details = f"发现 {matches} 处输入验证模式"
        return passed, score, details
    
    def _check_boundary_conditions(self, code: str) -> Tuple[bool, float, str]:
        patterns = [
            r'if\s+\w+\s*[<>=!]+\s*\d+',
            r'if\s+len\(\w+\)\s*[<>=!]',
            r'\.strip\(\)',
            r'\.lower\(\)',
            r'\.upper\(\)',
            r'if\s+\w+\s+in\s+',
        ]
        
        matches = sum(1 for p in patterns if re.search(p, code))
        score = min(1.0, matches / 3)
        passed = matches >= 1
        details = f"发现 {matches} 处边界条件处理"
        return passed, score, details
    
    def check_professionalism(self, code_content: str, artifacts: Dict[str, Any] = None) -> DimensionResult:
        """专业度维度检查"""
        result = DimensionResult(
            dimension=QualityDimension.PROFESSIONALISM,
            name="专业度"
        )
        
        items_config = self.CHECK_ITEMS[QualityDimension.PROFESSIONALISM]
        
        for item_config in items_config:
            item = CheckItem(
                name=item_config["name"],
                description=item_config["description"]
            )
            
            if item_config["name"] == "命名规范":
                item.passed, item.score, item.details = self._check_naming(code_content)
            elif item_config["name"] == "错误提示":
                item.passed, item.score, item.details = self._check_error_messages(code_content)
            elif item_config["name"] == "代码注释":
                item.passed, item.score, item.details = self._check_comments(code_content)
            elif item_config["name"] == "日志记录":
                item.passed, item.score, item.details = self._check_logging(code_content)
            
            result.items.append(item)
        
        result.total_score = sum(item.score for item in result.items) / len(result.items)
        result.passed = result.total_score >= self.PASS_THRESHOLD
        return result
    
    def _check_naming(self, code: str) -> Tuple[bool, float, str]:
        snake_case = re.findall(r'def\s+([a-z][a-z0-9_]*)\s*\(', code)
        camel_case = re.findall(r'def\s+([a-z][a-zA-Z0-9]*)\s*\(', code)
        bad_names = re.findall(r'def\s+([A-Z][a-zA-Z0-9]*)\s*\(', code)
        
        good_ratio = len(snake_case) / max(1, len(snake_case) + len(camel_case) + len(bad_names))
        score = max(0, good_ratio - len(bad_names) * 0.1)
        passed = len(bad_names) == 0 and good_ratio >= 0.8
        details = f"snake_case: {len(snake_case)}, camelCase: {len(camel_case)}, 不规范: {len(bad_names)}"
        return passed, score, details
    
    def _check_error_messages(self, code: str) -> Tuple[bool, float, str]:
        friendly_patterns = [
            r'["\'].*?请.*?["\']',
            r'["\'].*?无法.*?["\']',
            r'["\'].*?失败.*?["\']',
            r'["\'].*?错误.*?["\']',
            r'f["\'].*?\{.*?\}.*?["\']',
        ]
        
        matches = sum(1 for p in friendly_patterns if re.search(p, code))
        score = min(1.0, matches / 2)
        passed = matches >= 1
        details = f"发现 {matches} 处友好错误提示"
        return passed, score, details
    
    def _check_comments(self, code: str) -> Tuple[bool, float, str]:
        lines = code.split('\n')
        comment_lines = [l for l in lines if l.strip().startswith('#') or l.strip().startswith('"""') or l.strip().startswith("'''")]
        docstrings = len(re.findall(r'""".*?"""', code, re.DOTALL)) + len(re.findall(r"'''.*?'''", code, re.DOTALL))
        
        comment_ratio = len(comment_lines) / max(1, len(lines))
        score = min(1.0, comment_ratio * 5 + docstrings * 0.2)
        passed = comment_ratio >= 0.1 or docstrings >= 1
        details = f"注释行: {len(comment_lines)}, 文档字符串: {docstrings}, 注释率: {comment_ratio:.1%}"
        return passed, score, details
    
    def _check_logging(self, code: str) -> Tuple[bool, float, str]:
        log_patterns = [
            r'logger\.',
            r'logging\.',
            r'print\(',
            r'console\.log',
            r'log\.debug',
            r'log\.info',
            r'log\.warning',
            r'log\.error',
        ]
        
        matches = sum(1 for p in log_patterns if re.search(p, code))
        score = min(1.0, matches / 3)
        passed = matches >= 1
        details = f"发现 {matches} 处日志输出"
        return passed, score, details
    
    def check_completeness(self, artifacts: Dict[str, Any] = None) -> DimensionResult:
        """完整性维度检查"""
        result = DimensionResult(
            dimension=QualityDimension.COMPLETENESS,
            name="完整性"
        )
        
        artifacts = artifacts or {}
        items_config = self.CHECK_ITEMS[QualityDimension.COMPLETENESS]
        
        for item_config in items_config:
            item = CheckItem(
                name=item_config["name"],
                description=item_config["description"]
            )
            
            if item_config["name"] == "文档齐全":
                item.passed, item.score, item.details = self._check_documentation(artifacts)
            elif item_config["name"] == "配置完整":
                item.passed, item.score, item.details = self._check_config(artifacts)
            elif item_config["name"] == "示例代码":
                item.passed, item.score, item.details = self._check_examples(artifacts)
            elif item_config["name"] == "测试覆盖":
                item.passed, item.score, item.details = self._check_tests(artifacts)
            
            result.items.append(item)
        
        result.total_score = sum(item.score for item in result.items) / len(result.items)
        result.passed = result.total_score >= self.PASS_THRESHOLD
        return result
    
    def _check_documentation(self, artifacts: Dict) -> Tuple[bool, float, str]:
        docs = artifacts.get('documentation', [])
        readme = artifacts.get('readme', False)
        api_doc = artifacts.get('api_doc', False)
        
        score = 0.0
        if readme: score += 0.4
        if api_doc: score += 0.3
        if docs: score += min(0.3, len(docs) * 0.1)
        
        passed = score >= 0.4
        details = f"README: {readme}, API文档: {api_doc}, 其他文档: {len(docs)}"
        return passed, score, details
    
    def _check_config(self, artifacts: Dict) -> Tuple[bool, float, str]:
        config_files = artifacts.get('config_files', [])
        env_example = artifacts.get('env_example', False)
        
        score = min(1.0, len(config_files) * 0.3 + (0.4 if env_example else 0))
        passed = len(config_files) >= 1
        details = f"配置文件: {len(config_files)}, .env示例: {env_example}"
        return passed, score, details
    
    def _check_examples(self, artifacts: Dict) -> Tuple[bool, float, str]:
        examples = artifacts.get('examples', [])
        usage_guide = artifacts.get('usage_guide', False)
        
        score = min(1.0, len(examples) * 0.3 + (0.4 if usage_guide else 0))
        passed = len(examples) >= 1 or usage_guide
        details = f"示例代码: {len(examples)}, 使用指南: {usage_guide}"
        return passed, score, details
    
    def _check_tests(self, artifacts: Dict) -> Tuple[bool, float, str]:
        test_files = artifacts.get('test_files', [])
        test_coverage = artifacts.get('test_coverage', 0)
        
        score = min(1.0, len(test_files) * 0.3 + test_coverage * 0.5)
        passed = len(test_files) >= 1
        details = f"测试文件: {len(test_files)}, 覆盖率: {test_coverage:.0%}"
        return passed, score, details
    
    def check_real_validation(self, files_to_verify: List[str] = None) -> DimensionResult:
        """
        真实验证维度检查 - 运行实际的 lint/test/typecheck
        """
        result = DimensionResult(
            dimension=QualityDimension.REAL_VALIDATION,
            name="真实验证"
        )
        
        validation_results = self.validator.run_full_validation(files_to_verify)
        
        items_config = self.CHECK_ITEMS[QualityDimension.REAL_VALIDATION]
        
        for item_config in items_config:
            item = CheckItem(
                name=item_config["name"],
                description=item_config["description"],
                automated=True
            )
            
            if item_config["name"] == "Lint检查":
                lint_result = validation_results.get('eslint') or validation_results.get('python_lint', {})
                item.passed = lint_result.get('passed', False) if lint_result.get('available') else True
                item.score = 1.0 if item.passed else 0.5
                item.details = f"可用: {lint_result.get('available', False)}, 通过: {item.passed}"
                
            elif item_config["name"] == "类型检查":
                type_result = validation_results.get('typescript') or validation_results.get('python_typecheck', {})
                item.passed = type_result.get('passed', False) if type_result.get('available') else True
                item.score = 1.0 if item.passed else 0.5
                item.details = f"可用: {type_result.get('available', False)}, 通过: {item.passed}"
                
            elif item_config["name"] == "测试运行":
                test_result = validation_results.get('tests', {})
                item.passed = test_result.get('passed', False) if test_result.get('available') else True
                item.score = 1.0 if item.passed else 0.5
                item.details = f"通过: {test_result.get('tests_passed', 0)}/{test_result.get('tests_run', 0)}"
                
            elif item_config["name"] == "文件验证":
                file_result = validation_results.get('file_existence', {})
                if file_result:
                    item.passed = file_result.get('passed', True)
                    item.score = file_result.get('exist', 0) / max(1, file_result.get('total', 1))
                    item.details = f"存在: {file_result.get('exist', 0)}/{file_result.get('total', 0)}"
                else:
                    item.passed = True
                    item.score = 1.0
                    item.details = "无文件需要验证"
            
            result.items.append(item)
        
        result.total_score = sum(item.score for item in result.items) / len(result.items)
        result.passed = result.total_score >= self.PASS_THRESHOLD
        
        return result, validation_results
    
    def run_full_check(self, code_content: str = "", artifacts: Dict[str, Any] = None, 
                       session_id: str = None, files_to_verify: List[str] = None,
                       run_real_validation: bool = True) -> QualityReport:
        """执行完整的质量检查"""
        session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        
        input_text = f"quality_check:{session_id} code_len:{len(code_content)} files:{len(files_to_verify or [])}"
        
        report = QualityReport(
            session_id=session_id,
            timestamp=datetime.now().isoformat()
        )
        
        report.dimensions.append(self.check_boundary(code_content, artifacts))
        report.dimensions.append(self.check_professionalism(code_content, artifacts))
        report.dimensions.append(self.check_completeness(artifacts))
        
        if run_real_validation:
            real_result, validation_results = self.check_real_validation(files_to_verify)
            report.dimensions.append(real_result)
            report.real_validation_results = validation_results
        
        report.overall_score = sum(d.total_score for d in report.dimensions) / len(report.dimensions)
        report.passed = report.overall_score >= self.PASS_THRESHOLD
        
        report.recommendations = self._generate_recommendations(report)
        
        self._save_report(report)
        
        output_text = f"quality_report:{session_id} score:{report.overall_score:.2f} passed:{report.passed}"
        record_session_tokens(
            session_id, 
            input_text, 
            output_text, 
            "quality_check"
        )
        
        return report
    
    def _generate_recommendations(self, report: QualityReport) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        for dim in report.dimensions:
            if not dim.passed:
                failed_items = [item for item in dim.items if not item.passed]
                for item in failed_items:
                    recommendations.append(f"[{dim.name}] {item.name}: {item.details}")
        
        if report.real_validation_results:
            summary = report.real_validation_results.get('summary', {})
            if summary.get('pass_rate', 1) < 0.8:
                recommendations.append(f"真实验证通过率: {summary.get('pass_rate', 0):.0%}，建议修复失败项")
        
        if not recommendations:
            recommendations.append("✅ 所有质量检查项均已通过")
        
        return recommendations
    
    def _save_report(self, report: QualityReport):
        """保存质量报告"""
        report_path = self.quality_dir / f"{report.session_id}_quality.json"
        
        report_dict = {
            "session_id": report.session_id,
            "timestamp": report.timestamp,
            "overall_score": report.overall_score,
            "passed": report.passed,
            "retry_count": report.retry_count,
            "recommendations": report.recommendations,
            "real_validation_summary": report.real_validation_results.get('summary', {}) if report.real_validation_results else {},
            "dimensions": [
                {
                    "dimension": d.dimension.value,
                    "name": d.name,
                    "total_score": d.total_score,
                    "passed": d.passed,
                    "items": [
                        {
                            "name": i.name,
                            "description": i.description,
                            "passed": i.passed,
                            "score": i.score,
                            "details": i.details,
                            "automated": i.automated
                        }
                        for i in d.items
                    ]
                }
                for d in report.dimensions
            ]
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, ensure_ascii=False, indent=2)
    
    def can_retry(self, report: QualityReport) -> bool:
        """检查是否可以重试"""
        return report.retry_count < report.max_retries
    
    def increment_retry(self, report: QualityReport) -> QualityReport:
        """增加重试计数"""
        report.retry_count += 1
        self._save_report(report)
        return report
    
    def get_summary(self, report: QualityReport) -> str:
        """获取质量报告摘要"""
        lines = [
            f"📊 质量检查报告 - {report.session_id}",
            f"{'='*50}",
            f"总体得分: {report.overall_score:.1%} {'✅ 通过' if report.passed else '❌ 未通过'}",
            f"重试次数: {report.retry_count}/{report.max_retries}",
            ""
        ]
        
        for dim in report.dimensions:
            status = "✅" if dim.passed else "❌"
            lines.append(f"{status} {dim.name}: {dim.total_score:.1%}")
            for item in dim.items:
                item_status = "✓" if item.passed else "✗"
                lines.append(f"   {item_status} {item.name}: {item.details}")
        
        lines.append("")
        lines.append("📝 改进建议:")
        for rec in report.recommendations:
            lines.append(f"   - {rec}")
        
        return "\n".join(lines)
    
    def get_research_directive(self, session_id: str) -> Dict[str, Any]:
        """获取研究指令 - 供 Agent 联网查找解决方案"""
        report = self._load_report(session_id)
        
        if not report:
            return {"error": f"No report found for session {session_id}"}
        
        failed_items = []
        for dim in report.get("dimensions", []):
            for item in dim.get("items", []):
                if not item.get("passed", True):
                    failed_items.append({
                        "dimension": dim.get("name", ""),
                        "name": item.get("name", ""),
                        "details": item.get("details", "")
                    })
        
        return {
            "session_id": session_id,
            "instruction": """
# 验证研究指令

## 目标
联网查找优质解决方案，修复验证失败项。

## 研究来源
1. GitHub 开源项目
2. 官方文档
3. Stack Overflow
4. 技术博客

## 研究内容
根据失败项，查找:
- 错误修复方案
- 最佳实践
- 代码示例

## 输出要求
整合归纳找到的内容，生成:
1. 修复策略
2. 具体修复步骤
3. 预期结果
""",
            "failed_items": failed_items,
            "quality_score": report.get("overall_score", 0)
        }
    
    def _load_report(self, session_id: str) -> Optional[Dict]:
        """加载质量报告"""
        report_path = self.quality_dir / f"{session_id}_quality.json"
        if not report_path.exists():
            return None
        with open(report_path, 'r', encoding='utf-8') as f:
            return json.load(f)
