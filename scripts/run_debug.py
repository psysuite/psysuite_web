import os
import sys
import logging

# Add the project root to the path so we can import the app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

# Configure logging for PyCharm console
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Diagnostic information
print("=" * 60)
print("DIAGNOSTIC INFO:")
print(f"Python executable: {sys.executable}")
print(f"Working directory: {os.getcwd()}")
print(f"Script path: {__file__}")
print(f"FLASK_CONFIG: {os.getenv('FLASK_CONFIG', 'NOT SET')}")
print(f"DATABASE_URL: {os.getenv('DATABASE_URL', 'NOT SET')[:50]}...")
print(f"Python path: {sys.path[:3]}...")  # First 3 entries
print(f"PyCharm debugging: {'PYDEVD_LOAD_VALUES_ASYNC' in os.environ}")
print("=" * 60)

# Create app with debug configuration
app = create_app(os.getenv('FLASK_CONFIG') or 'default')

# Verify trial models for existing tests (diagnostic only)
with app.app_context():
    from app.models.test import Test
    from app import db
    
    print("DEBUG: Checking existing tests...")
    
    try:
        tests = Test.query.all()
        print(f"DEBUG: Found {len(tests)} tests in database:")
        for test in tests:
            print(f"  - {test.name} (class: {test.class_name}, status: {test.status})")
            if test.trial_columns:
                print(f"    ✅ {len(test.trial_columns)} trial columns defined")
                # Trial table will be automatically available via the new system
            else:
                print(f"    ⚠️  No trial columns defined")
    except Exception as e:
        print(f"DEBUG: Error querying tests: {e}")
        db.session.rollback()
    
    print("DEBUG: Tests check complete - trial tables managed automatically")
    
    # Configure database for debugger compatibility
    if 'PYDEVD_LOAD_VALUES_ASYNC' in os.environ or any('pydev' in path for path in sys.path):
        print("DEBUG: Configuring database for PyCharm debugger compatibility...")
        
        # Set database engine options for debugger compatibility
        db.engine.pool._recycle = -1  # Disable connection recycling
        db.engine.pool._timeout = 30  # Increase timeout
        
        # Test database connection
        try:
            db.session.execute(db.text('SELECT 1'))
            db.session.commit()
            print("DEBUG: Database connection test successful")
        except Exception as e:
            print(f"DEBUG: Database connection test failed: {e}")
            db.session.rollback()

# Enable Flask's logger
app.logger.setLevel(logging.DEBUG)

print("DEBUG: Starting Flask app in debug mode")
app.logger.info("Flask app created successfully")

if __name__ == '__main__':
    print("DEBUG: About to start Flask server")
    # For PyCharm debugging - disable reloader to prevent process conflicts
    # use_reloader=False is essential for proper database connections and debugging
    app.run(
        debug=True, host='0.0.0.0', port=5001,
        use_reloader=False,  # Must be False for PyCharm debugging and stable DB connections
        use_debugger=False   # Let PyCharm handle debugging
    )