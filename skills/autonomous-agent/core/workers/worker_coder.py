from .worker_base import BaseWorker
import time
import os
from pathlib import Path
import ast

class CoderWorker(BaseWorker):
    def __init__(self):
        super().__init__(worker_type="backend-architect")

    def execute(self, payload: dict) -> dict:
        action = payload.get("action")
        file_path = payload.get("file_path")
        content = payload.get("content")
        
        self.logger.info(f"Coding Action: {action} on {file_path}")
        
        if not file_path:
            raise ValueError("Missing file_path")
            
        p = Path(file_path).resolve()
        
        # Security check: Ensure we are inside the project (commented out for flexibility in demo)
        # project_root = Path(os.getcwd()).resolve()
        # if not str(p).startswith(str(project_root)):
        #    raise ValueError(f"Access denied: {file_path} is outside project root")

        if action == "write":
            if content is None:
                raise ValueError("Missing content for write action")
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding='utf-8')
            return {"status": "success", "message": f"File written: {file_path}", "size": len(content)}
            
        elif action == "read":
            if not p.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            data = p.read_text(encoding='utf-8')
            return {"status": "success", "content": data, "size": len(data)}
            
        elif action == "analyze":
            if not p.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            try:
                data = p.read_text(encoding='utf-8')
                tree = ast.parse(data)
                
                analysis = {
                    "classes": [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)],
                    "functions": [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)],
                    "imports": [alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names] + 
                               [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module]
                }
                return {"status": "success", "analysis": analysis}
            except Exception as e:
                return {"status": "error", "message": f"Analysis failed: {str(e)}"}
                
        else:
            raise ValueError(f"Unknown action: {action}")

if __name__ == "__main__":
    worker = CoderWorker()
    worker.start()
