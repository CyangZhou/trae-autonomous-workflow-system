#!/usr/bin/env python3
"""
Trae Skill Utilities

Helper functions for creating, validating, and installing Trae skills.
"""

import os
import sys
import shutil
import argparse
from pathlib import Path

TRAE_SKILLS_ROOT = Path(".trae/skills")

def validate_trae_skill(skill_path: str) -> bool:
    """
    Validate that a directory is a valid Trae skill.
    
    Args:
        skill_path: Path to the skill directory.
        
    Returns:
        True if valid, False otherwise.
    """
    path = Path(skill_path)
    if not path.exists() or not path.is_dir():
        print(f"❌ Error: {skill_path} is not a valid directory.")
        return False
        
    skill_md = path / "SKILL.md"
    if not skill_md.exists():
        print(f"❌ Error: Missing SKILL.md in {skill_path}")
        return False
        
    # Check frontmatter
    try:
        content = skill_md.read_text(encoding="utf-8")
        if not content.startswith("---"):
            print("❌ Error: SKILL.md must start with YAML frontmatter (---)")
            return False
    except Exception as e:
        print(f"❌ Error reading SKILL.md: {e}")
        return False
        
    print(f"✅ Valid Trae skill: {path.name}")
    return True

def create_skill(name: str, description: str, output_dir: str = None):
    """
    Scaffold a new Trae skill.
    
    Args:
        name: Name of the skill (kebab-case).
        description: Short description.
        output_dir: Directory to create the skill in (default: .trae/skills/<name>).
    """
    if output_dir:
        skill_dir = Path(output_dir)
    else:
        skill_dir = TRAE_SKILLS_ROOT / name
        
    if skill_dir.exists():
        print(f"❌ Error: Skill directory already exists: {skill_dir}")
        return False
        
    try:
        skill_dir.mkdir(parents=True, exist_ok=True)
        
        # Create SKILL.md
        skill_md_content = f"""---
name: {name}
description: {description}
---

# {name.replace('-', ' ').title()}

{description}

## Usage

Describe how to use this skill here.
"""
        (skill_dir / "SKILL.md").write_text(skill_md_content, encoding="utf-8")
        
        # Create README.md
        (skill_dir / "README.md").write_text(f"# {name}\n\n{description}", encoding="utf-8")
        
        # Create requirements.txt
        (skill_dir / "requirements.txt").touch()
        
        # Create main.py
        main_py_content = """#!/usr/bin/env python3
import sys

def main():
    print("Hello from Trae Skill!")
    
if __name__ == "__main__":
    main()
"""
        (skill_dir / "main.py").write_text(main_py_content, encoding="utf-8")
        
        print(f"✅ Skill created successfully at: {skill_dir}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating skill: {e}")
        return False

def install_skill(source_path: str, force: bool = False):
    """
    Install a skill into .trae/skills.
    
    Args:
        source_path: Path to the source skill directory.
        force: Overwrite if exists.
    """
    source = Path(source_path)
    if not validate_trae_skill(str(source)):
        return False
        
    skill_name = source.name
    dest = TRAE_SKILLS_ROOT / skill_name
    
    if dest.exists():
        if force:
            shutil.rmtree(dest)
        else:
            print(f"❌ Error: Skill {skill_name} already installed. Use --force to overwrite.")
            return False
            
    try:
        shutil.copytree(source, dest)
        print(f"✅ Skill installed to: {dest}")
        return True
    except Exception as e:
        print(f"❌ Error installing skill: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Trae Skill Utilities")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new skill")
    create_parser.add_argument("name", help="Skill name (kebab-case)")
    create_parser.add_argument("description", help="Skill description")
    create_parser.add_argument("--output", "-o", help="Output directory")
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate a skill")
    validate_parser.add_argument("path", help="Path to skill directory")
    
    # Install command
    install_parser = subparsers.add_parser("install", help="Install a skill")
    install_parser.add_argument("path", help="Path to source skill directory")
    install_parser.add_argument("--force", "-f", action="store_true", help="Overwrite existing skill")
    
    args = parser.parse_args()
    
    if args.command == "create":
        create_skill(args.name, args.description, args.output)
    elif args.command == "validate":
        validate_trae_skill(args.path)
    elif args.command == "install":
        install_skill(args.path, args.force)
    else:
        parser.print_help()
        
if __name__ == "__main__":
    main()
