#!/usr/bin/env python3
"""
Script to clear all database entries
"""
import os
import sys

# Add the project root to the path so we can import the app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app import create_app, db
from app.models.user import User
from app.models.test import Test
from app.models.experiment import Experiment

def clear_database():
    """Clear all entries from the database"""
    app = create_app('development')
    
    with app.app_context():
        print("Clearing database...")
        
        # Delete in order to respect foreign key constraints
        print("Deleting experiments...")
        Experiment.query.delete()
        
        print("Deleting tests...")
        Test.query.delete()
        
        print("Deleting users...")
        User.query.delete()
        
        # Commit the changes
        db.session.commit()
        print("Database cleared successfully!")

if __name__ == '__main__':
    clear_database()