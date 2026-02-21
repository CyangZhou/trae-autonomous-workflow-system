import os
import re
import argparse
import ast
from pathlib import Path
from typing import List, Dict, Any

class PathScanner:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir).resolve()
        # Regex for finding quoted strings in non-code files
        self.quoted_string_pattern = re.compile(r'([\'\"])((?:/[^/]+/[^/]+|[a-zA-Z]:\\[^\\]+)(?:/[^/]+)*)\1')
        # Regex for validating if a string is an absolute path (no quotes)
        self.abs_path_validator = re.compile(r'^(?:/[^/]+/[^/]+|[a-zA-Z]:\\[^\\]+)(?:/[^/]+)*$')
        self.ignore_dirs = {'.git', '.trae', '__pycache__', 'node_modules', 'venv', '.venv', 'temp', 'tmp'}

    def scan(self) -> List[Dict[str, Any]]:
        results = []
        for file_path in self.root_dir.rglob('*'):
            if file_path.is_dir():
                continue
                
            parts = file_path.parts
            if any(p in parts for p in self.ignore_dirs):
                # print(f"DEBUG: Ignoring {file_path}")
                continue
            
            # Skip binary files or missing files
            try:
                content = file_path.read_text(encoding='utf-8')
            except (UnicodeDecodeError, FileNotFoundError, PermissionError):
                continue

            matches = []
            
            # 1. AST Analysis for Python files (more accurate)
            if file_path.suffix == '.py':
                matches.extend(self._scan_python_ast(content, file_path))
            
            # 2. Regex fallback for strings in Python (comments, f-strings) or other files
            # Note: AST handles string literals, but regex catches things in comments or non-code
            # For simplicity in this v1, we rely on Regex for non-python and AST for python
            if file_path.suffix != '.py':
                for match in self.quoted_string_pattern.finditer(content):
                    path_str = match.group(2) # Group 2 is the content inside quotes
                    # Filter out short paths or system paths that are likely valid
                    if len(path_str) > 10 and self._is_suspicious(path_str):
                         matches.append({
                            'line': content[:match.start()].count('\n') + 1,
                            'path': path_str,
                            'type': 'regex'
                        })

            if matches:
                results.append({
                    'file': str(file_path.relative_to(self.root_dir)),
                    'matches': matches
                })
        
        return results

    def _scan_python_ast(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        matches = []
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                # print(f"DEBUG: Node {type(node)}")
                if isinstance(node, (ast.Constant, ast.Str)): # Handle both Py3.8+ and older
                    val = node.value if isinstance(node, ast.Constant) else node.s
                    if isinstance(val, str):
                        # print(f"DEBUG: String found: {val}")
                        if self._is_suspicious(val):
                            # print(f"DEBUG: Suspicious! {val}")
                            matches.append({
                                'line': node.lineno,
                                'path': val,
                                'type': 'ast'
                            })
                # Handle f-strings (JoinedStr) - harder to detect exact absolute path if dynamic
        except SyntaxError:
            pass # Skip malformed files
        return matches

    def _is_suspicious(self, text: str) -> bool:
        if len(text) < 10:
            return False
        if any(c in text for c in '<>:"|?*%;'): # Invalid path chars (Windows/Unix mixed) + URL encoding
            return False
        # Check if it looks like an absolute path
        return bool(self.abs_path_validator.search(text))

def main():
    parser = argparse.ArgumentParser(description="Scan for hardcoded absolute paths")
    parser.add_argument("--root", default=".", help="Root directory to scan")
    args = parser.parse_args()

    scanner = PathScanner(args.root)
    print(f"Scanning {scanner.root_dir} for hardcoded paths...")
    results = scanner.scan()

    if not results:
        print("✅ No suspicious hardcoded paths found.")
    else:
        print(f"⚠️ Found {len(results)} files with hardcoded paths:")
        for res in results:
            print(f"\n📄 {res['file']}")
            for m in res['matches']:
                print(f"  L{m['line']}: {m['path']}")

if __name__ == "__main__":
    main()
