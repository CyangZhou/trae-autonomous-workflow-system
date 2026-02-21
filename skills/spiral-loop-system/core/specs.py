import os
import re

class ProjectSpecChecker:
    def __init__(self, root_dir: str = "."):
        self.root_dir = root_dir

    def check_doc_structure(self, filepath: str) -> dict:
        """检查文档是否符合 Markdown 层级结构"""
        issues = []
        if not filepath.endswith('.md'):
            return {"valid": False, "issues": ["Not a Markdown file"]}
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if re.search(r'<SYS_KERNEL_OPTIMIZED\b', content):
                if "<META>" not in content:
                    issues.append("Missing META section.")
                if "<PROTOCOLS>" not in content:
                    issues.append("Missing PROTOCOLS section.")
                return {"valid": not issues, "issues": issues}
            
            # Check for headers hierarchy
            headers = re.findall(r'^(#+)\s', content, re.MULTILINE)
            if not headers:
                issues.append("No headers found.")
            
            # Check for clear links (simplistic check)
            links = re.findall(r'\[(.*?)\]\((.*?)\)', content)
            for text, url in links:
                if not text.strip():
                    issues.append(f"Empty link text for url: {url}")
            
            return {"valid": not issues, "issues": issues}
        except Exception as e:
            return {"valid": False, "issues": [str(e)]}

    def check_file_org(self, module_dir: str) -> dict:
        """检查文件组织规范 (同类模块集中)"""
        # This is a heuristic check.
        # E.g., verify that Python files are in src or scripts folders, etc.
        issues = []
        for root, dirs, files in os.walk(module_dir):
            for file in files:
                if file.endswith('.py') and 'scripts' not in root and 'src' not in root and 'core' not in root:
                    issues.append(f"Python file {file} found outside structured folders (scripts/src/core).")
        return {"valid": not issues, "issues": issues}

    def check_progress_doc(self) -> dict:
        """检查是否有进度管理文档"""
        # Look for files with "progress" or "plan" in name
        found = False
        for root, dirs, files in os.walk(self.root_dir):
            for file in files:
                if "progress" in file.lower() or "plan" in file.lower():
                    found = True
                    break
        if not found:
            return {"valid": False, "issues": ["No progress or plan document found."]}
        return {"valid": True, "issues": []}
