#!/usr/bin/env python3
"""Test runner for PsySuite Web Manager."""
import os
import sys
import pytest
from app import create_app, db


def run_tests():
    """Run all tests with proper configuration."""
    # Set test environment
    os.environ['FLASK_CONFIG'] = 'testing'
    
    # Create test app
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key'
    })
    
    # Run tests
    with app.app_context():
        # Create all tables for testing
        db.create_all()
        
        # Run pytest with coverage
        exit_code = pytest.main([
            'tests/',
            '-v',
            '--tb=short',
            '--cov=app',
            '--cov-report=term-missing',
            '--cov-report=html:htmlcov',
            '--cov-fail-under=80'
        ])
    
    return exit_code


if __name__ == '__main__':
    exit_code = run_tests()
    sys.exit(exit_code)