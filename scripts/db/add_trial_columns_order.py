#!/usr/bin/env python3
"""
Database migration script to add trial_columns_order field to tests table.
This script adds the new field and populates it with current column order for existing tests.
"""
import os
import sys
from datetime import datetime

# Add the project root to the path so we can import the app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app import create_app, db
from app.models.test import Test


def migrate_add_trial_columns_order():
    """Add trial_columns_order field and populate existing data"""
    app = create_app('development')
    
    with app.app_context():
        print("Starting migration: Add trial_columns_order field...")
        
        try:
            # Check if the column already exists
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('tests')]
            
            if 'trial_columns_order' in columns:
                print("✅ Column trial_columns_order already exists, skipping creation")
            else:
                # Add the column using raw SQL
                print("Adding trial_columns_order column to tests table...")
                with db.engine.connect() as conn:
                    conn.execute(db.text("ALTER TABLE tests ADD COLUMN trial_columns_order JSON"))
                    conn.commit()
                print("✅ Column added successfully")
            
            # Populate existing tests with current column order
            print("Populating trial_columns_order for existing tests...")
            tests = Test.query.all()
            
            updated_count = 0
            skipped_count = 0
            
            for test in tests:
                if test.trial_columns and not test.trial_columns_order:
                    # Use current alphabetical order as fallback
                    column_names = list(test.trial_columns.keys())
                    if column_names:  # Only update if there are actually columns
                        test.trial_columns_order = column_names
                        updated_count += 1
                        print(f"  Updated test '{test.name}' with {len(column_names)} columns: {column_names}")
                    else:
                        skipped_count += 1
                        print(f"  Skipped test '{test.name}' - no trial columns defined")
                elif test.trial_columns_order:
                    print(f"  Test '{test.name}' already has trial_columns_order")
                else:
                    skipped_count += 1
                    print(f"  Skipped test '{test.name}' - no trial columns defined")
            
            if updated_count > 0:
                db.session.commit()
                print(f"✅ Updated {updated_count} tests with trial_columns_order")
            else:
                print("✅ No tests needed updating")
            
            if skipped_count > 0:
                print(f"ℹ️  Skipped {skipped_count} tests without trial columns")
            
            print("Migration completed successfully!")
            
        except Exception as e:
            print(f"❌ Migration failed: {str(e)}")
            db.session.rollback()
            raise


def rollback_trial_columns_order():
    """Rollback the migration by removing the trial_columns_order column"""
    app = create_app('development')
    
    with app.app_context():
        print("Rolling back migration: Remove trial_columns_order field...")
        
        try:
            # Check if the column exists
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('tests')]
            
            if 'trial_columns_order' not in columns:
                print("✅ Column trial_columns_order doesn't exist, nothing to rollback")
            else:
                # Remove the column using raw SQL
                print("Removing trial_columns_order column from tests table...")
                with db.engine.connect() as conn:
                    conn.execute(db.text("ALTER TABLE tests DROP COLUMN trial_columns_order"))
                    conn.commit()
                print("✅ Column removed successfully")
            
            print("Rollback completed successfully!")
            
        except Exception as e:
            print(f"❌ Rollback failed: {str(e)}")
            raise


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate trial_columns_order field')
    parser.add_argument('--rollback', action='store_true', 
                       help='Rollback the migration (remove the column)')
    
    args = parser.parse_args()
    
    if args.rollback:
        rollback_trial_columns_order()
    else:
        migrate_add_trial_columns_order()