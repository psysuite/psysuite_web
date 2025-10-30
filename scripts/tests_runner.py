#!/usr/bin/env python3
"""
Convenient script runner for PsySuite Web Manager development scripts
"""
import os
import sys
import subprocess
import argparse

def run_script(script_path, args=None):
    """Run a script with optional arguments"""
    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=os.path.dirname(os.path.dirname(__file__)))
    return result.returncode

def main():
    parser = argparse.ArgumentParser(description='PsySuite Web Manager Script Runner')
    subparsers = parser.add_subparsers(dest='category', help='Script category')
    
    # Database scripts
    db_parser = subparsers.add_parser('db', help='Database management scripts')
    db_parser.add_argument('action', choices=['clear', 'dummy', 'export', 'import', 'init', 'recreate'], help='Database action to perform')
    db_parser.add_argument('--file', help='File for export/import operations')
    db_parser.add_argument('--env', default='development', help='Environment for import')
    
    # Debug script (simplified)
    subparsers.add_parser('debug', help='Run debug Flask server')
    
    # Test scripts
    test_parser = subparsers.add_parser('test', help='Test scripts')
    test_parser.add_argument('action', choices=['all', 'system', 'android'], help='Test action to perform')
    
    args = parser.parse_args()
    
    if not args.category:
        parser.print_help()
        return 1
    
    script_dir = os.path.dirname(__file__)
    
    if args.category == 'db':
        if args.action == 'clear':
            return run_script(os.path.join(script_dir, 'db', 'dev_clear_db.py'))
        elif args.action == 'export':
            script_args = [args.file] if args.file else []
            return run_script(os.path.join(script_dir, 'db', 'dev_export_data.py'), script_args)
        elif args.action == 'recreate':
            return run_script(os.path.join(script_dir, 'db', 'dev_recreate_db.py'))
        elif args.action == 'import':
            if not args.file:
                print("Error: --file is required for import")
                return 1
            script_args = [args.file, args.env]
            return run_script(os.path.join(script_dir, 'db', 'dev_import_data.py'), script_args)
    
    elif args.category == 'debug':
        return run_script(os.path.join(script_dir, 'run_debug.py'))

    elif args.category == 'test':
        if args.action == 'all':
            return run_script(os.path.join(script_dir, 'tests', 'run_tests.py'))
        elif args.action == 'system':
            return run_script(os.path.join(script_dir, 'tests', 'test_system.py'))
        elif args.action == 'android':
            return run_script(os.path.join(script_dir, 'tests', 'test_android_integration_manual.py'))
    
    return 0

if __name__ == '__main__':
    sys.exit(main())