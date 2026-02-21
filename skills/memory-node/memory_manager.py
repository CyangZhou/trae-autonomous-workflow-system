import os
import sys
import yaml
import argparse
import json

def get_skill_dir(topic):
    skill_name = f"mem-{topic}"
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), skill_name)

def write_memory(topic, content):
    """
    Writes memory content to a skill-like structure for LLM discovery.
    """
    skill_dir = get_skill_dir(topic)
    
    if not os.path.exists(skill_dir):
        os.makedirs(skill_dir)
    
    # Generate summary (first 100 chars or first line)
    lines = content.strip().split('\n')
    summary = lines[0] if lines else "No content"
    if len(summary) > 100:
        summary = summary[:97] + "..."
    
    # Create skill.yaml (avoiding SKILL.md as per user request)
    skill_data = {
        "name": f"mem-{topic}",
        "description": f"MEMORY: {summary}",
        "version": "1.0.0",
        "commands": [
            {
                "name": "read",
                "description": "Read full memory content",
                "arguments": []
            }
        ]
    }
    
    with open(os.path.join(skill_dir, "skill.yaml"), "w", encoding="utf-8") as f:
        yaml.dump(skill_data, f, allow_unicode=True)
    
    # Write full content to README.md
    with open(os.path.join(skill_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write(content)
        
    print(f"Memory written to {skill_dir}")

def read_memory(topic):
    skill_dir = get_skill_dir(topic)
    readme_path = os.path.join(skill_dir, "README.md")
    
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            print(f.read())
    else:
        print(f"Memory for topic '{topic}' not found at {readme_path}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Write command
    write_parser = subparsers.add_parser("write")
    write_parser.add_argument("--topic", help="Topic of the memory", required=True)
    write_parser.add_argument("--content", help="Content of the memory", required=True)
    
    # Read command
    read_parser = subparsers.add_parser("read")
    read_parser.add_argument("--topic", help="Topic of the memory", required=True)
    
    # List command
    list_parser = subparsers.add_parser("list")
    
    args = parser.parse_args()
    
    if args.command == "write":
        write_memory(args.topic, args.content)
    elif args.command == "read":
        read_memory(args.topic)
    elif args.command == "list":
        # List all memory topics by scanning .trae/skills/mem-*
        skills_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        mem_skills = [d for d in os.listdir(skills_root) if d.startswith("mem-") and os.path.isdir(os.path.join(skills_root, d))]
        print(json.dumps(mem_skills, indent=2))
