import argparse
import sys
import json
from pathlib import Path

# Add current directory to sys.path to allow imports from core
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

try:
    from core.enhanced_decomposer import EnhancedAtomicTaskDecomposer
except ImportError:
    # If running from root, try different import
    try:
        from .core.enhanced_decomposer import EnhancedAtomicTaskDecomposer
    except ImportError:
        # Fallback for direct execution
        sys.path.append(str(current_dir / "core"))
        from enhanced_decomposer import EnhancedAtomicTaskDecomposer

def main():
    parser = argparse.ArgumentParser(description="Task Decomposer Skill")
    parser.add_argument("task_description", help="The description of the task to decompose")
    parser.add_argument("--output-dir", help="Directory to save the task document", default=None)
    parser.add_argument("--session-id", help="Session ID for the task", default=None)
    
    args = parser.parse_args()
    
    try:
        decomposer = EnhancedAtomicTaskDecomposer(output_dir=args.output_dir)
        doc = decomposer.decompose(args.task_description, session_id=args.session_id)
        
        # Output the result as JSON to stdout
        result = {
            "session_id": doc.session_id,
            "total_tasks": doc.total_tasks,
            "execution_order": doc.execution_order,
            "decomposition_strategy": doc.decomposition_strategy,
            "tasks": [
                {
                    "task_id": t.task_id,
                    "name": t.name,
                    "description": t.description,
                    "agent_type": t.agent_type,
                    "dependencies": t.dependencies
                }
                for t in doc.tasks
            ]
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(f"Error decomposing task: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
