import argparse
import os
from pathlib import Path
import sys

def suggest_fix(file_path: str, line_no: int, old_path: str):
    file_path = Path(file_path).resolve()
    target_path = Path(old_path)
    
    if not target_path.exists():
        # Try to check if it's an absolute path that just happens to be missing locally
        # or if it's a relative path that was resolved incorrectly.
        print(f"⚠️ Target path does not exist: {old_path}")
        if not target_path.is_absolute():
             print("   (Path is relative, maybe already fixed?)")
             return

    try:
        # Calculate relative path using os.path.relpath which handles '..' correctly
        # relative_to() in pathlib is strict and doesn't do '..' for siblings
        rel_path_str = os.path.relpath(target_path, file_path.parent)
        rel_path = Path(rel_path_str)
        
        parts = rel_path.parts
        parent_count = 0
        remaining_parts = []
        
        for part in parts:
            if part == '..':
                parent_count += 1
            elif part == '.':
                continue
            else:
                remaining_parts.append(part)
        
        if parent_count > 0:
            # parents[0] is directory containing file
            # parents[1] is parent of that directory
            # rel '..' means parent of directory containing file -> parents[1]
            # rel '../..' -> parents[2]
            # So index matches parent_count!
            # Wait. 
            # file: /a/b/c.py. parent: /a/b.
            # target: /a. rel: ..
            # parents[0]: /a/b.
            # parents[1]: /a.
            # So index 1 is correct for '..'.
            base = f'Path(__file__).resolve().parents[{parent_count}]'
        else:
            # parent_count 0 means in same directory or subdirectory
            base = f'Path(__file__).resolve().parent'
            
        if remaining_parts:
            joined = ' / '.join([f"'{p}'" for p in remaining_parts])
            code = f"{base} / {joined}"
        else:
            code = base
            
        print(f"✅ Suggestion for {file_path.name}:{line_no}")
        print(f"   Original: \"{old_path}\"")
        print(f"   Fix:      {code}")

    except ValueError:
        print(f"⚠️ Could not calculate relative path from {file_path} to {target_path}")

    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    parser = argparse.ArgumentParser(description="Suggest fixes for hardcoded paths")
    parser.add_argument("--file", required=True, help="File to fix")
    parser.add_argument("--line", type=int, help="Line number (optional)")
    parser.add_argument("--path", help="The hardcoded path string (optional)")
    args = parser.parse_args()

    if args.path and args.line:
        suggest_fix(args.file, args.line, args.path)
    else:
        print("Please provide --line and --path for specific suggestion.")

if __name__ == "__main__":
    main()
