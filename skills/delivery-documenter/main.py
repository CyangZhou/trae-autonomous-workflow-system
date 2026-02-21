import argparse
import sys
import json
from pathlib import Path

# Add current directory to sys.path to allow imports from core
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

try:
    from core.delivery_doc import DeliveryDocGenerator
except ImportError:
    try:
        from .core.delivery_doc import DeliveryDocGenerator
    except ImportError:
        sys.path.append(str(current_dir / "core"))
        from delivery_doc import DeliveryDocGenerator

def main():
    parser = argparse.ArgumentParser(description="Delivery Documenter Skill")
    parser.add_argument("task_description", help="Description of the task")
    parser.add_argument("--session-id", help="Session ID", required=True)
    parser.add_argument("--output-dir", help="Directory to save the delivery document", default=None)
    parser.add_argument("--execution-result", help="JSON string of execution result", default=None)
    parser.add_argument("--quality-report", help="JSON string of quality report", default=None)
    parser.add_argument("--task-type", help="Type of the task", default="general")
    
    args = parser.parse_args()
    
    try:
        execution_result = json.loads(args.execution_result) if args.execution_result else None
        quality_report = json.loads(args.quality_report) if args.quality_report else None
        
        generator = DeliveryDocGenerator(output_dir=args.output_dir)
        
        doc = generator.generate(
            session_id=args.session_id,
            task_description=args.task_description,
            execution_result=execution_result,
            quality_report=quality_report,
            task_type=args.task_type
        )
        
        print(generator.get_summary(doc))
        print(f"\nDocument saved to: {generator.output_dir}/{doc.session_id}_delivery.md")
        
    except Exception as e:
        print(f"Error generating delivery document: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
