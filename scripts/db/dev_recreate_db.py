#!/usr/bin/env python3
"""
Script to recreate the database with proper schema
"""
import os
import sys
from datetime import datetime

# Add the project root to the path so we can import the app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app import create_app, db
from app.models.user import User
from app.models.test import Test
from app.models.experiment import Experiment


def recreate_database_postgres():
    """Recreate database with proper schema for PostgreSQL"""
    # Create app without auto-initialization to avoid premature admin creation.
    # user would be eliminated now
    app = create_app('development', skip_db_init=True)

    with app.app_context():
        print("Recreating PostgreSQL database with proper schema...")
        
        # For PostgreSQL, we need to drop tables in the right order due to foreign keys
        try:
            # First, clear dynamic models registry to prevent old trial tables
            print("Clearing dynamic models registry...")
            from app.models.dynamic_models import _trial_models
            _trial_models.clear()
            
            # Get all table names from metadata
            inspector = db.inspect(db.engine)
            table_names = inspector.get_table_names()
            
            if table_names:
                print(f"Found existing tables: {table_names}")
                
                # Drop all tables with CASCADE to handle foreign key constraints
                print("Dropping all existing tables...")
                with db.engine.connect() as conn:
                    # Disable foreign key checks temporarily
                    for table_name in table_names:
                        conn.execute(db.text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE'))
                    conn.commit()
                print("All tables dropped successfully")
            else:
                print("No existing tables found")
                
        except Exception as e:
            print(f"Error during table cleanup: {e}")
            # If drop_all fails, try the alternative method
            try:
                print("Trying alternative cleanup method...")
                db.drop_all()
            except Exception as e2:
                print(f"Alternative cleanup also failed: {e2}")
                print("Continuing with table creation...")

        # Create all tables with current schema
        print("Creating tables with current schema...")
        db.create_all()
        
        # Verify tables were created
        inspector = db.inspect(db.engine)
        new_tables = inspector.get_table_names()
        print(f"Created tables: {new_tables}")

        # Create default admin user
        print("Creating default admin user...")
        # Check if admin already exists
        existing_admin = User.query.filter_by(email=app.config['ADMIN_EMAIL']).first()
        if not existing_admin:
            admin = User(
                email=app.config['ADMIN_EMAIL'],
                role='admin'
            )
            admin.set_password(app.config['ADMIN_PASSWORD'])
            db.session.add(admin)
            db.session.commit()
            print(f"Admin user created: {admin.email}")
        else:
            print(f"Admin user already exists: {existing_admin.email}")

        print(f"PostgreSQL database recreated successfully!")


def recreate_database_sqllite():
    """Recreate database with proper schema"""
    # Create app without auto-initialization to avoid premature admin creation
    app = create_app('development', skip_db_init=True)
    
    # Ensure instance directory exists
    os.makedirs(app.instance_path, exist_ok=True)
    
    # Delete all possible database files for a clean start
    possible_db_paths = [
        os.path.join(app.instance_path, 'app-dev.db'),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app-dev.db'),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'instance', 'app-dev.db')
    ]
    
    for db_path in possible_db_paths:
        if os.path.exists(db_path):
            print(f"Deleting existing database file: {db_path}")
            os.remove(db_path)
    
    with app.app_context():
        print("Recreating database with proper schema...")
        
        # Clear dynamic models registry to prevent old trial tables
        print("Clearing dynamic models registry...")
        from app.models.dynamic_models import _trial_models
        _trial_models.clear()
        
        # Create all tables with current schema
        print("Creating tables with current schema...")
        db.create_all()
        
        # Create default admin user
        print("Creating default admin user...")
        # Check if admin already exists
        existing_admin = User.query.filter_by(email=app.config['ADMIN_EMAIL']).first()
        if not existing_admin:
            admin = User(
                email=app.config['ADMIN_EMAIL'],
                role='admin'
            )
            admin.set_password(app.config['ADMIN_PASSWORD'])
            db.session.add(admin)
            db.session.commit()
            print(f"Admin user created: {admin.email}")
        else:
            print(f"Admin user already exists: {existing_admin.email}")

        print(f"Database recreated successfully!")


def recreate_database_postgres_full():
    """Completely recreate the PostgreSQL database (drop and create database)"""
    import subprocess
    
    # Database connection details from config
    db_name = "psysuite_dev"
    db_user = "psysuite_user"

    print(f"Completely recreating PostgreSQL database '{db_name}'...")
    
    try:
        # Drop the database
        print(f"Dropping database '{db_name}'...")
        subprocess.run([
            'sudo', '-u', 'postgres', 'psql', '-c', f'DROP DATABASE IF EXISTS {db_name};'
        ], check=True, capture_output=True, text=True)
        
        # Create the database
        print(f"Creating database '{db_name}'...")
        subprocess.run([
            'sudo', '-u', 'postgres', 'psql', '-c', f'CREATE DATABASE {db_name} OWNER {db_user};'
        ], check=True, capture_output=True, text=True)
        
        print("Database recreated successfully!")
        
        # Now create tables and admin user
        app = create_app('development', skip_db_init=True)
        with app.app_context():
            print("Creating tables with current schema...")
            db.create_all()
            
            # Clear dynamic models registry
            print("Clearing dynamic models registry...")
            from app.models.dynamic_models import _trial_models
            _trial_models.clear()
            
            # Create default admin user
            print("Creating default admin user...")
            admin = User(
                email=app.config['ADMIN_EMAIL'],
                role='admin'
            )
            admin.set_password(app.config['ADMIN_PASSWORD'])
            db.session.add(admin)
            db.session.commit()
            print(f"Admin user created: {admin.email}")
            
        print("PostgreSQL database fully recreated successfully!")
        
    except subprocess.CalledProcessError as e:
        print(f"Error recreating database: {e}")
        print("Falling back to table-level recreation...")
        recreate_database_postgres()


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--full':
        recreate_database_postgres_full()
    elif len(sys.argv) > 1 and sys.argv[1] == '--sqlite':
        recreate_database_sqllite()
    else:
        recreate_database_postgres()