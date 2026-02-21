#!/usr/bin/env python3
"""
Autonomous Agent CLI Entry Point
"""
import sys
import os
import argparse
from pathlib import Path

# Add core path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.kernel import UnifiedKernel
from core.paths import init_runtime_directories

def main():
    parser = argparse.ArgumentParser(description='Autonomous Agent v2.0 - Closed Loop Edition')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Init
    parser_init = subparsers.add_parser('init', help='Initialize kernel')
    
    # Analyze
    parser_analyze = subparsers.add_parser('analyze', help='Analyze task')
    parser_analyze.add_argument('task', type=str, help='Task description')
    
    # Scenario
    parser_scenario = subparsers.add_parser('scenario', help='Get scenario info')
    parser_scenario.add_argument('task', type=str, nargs='?', help='Task description (optional)')
    
    # Quality
    parser_quality = subparsers.add_parser('quality', help='Run quality check')
    parser_quality.add_argument('--code', type=str, default='', help='Code content')
    parser_quality.add_argument('--artifacts', type=str, help='Artifacts JSON')
    parser_quality.add_argument('--session', type=str, help='Session ID')
    parser_quality.add_argument('--files', type=str, help='Files to verify (comma-separated or JSON)')
    parser_quality.add_argument('--no-real-validation', action='store_true', help='Skip real validation')
    
    parser_quality_report = subparsers.add_parser('quality-report', help='Get quality report')
    parser_quality_report.add_argument('--session', type=str, help='Session ID')
    
    # Skills
    parser_discover = subparsers.add_parser('discover', help='Discover skills')
    parser_discover.add_argument('task', type=str, help='Task description')
    parser_discover.add_argument('--type', type=str, help='Task type')
    
    parser_list_skills = subparsers.add_parser('list-skills', help='List available skills')
    
    # Tracking
    parser_track_file = subparsers.add_parser('track-file', help='Track file change')
    parser_track_file.add_argument('--path', type=str, required=True, help='File path')
    parser_track_file.add_argument('--action', type=str, default='create', choices=['create', 'modify', 'delete'], help='Action type')
    parser_track_file.add_argument('--diff', type=str, default='', help='Diff summary')
    
    parser_track_command = subparsers.add_parser('track-command', help='Track command execution')
    parser_track_command.add_argument('--cmd', type=str, required=True, help='Command')
    parser_track_command.add_argument('--exit', type=int, required=True, help='Exit code')
    parser_track_command.add_argument('--output', type=str, default='', help='Output summary')
    parser_track_command.add_argument('--error', type=str, default='', help='Error message')
    
    parser_track_test = subparsers.add_parser('track-test', help='Track test result')
    parser_track_test.add_argument('--name', type=str, required=True, help='Test name')
    parser_track_test.add_argument('--passed', type=lambda x: x.lower() == 'true', required=True, help='Passed (true/false)')
    parser_track_test.add_argument('--details', type=str, default='', help='Details')
    parser_track_test.add_argument('--error-msg', type=str, default='', help='Error message')
    
    parser_track_verification = subparsers.add_parser('track-verification', help='Track verification check')
    parser_track_verification.add_argument('--name', type=str, required=True, help='Check name')
    parser_track_verification.add_argument('--passed', type=lambda x: x.lower() == 'true', required=True, help='Passed (true/false)')
    parser_track_verification.add_argument('--details', type=str, default='', help='Details')
    parser_track_verification.add_argument('--manual', action='store_true', help='Manual check')
    
    parser_add_finding = subparsers.add_parser('add-finding', help='Add key finding')
    parser_add_finding.add_argument('--finding', type=str, required=True, help='Finding text')
    
    parser_tracker_summary = subparsers.add_parser('tracker-summary', help='Get tracker summary')
    parser_tracker_summary.add_argument('--session', type=str, help='Session ID')
    
    # Delivery
    parser_delivery = subparsers.add_parser('delivery', help='Generate delivery document')
    parser_delivery.add_argument('--session', type=str, help='Session ID')
    parser_delivery.add_argument('--task', type=str, default='', help='Task description')
    parser_delivery.add_argument('--result', type=str, help='Execution result JSON')
    parser_delivery.add_argument('--quality', type=float, default=0, help='Quality score')
    parser_delivery.add_argument('--type', type=str, default='general', help='Task type')
    
    parser_delivery_report = subparsers.add_parser('delivery-report', help='Get delivery document')
    parser_delivery_report.add_argument('--session', type=str, help='Session ID')
    
    # Validation & Memory
    parser_validate = subparsers.add_parser('validate', help='Run validation')
    
    parser_save = subparsers.add_parser('save', help='Save session to memory')
    parser_save.add_argument('--session', type=str, help='Session ID')
    
    parser_reflect = subparsers.add_parser('reflect', help='Reflect on error')
    parser_reflect.add_argument('--error', type=str, required=True, help='Error message')
    
    parser_record = subparsers.add_parser('record', help='Record error fix')
    parser_record.add_argument('--error', type=str, required=True, help='Error message')
    parser_record.add_argument('--fix', type=str, required=True, help='Fix solution')
    
    # Swarm
    parser_tasks = subparsers.add_parser('tasks', help='Get parallel tasks')
    parser_tasks.add_argument('--session', type=str, help='Session ID')
    
    parser_exec_directive = subparsers.add_parser('exec-directive', help='Get execution directive for session')
    parser_exec_directive.add_argument('--session', type=str, required=True, help='Session ID')
    
    # Tokens
    parser_tokens = subparsers.add_parser('tokens', help='Get token usage summary')
    
    parser_record_tools = subparsers.add_parser('record-tools', help='Record tool calls token usage')
    parser_record_tools.add_argument('--session', type=str, help='Session ID')
    parser_record_tools.add_argument('--tool-calls', type=str, help='Tool calls description')
    parser_record_tools.add_argument('--input', type=int, default=0, help='Input token estimate')
    parser_record_tools.add_argument('--output', type=int, default=0, help='Output token estimate')
    parser_record_tools.add_argument('--type', type=str, default='tool_calls', help='Task type')
    
    parser_estimate = subparsers.add_parser('estimate-session', help='Estimate session token usage')
    parser_estimate.add_argument('--session', type=str, help='Session ID')
    parser_estimate.add_argument('--description', type=str, default='', help='Session description')
    
    # Workflow
    parser_workflow = subparsers.add_parser('workflow', help='Run full workflow')
    parser_workflow.add_argument('task', type=str, help='Task description')
    
    parser_repair = subparsers.add_parser('repair', help='Workflow repair commands')
    parser_repair.add_argument('action', type=str, choices=['scan', 'validate', 'detect-new', 'sync', 'full'],
                               help='Repair action: scan, validate, detect-new, sync, full')
    
    parser_route = subparsers.add_parser('route', help='Smart route task to best execution method')
    parser_route.add_argument('task', type=str, help='Task description')
    
    parser_monitor = subparsers.add_parser('monitor', help='Monitor project context and recommend workflows')
    
    # Closed Loop
    parser_closed_loop_start = subparsers.add_parser('closed-loop-start', help='Start closed loop workflow')
    parser_closed_loop_start.add_argument('task', type=str, help='Task description')
    parser_closed_loop_start.add_argument('--session', type=str, help='Session ID (optional)')
    
    parser_closed_loop_phase = subparsers.add_parser('closed-loop-phase', help='Execute closed loop phase')
    parser_closed_loop_phase.add_argument('--session', type=str, required=True, help='Session ID')
    parser_closed_loop_phase.add_argument('--phase', type=str, required=True, 
                                          choices=['execute', 'integrate', 'validate', 'research', 'fix', 'deliver'],
                                          help='Phase to execute')
    parser_closed_loop_phase.add_argument('--data', type=str, help='JSON data for the phase')
    
    parser_closed_loop_status = subparsers.add_parser('closed-loop-status', help='Get closed loop status')
    parser_closed_loop_status.add_argument('--session', type=str, required=True, help='Session ID')
    
    parser_closed_loop_resume = subparsers.add_parser('closed-loop-resume', help='Resume interrupted closed loop')
    parser_closed_loop_resume.add_argument('--session', type=str, required=True, help='Session ID')
    
    # Atomic
    parser_decompose = subparsers.add_parser('decompose', help='Decompose task into atomic tasks')
    parser_decompose.add_argument('task', type=str, help='Task description')
    parser_decompose.add_argument('--session', type=str, help='Session ID (optional)')
    
    # Integration
    parser_integrate = subparsers.add_parser('integrate', help='Integrate subtask results')
    parser_integrate.add_argument('--session', type=str, required=True, help='Session ID')
    parser_integrate.add_argument('--results', type=str, required=True, help='JSON results from subtasks')
    
    # Smart Validate
    parser_smart_validate = subparsers.add_parser('smart-validate', help='Run smart validation with research')
    parser_smart_validate.add_argument('--session', type=str, required=True, help='Session ID')
    parser_smart_validate.add_argument('--project-type', type=str, help='Project type (python/node/general)')
    parser_smart_validate.add_argument('--files', type=str, help='Files to validate (comma-separated or JSON)')
    
    args = parser.parse_args()
    
    kernel = UnifiedKernel()
    
    if args.command == 'init':
        result = init_runtime_directories()
        kernel.init()
        print(f"Initialized {result['initialized']} directories:")
        for d in result['directories']:
            print(f"  - {d}")
    elif args.command == 'analyze':
        kernel.analyze(args.task)
    elif args.command == 'scenario':
        kernel.scenario(args.task)
    elif args.command == 'quality':
        kernel.quality_check(args.code, args.artifacts, args.session, args.files, not args.no_real_validation)
    elif args.command == 'quality-report':
        kernel.quality_report(args.session)
    elif args.command == 'discover':
        kernel.discover_skills(args.task, args.type)
    elif args.command == 'list-skills':
        kernel.list_skills()
    elif args.command == 'track-file':
        kernel.track_file(args.path, args.action, args.diff)
    elif args.command == 'track-command':
        kernel.track_command(args.cmd, args.exit, args.output, args.error)
    elif args.command == 'track-test':
        kernel.track_test(args.name, args.passed, args.details, args.error_msg)
    elif args.command == 'track-verification':
        kernel.track_verification(args.name, args.passed, args.details, not args.manual)
    elif args.command == 'add-finding':
        kernel.add_finding(args.finding)
    elif args.command == 'tracker-summary':
        kernel.get_tracker_summary(args.session)
    elif args.command == 'delivery':
        kernel.generate_delivery(args.session, args.task, args.result, args.quality, args.type)
    elif args.command == 'delivery-report':
        kernel.delivery_report(args.session)
    elif args.command == 'validate':
        kernel.validate()
    elif args.command == 'save':
        kernel.save(args.session)
    elif args.command == 'reflect':
        kernel.reflect(args.error)
    elif args.command == 'record':
        kernel.record(args.error, args.fix)
    elif args.command == 'tasks':
        kernel.get_parallel_tasks(args.session)
    elif args.command == 'exec-directive':
        kernel.get_execution_directive(args.session)
    elif args.command == 'tokens':
        kernel.token_usage()
    elif args.command == 'record-tools':
        kernel.record_tools_usage(args.session, args.tool_calls, args.input, args.output, args.type)
    elif args.command == 'estimate-session':
        kernel.estimate_session(args.session, args.description)
    elif args.command == 'workflow':
        kernel.full_workflow(args.task)
    elif args.command == 'repair':
        if args.action == 'scan':
            kernel.repair_scan()
        elif args.action == 'validate':
            kernel.repair_validate()
        elif args.action == 'detect-new':
            kernel.repair_detect_new()
        elif args.action == 'sync':
            kernel.repair_sync()
        elif args.action == 'full':
            kernel.repair_full()
    elif args.command == 'route':
        kernel.route(args.task)
    elif args.command == 'monitor':
        kernel.monitor()
    elif args.command == 'closed-loop-start':
        kernel.closed_loop_start(args.task, args.session)
    elif args.command == 'closed-loop-phase':
        kernel.closed_loop_phase(args.session, args.phase, args.data)
    elif args.command == 'closed-loop-status':
        kernel.closed_loop_status(args.session)
    elif args.command == 'closed-loop-resume':
        kernel.closed_loop_resume(args.session)
    elif args.command == 'decompose':
        kernel.decompose_task(args.task, args.session)
    elif args.command == 'integrate':
        kernel.integrate_results(args.session, args.results)
    elif args.command == 'smart-validate':
        kernel.smart_validate(args.session, args.project_type, args.files)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()