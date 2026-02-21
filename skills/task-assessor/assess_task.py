import os
import sys
import yaml
import argparse
import json

def assess_task(task_desc, task_type):
    """
    Assesses task complexity based on task description and type.
    """
    skill_dir = os.path.dirname(os.path.abspath(__file__))
    methods_dir = os.path.join(skill_dir, "methods")
    if not os.path.exists(methods_dir):
        os.makedirs(methods_dir)
        
    method_file = os.path.join(methods_dir, f"{task_type}.yaml")
    
    if not os.path.exists(method_file):
        print(f"[REQUEST_SEARCH: best practices for assessing complexity of '{task_type}' tasks]")
        print("Waiting for Agent to provide assessment method...")
        return
    
    # Simple logic based on length/keywords for now as placeholder
    # In real use, this would be more sophisticated.
    complexity_score = len(task_desc) / 100  # Mock score
    level = "L0"
    if complexity_score > 3:
        level = "L1"
    if complexity_score > 6:
        level = "L2"
        
    result = {
        "score": round(complexity_score, 2),
        "level": level,
        "strategy": "Direct Execution" if level == "L0" else "Spiral Loop"
    }
    
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--desc", help="Description of the task", required=True)
    parser.add_argument("--type", help="Type of task (e.g., refactor, feature, bugfix)", required=True)
    args = parser.parse_args()
    
    assess_task(args.desc, args.type)
