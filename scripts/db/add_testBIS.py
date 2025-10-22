#!/usr/bin/env python3
"""
Script to add a dummy test using the test service.
This demonstrates how to use the service layer from scripts.
"""
import os
import sys
from datetime import datetime

# Add the project root to the path so we can import the app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app import create_app, db
from app.services.test_service import create_test_service


def add_testBIS():
    """Add a dummy test using the service layer"""
    app = create_app('development')
    
    with app.app_context():
        print("Adding dummy test...")
        
        # Define test data
        test_data = {
            'name': 'Temporal Bisection',
            'class_name': 'TestBIS',
            'description': 'this is the temporal bisection task',
            'status': 'development',
            'trial_columns': {
                "trid": "integer",
                "label": "string", 
                "lat": "integer",
                "confl": "string",
                "res": "boolean",
                "cor_ans": "integer",
                "user_ans": "integer",
                "elapsed": "bigint",
                "rep": "integer",
                "confl_magn": "float"
                }
        }
        
        # Use the service to create the test
        success, result, error_code = create_test_service(
            name=test_data['name'],
            class_name=test_data['class_name'],
            description=test_data['description'],
            status=test_data['status'],
            trial_columns=test_data['trial_columns']
        )
        
        if success:
            print(f"✅ Dummy test created successfully!")
            print(f"   ID: {result.id}")
            print(f"   Name: {result.name}")
            print(f"   Class: {result.class_name}")
            print(f"   Description: {result.description}")
            print(f"   Status: {result.status}")
            print(f"   Trial columns: {result.trial_columns}")
            
            # Manually set the created_at and updated_at timestamps if needed
            if hasattr(result, 'created_at') and hasattr(result, 'updated_at'):
                result.created_at = datetime(2000, 1, 1, 0, 0, 0)
                result.updated_at = datetime(2000, 1, 1, 0, 0, 0)
                db.session.commit()
                print(f"   Timestamps updated to year 2000")
        else:
            print(f"❌ Failed to create dummy test: {result}")
            if error_code:
                print(f"   Error code: {error_code}")


if __name__ == '__main__':
    add_testBIS()