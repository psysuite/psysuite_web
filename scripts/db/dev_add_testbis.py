#!/usr/bin/env python3
"""
Script to add TestBIS test and create testbis_trials table in a new database
This script can be run on any database to add the TestBIS test configuration.
"""

import os
import sys

# Add parent directory to path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from datetime import datetime
from app import create_app, db
from app.models.test import Test
from sqlalchemy import text


def add_testbis_test():
    """Add TestBIS test to the tests table if it doesn't exist"""

    # Check if TestBIS already exists
    existing_test = Test.query.filter_by(class_name='TestBIS').first()
    if existing_test:
        print("✅ TestBIS test already exists in database")
        return existing_test

    print("📝 Creating TestBIS test...")

    # Create TestBIS test
    testbis = Test(
        name='Temporal Bisection',
        class_name='TestBIS',
        description='this is the temporal bisection task',
        status='production',
        created_at=datetime(2000, 1, 1),  # Original creation date
        updated_at=datetime.now(),
        _trial_columns={
            'trid': 'integer',
            'label': 'string',
            'lat': 'integer',
            'confl': 'string',
            'res': 'boolean',
            'cor_ans': 'integer',
            'user_ans': 'integer',
            'elapsed': 'bigint',
            'rep': 'integer',
            'confl_magn': 'float'
        },
        trial_columns_order=None
    )

    db.session.add(testbis)
    db.session.commit()

    print("✅ TestBIS test created successfully")
    
    # Verify trial table was created (the event listener should have handled this)
    success, message = testbis.create_trial_table()
    if success:
        print("✅ Trial table verified/created successfully")
    else:
        print(f"⚠️  Trial table issue: {message}")
    
    return testbis


def verify_testbis_trials_table(testbis_test):
    """Verify testbis_trials table exists"""
    
    print("🔍 Verifying testbis_trials table...")
    
    # Check if table exists
    inspector = db.inspect(db.engine)
    if 'testbis_trials' in inspector.get_table_names():
        print("✅ testbis_trials table exists")
        return True
    else:
        print("❌ testbis_trials table does not exist")
        return False


def main():
    """Main function to add TestBIS test and create table"""

    # Get configuration from environment
    config_name = os.getenv('FLASK_CONFIG', 'development')
    print(f"🚀 Adding TestBIS to {config_name} database...")

    # Create app with skip_db_init to avoid conflicts with running server
    app = create_app(config_name, skip_db_init=True)

    with app.app_context():
        try:
            # Test database connection first
            print("🔍 Testing database connection...")
            db.session.execute(text('SELECT 1'))
            print("✅ Database connection successful")
            
            # Check if server is running by looking for existing connections
            result = db.session.execute(text("SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()"))
            connection_count = result.scalar()
            print(f"🔍 Database connections: {connection_count}")
            
            # Add TestBIS test (trial table will be created automatically)
            testbis = add_testbis_test()

            # Verify testbis_trials table was created
            table_exists = verify_testbis_trials_table(testbis)
            
            if not table_exists:
                print("⚠️  Trial table was not created automatically, this might indicate an issue")
                print("   The table should have been created by the Test model events or explicit call")

            print(f"\n🎉 TestBIS setup complete!")
            print(f"   - Test ID: {testbis.id}")
            print(f"   - Test Name: {testbis.name}")
            print(f"   - Class Name: {testbis.class_name}")
            print(f"   - Status: {testbis.status}")
            print(f"   - Trial columns: {len(testbis._trial_columns)} columns defined")
            print(f"   - Table: testbis_trials created/verified")

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            
            # Additional debugging info
            print("\n🔍 Debug information:")
            print(f"   - Config: {config_name}")
            print(f"   - Database URL: {app.config.get('SQLALCHEMY_DATABASE_URI', 'NOT SET')[:50]}...")
            
            sys.exit(1)


if __name__ == '__main__':
    main()