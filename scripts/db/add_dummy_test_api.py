#!/usr/bin/env python3
"""
Script to add a dummy test by simulating an API call.
This demonstrates how to test the API endpoints from scripts.
"""
import os
import sys
import json

# Add the project root to the path so we can import the app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app import create_app


def add_dummy_test_via_api():
    """Add a dummy test by simulating an API call"""
    app = create_app('development')
    
    with app.test_client() as client:
        with app.app_context():
            print("Adding dummy test via API simulation...")
            
            # First, login as admin
            login_response = client.post('/api/auth/login', json={
                'email': app.config['ADMIN_EMAIL'],
                'password': app.config['ADMIN_PASSWORD']
            })
            
            if login_response.status_code != 200:
                print(f"❌ Login failed: {login_response.status_code}")
                print(f"   Response: {login_response.get_data(as_text=True)}")
                return
            
            print("✅ Login successful")
            
            # Define test data
            test_data = {
                'name': 'dummy test',
                'class_name': 'TestDummy',
                'description': 'this is a dummy test',
                'status': 'development',
                'trial_columns': {
                    "trid": "integer",
                    "label": "string", 
                    "type": "integer",
                    "response_time": "integer",
                    "response_type": "string"
                }
            }
            
            # Make API call to create test
            response = client.post('/api/tests', json=test_data)
            
            if response.status_code == 201:
                data = json.loads(response.get_data(as_text=True))
                test_info = data['test']
                
                print(f"✅ Dummy test created successfully via API!")
                print(f"   ID: {test_info['id']}")
                print(f"   Name: {test_info['name']}")
                print(f"   Class: {test_info['class_name']}")
                print(f"   Description: {test_info['description']}")
                print(f"   Status: {test_info['status']}")
                print(f"   Trial columns: {test_info['trial_columns']}")
                
                # Update timestamps if needed (requires direct database access)
                from app.models.test import Test
                from app import db
                from datetime import datetime
                
                test = Test.query.get(test_info['id'])
                if test:
                    test.created_at = datetime(2000, 1, 1, 0, 0, 0)
                    test.updated_at = datetime(2000, 1, 1, 0, 0, 0)
                    db.session.commit()
                    print(f"   Timestamps updated to year 2000")
                
            else:
                print(f"❌ Failed to create dummy test via API: {response.status_code}")
                print(f"   Response: {response.get_data(as_text=True)}")


if __name__ == '__main__':
    add_dummy_test_via_api()