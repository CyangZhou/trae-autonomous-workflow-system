import argparse
import sys
import os

# Add parent directory to path to import core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.memory import SpiralMemory
from core.solver import SpiralLoopSolver
from core.checkpoint import CheckpointManager
from core.specs import ProjectSpecChecker

def handle_memory(args):
    mem = SpiralMemory()
    if args.action == 'add':
        nid = mem.add_instant_node(args.content, metadata={'source': 'cli'})
        print(f"Added node: {nid}")
    elif args.action == 'list':
        nodes = mem.get_recent_nodes()
        print(json.dumps(nodes, ensure_ascii=False, indent=2))

def handle_checkpoint(args):
    mem = SpiralMemory()
    ckpt_mgr = CheckpointManager(mem)
    if args.action == 'create':
        cid = ckpt_mgr.create_checkpoint(args.desc)
        print(f"Created checkpoint: {cid}")
    elif args.action == 'restore':
        res = ckpt_mgr.restore_from_checkpoint(args.id)
        print(json.dumps(res, ensure_ascii=False, indent=2))
    elif args.action == 'list':
        ckpts = ckpt_mgr.list_checkpoints()
        print(json.dumps(ckpts, ensure_ascii=False, indent=2))

def handle_solver(args):
    solver = SpiralLoopSolver()
    if args.action == 'detect':
        res = solver.detect_interruption(args.state)
        print(f"Detection result: {res}")
    elif args.action == 'jump':
        res = solver.node_jump(args.state, args.strategy)
        print(json.dumps(res, ensure_ascii=False, indent=2))

def handle_specs(args):
    checker = ProjectSpecChecker()
    if args.action == 'check_doc':
        res = checker.check_doc_structure(args.file)
        print(json.dumps(res, ensure_ascii=False, indent=2))
    elif args.action == 'check_org':
        res = checker.check_file_org(args.dir)
        print(json.dumps(res, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Spiral Loop System CLI")
    subparsers = parser.add_subparsers(dest="command")

    # Memory
    mem_parser = subparsers.add_parser('memory')
    mem_parser.add_argument('--action', choices=['add', 'list'], required=True)
    mem_parser.add_argument('--content', help="Content for node")
    mem_parser.set_defaults(func=handle_memory)

    # Checkpoint
    ckpt_parser = subparsers.add_parser('checkpoint')
    ckpt_parser.add_argument('--action', choices=['create', 'restore', 'list'], required=True)
    ckpt_parser.add_argument('--desc', help="Description for checkpoint")
    ckpt_parser.add_argument('--id', help="Checkpoint ID for restore")
    ckpt_parser.set_defaults(func=handle_checkpoint)

    # Solver
    sol_parser = subparsers.add_parser('solver')
    sol_parser.add_argument('--action', choices=['detect', 'jump'], required=True)
    sol_parser.add_argument('--state', help="Current state content", required=True)
    sol_parser.add_argument('--strategy', choices=['spiral', 'lateral', 'quantum'], default='spiral')
    sol_parser.set_defaults(func=handle_solver)

    # Specs
    spec_parser = subparsers.add_parser('specs')
    spec_parser.add_argument('--action', choices=['check_doc', 'check_org'], required=True)
    spec_parser.add_argument('--file', help="File to check")
    spec_parser.add_argument('--dir', help="Directory to check")
    spec_parser.set_defaults(func=handle_specs)

    args = parser.parse_args()
    if hasattr(args, 'func'):
        import json
        args.func(args)
    else:
        parser.print_help()
