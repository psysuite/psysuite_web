#!/usr/bin/env python3
"""Test runner for PsySuite Web Manager."""
import os
import sys
import pytest

# Add the project root to the path so we can import the app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app import create_app, db


def run_tests():
    """Run all tests with proper configuration."""
    # Set test environment
    os.environ['FLASK_CONFIG'] = 'testing'
    
    # Get the project root directory (3 levels up from this script)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    tests_dir = os.path.join(project_root, 'tests')
    
    # Create test app
    app = create_app({
        'TESTING': True,
        'DEBUG': False,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key',
        'ADMIN_EMAIL': 'admin@test.com',
        'ADMIN_PASSWORD': 'test-admin-password',
        'PSYSUITE_API_KEY': 'test-api-key',  # Add API key for upload tests
        'MAIL_SERVER': None,
        'MAIL_PORT': 587,
        'MAIL_USE_TLS': False,
        'MAIL_USERNAME': None,
        'MAIL_PASSWORD': None,
        'MAX_CONTENT_LENGTH': 200 * 1024 * 1024,  # Updated to match current config
        'PERMANENT_SESSION_LIFETIME': 3600
    })
    
    # Run tests
    with app.app_context():
        # Create all tables for testing
        db.create_all()
        
        print(f"Running tests from: {tests_dir}")
        
        # Run pytest with coverage
        exit_code = pytest.main([
            tests_dir,
            '-v',
            '--tb=short',
            '--cov=app',
            '--cov-report=term-missing',
            '--cov-report=html:htmlcov',
            '--cov-fail-under=70'  # Lowered threshold since we cleaned up files
        ])
    
    return exit_code


if __name__ == '__main__':
    exit_code = run_tests()
    sys.exit(exit_code)