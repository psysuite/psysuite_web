#!/usr/bin/env python3
"""
Script to import database data from JSON (for production deployment)
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

def import_data(input_file='data_export.json', environment='production'):
    """Import data from JSON file"""
    app = create_app(environment)
    
    with app.app_context():
        print(f"Importing data to {environment} environment...")
        
        # Read the export file
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        print(f"Import file created: {data['export_date']}")
        
        # Import users
        print("Importing users...")
        for user_data in data['users']:
            existing_user = User.query.filter_by(email=user_data['email']).first()
            if not existing_user:
                user = User(
                    email=user_data['email'],
                    role=user_data['role'],
                    password_hash=user_data['password_hash']
                )
                if user_data['created_at']:
                    user.created_at = datetime.fromisoformat(user_data['created_at'])
                db.session.add(user)
            else:
                print(f"User {user_data['email']} already exists, skipping...")
        
        # Import tests
        print("Importing tests...")
        for test_data in data['tests']:
            existing_test = Test.query.filter_by(name=test_data['name']).first()
            if not existing_test:
                test = Test(
                    name=test_data['name'],
                    class_name=test_data['class_name'],
                    description=test_data['description'],
                    status=test_data['status'],
                    trials_columns=test_data['trials_columns']
                )
                if test_data['created_at']:
                    test.created_at = datetime.fromisoformat(test_data['created_at'])
                if test_data['updated_at']:
                    test.updated_at = datetime.fromisoformat(test_data['updated_at'])
                db.session.add(test)
            else:
                print(f"Test {test_data['name']} already exists, skipping...")
        
        # Commit users and tests first
        db.session.commit()
        
        # Import experiments
        print("Importing experiments...")
        for exp_data in data['experiments']:
            # Find the test by name (since IDs might be different)
            test = Test.query.get(exp_data['test_id'])
            if test:
                experiment = Experiment(
                    test_id=test.id,
                    participant_id=exp_data['participant_id'],
                    data_file_path=exp_data['data_file_path'],
                    notes=exp_data['notes']
                )
                if exp_data['uploaded_at']:
                    experiment.uploaded_at = datetime.fromisoformat(exp_data['uploaded_at'])
                db.session.add(experiment)
            else:
                print(f"Test ID {exp_data['test_id']} not found, skipping experiment...")
        
        # Final commit
        db.session.commit()
        
        print("Import completed successfully!")
        print(f"Users imported: {len(data['users'])}")
        print(f"Tests imported: {len(data['tests'])}")
        print(f"Experiments imported: {len(data['experiments'])}")

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python dev_import_data.py <json_file> [environment]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    environment = sys.argv[2] if len(sys.argv) > 2 else 'production'
    import_data(input_file, environment)