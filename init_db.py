#!/usr/bin/env python3
"""
Database initialization script for PsySuite Web Manager
Run this script to create all database tables and initialize the database.
"""

import os
import sys
from app import create_app, db
from app.models.user import User
from app.models.test import Test
from app.models.experiment import Experiment
from app.models.project import Project

def init_database():
    """Initialize the database with all tables"""
    # Force development config to use PostgreSQL
    app = create_app('development')
    
    with app.app_context():
        print("Creating database tables...")
        
        # Drop all tables (optional - uncomment if you want to reset)
        # db.drop_all()
        
        # Create all tables
        db.create_all()
        
        print("Database tables created successfully!")
        
        # Check if tables exist
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"Created tables: {tables}")
        
        # Create default admin user if it doesn't exist
        admin_email = app.config.get('ADMIN_EMAIL', 'admin@psysuite.com')
        admin_password = app.config.get('ADMIN_PASSWORD', 'admin123')
        
        admin = User.query.filter_by(email=admin_email).first()
        if not admin:
            print(f"Creating default admin user: {admin_email}")
            admin = User(
                email=admin_email,
                role='admin'
            )
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()
            print("Default admin user created!")
        else:
            print("Admin user already exists.")
        
        # Test project operations
        print("\nTesting project operations...")
        try:
            projects = Project.get_all_projects()
            print(f"Found {len(projects)} existing projects")
            
            projects_with_counts = Project.get_projects_with_counts()
            print(f"Projects with counts: {len(projects_with_counts)}")
            
            print("Project operations test successful!")
        except Exception as e:
            print(f"Error testing project operations: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    init_database()