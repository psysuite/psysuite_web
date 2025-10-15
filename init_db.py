#!/usr/bin/env python3
"""
Database initialization script for PsySuite Web Manager
"""

import os
import sys
from app import create_app, db
from app.models.user import User
from app.models.test import Test
from app.models.experiment import Experiment
from app.models.dynamic_models import initialize_existing_tests


def init_database():
    """Initialize the database with tables and default data"""
    
    app = create_app(os.getenv('FLASK_CONFIG') or 'development')
    
    with app.app_context():
        print("Initializing PsySuite Web Manager database...")
        
        # Create all tables
        print("Creating database tables...")
        db.create_all()
        
        # Create default admin user
        admin_email = app.config['ADMIN_EMAIL']
        admin_password = app.config['ADMIN_PASSWORD']
        
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
            print("Default admin user created successfully")
        else:
            print(f"Admin user {admin_email} already exists")
        
        # Initialize existing trial models
        print("Initializing trial models for existing tests...")
        initialize_existing_tests()
        
        print("Database initialization completed successfully!")
        print(f"Admin login: {admin_email}")
        print(f"Admin password: {admin_password}")
        print("\nYou can now start the application with: python run.py")


if __name__ == '__main__':
    init_database()