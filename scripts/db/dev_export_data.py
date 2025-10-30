#!/usr/bin/env python3
"""
Script to export database data to JSON for migration between environments
"""
import os
import sys
import json
from datetime import datetime

# Add the project root to the path so we can import the app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app import create_app, db
from app.models.user import User
from app.models.test import Test
from app.models.experiment import Experiment

def export_data(output_file='data_export.json'):
    """Export all data to JSON file"""
    app = create_app('development')
    
    with app.app_context():
        print("Exporting database data...")
        
        # Export users
        users = []
        for user in User.query.all():
            users.append({
                'email': user.email,
                'role': user.role,
                'password_hash': user.password_hash,
                'created_at': user.created_at.isoformat() if user.created_at else None
            })
        
        # Export tests
        tests = []
        for test in Test.query.all():
            tests.append({
                'id': test.id,
                'name': test.name,
                'class_name': test.class_name,
                'description': test.description,
                'status': test.status,
                'created_at': test.created_at.isoformat() if test.created_at else None,
                'updated_at': test.updated_at.isoformat() if test.updated_at else None,
                'trials_columns': test.trials_columns
            })
        
        # Export experiments
        experiments = []
        for exp in Experiment.query.all():
            experiments.append({
                'id': exp.id,
                'test_id': exp.test_id,
                'participant_id': exp.participant_id,
                'uploaded_at': exp.uploaded_at.isoformat() if exp.uploaded_at else None,
                'data_file_path': exp.data_file_path,
                'notes': exp.notes
            })
        
        # Create export data
        export_data = {
            'export_date': datetime.now().isoformat(),
            'users': users,
            'tests': tests,
            'experiments': experiments
        }
        
        # Write to file
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"Data exported to {output_file}")
        print(f"Users: {len(users)}")
        print(f"Tests: {len(tests)}")
        print(f"Experiments: {len(experiments)}")

if __name__ == '__main__':
    import sys
    output_file = sys.argv[1] if len(sys.argv) > 1 else 'data_export.json'
    export_data(output_file)