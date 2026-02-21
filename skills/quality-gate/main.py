import argparse
import sys
import json
from pathlib import Path

# Add current directory to sys.path to allow imports from core
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

try:
    from core.quality_gate import QualityGate
except ImportError:
    try:
        from .core.quality_gate import QualityGate
    except ImportError:
        sys.path.append(str(current_dir / "core"))
        from quality_gate import QualityGate

def main():
    parser = argparse.ArgumentParser(description="Quality Gate Skill")
    parser.add_argument("path", help="Path to file or directory to check")
    parser.add_argument("--code", help="Code content to check (if path is not a file)", default="")
    parser.add_argument("--session-id", help="Session ID", default=None)
    parser.add_argument("--artifacts", help="JSON string of artifacts metadata", default="{}")
    
    args = parser.parse_args()
    
    try:
        gate = QualityGate(project_root=str(Path.cwd()))
        
        files_to_verify = []
        path = Path(args.path)
        if path.is_file():
            files_to_verify.append(str(path))
            if not args.code:
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        args.code = f.read()
                except:
                    pass
        elif path.is_dir():
            # If directory, maybe verify all files? For now just passed path
            pass
            
        artifacts = json.loads(args.artifacts)
        
        report = gate.run_full_check(
            code_content=args.code,
            artifacts=artifacts,
            session_id=args.session_id,
            files_to_verify=files_to_verify
        )
        
        print(gate.get_summary(report))
        
        # Also output JSON result for parsing
        print("\n--- JSON RESULT ---")
        result = {
            "session_id": report.session_id,
            "passed": report.passed,
            "overall_score": report.overall_score,
            "recommendations": report.recommendations
        }
        print(json.dumps(result, ensure_ascii=False))
        
        if not report.passed:
            sys.exit(1)
            
    except Exception as e:
        print(f"Error running quality gate: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
