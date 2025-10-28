#!/usr/bin/env python3
"""
Script to add TestBIS test and create testbis_trials table in a new database
This script can be run on any database to add the TestBIS test configuration.
"""

import os
import sys
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
    return testbis


def create_testbis_trials_table():
    """Create testbis_trials table if it doesn't exist"""

    # Check if table already exists
    inspector = db.inspect(db.engine)
    if 'testbis_trials' in inspector.get_table_names():
        print("✅ testbis_trials table already exists")
        return

    print("📝 Creating testbis_trials table...")

    # Create testbis_trials table
    create_table_sql = """
    CREATE TABLE testbis_trials (
        id SERIAL PRIMARY KEY,
        experiment_id INTEGER NOT NULL,
        trid INTEGER,
        created_at TIMESTAMP,
        label VARCHAR(255),
        lat INTEGER,
        confl VARCHAR(255),
        res BOOLEAN,
        cor_ans INTEGER,
        user_ans INTEGER,
        elapsed BIGINT,
        rep INTEGER,
        confl_magn DOUBLE PRECISION,
        FOREIGN KEY (experiment_id) REFERENCES experiments(id) ON DELETE CASCADE
    );
    """

    db.session.execute(text(create_table_sql))
    db.session.commit()

    print("✅ testbis_trials table created successfully")


def main():
    """Main function to add TestBIS test and create table"""

    # Get configuration from environment
    config_name = os.getenv('FLASK_CONFIG', 'development')
    print(f"🚀 Adding TestBIS to {config_name} database...")

    app = create_app(config_name)

    with app.app_context():
        try:
            # Add TestBIS test
            testbis = add_testbis_test()

            # Create testbis_trials table
            create_testbis_trials_table()

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
            sys.exit(1)


if __name__ == '__main__':
    main()