"""Test configuration and fixtures."""
import pytest
import tempfile
import os
from app import create_app, db
from app.models.user import User
from app.models.test import Test


@pytest.fixture
def app():
    """Create application for testing."""
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app({
        'TESTING': True,
        'DEBUG': False,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
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
    
    with app.app_context():
        db.create_all()
        yield app
        
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def admin_user(app):
    """Create admin user for testing."""
    with app.app_context():
        # The admin user is created automatically by the app initialization
        # Just return the existing one
        user = User.query.filter_by(email='admin@test.com').first()
        if not user:
            user = User(email='admin@test.com', role='admin')
            user.set_password('test-admin-password')
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def researcher_user(app):
    """Create researcher user for testing."""
    with app.app_context():
        user = User(email='researcher@test.com', role='researcher')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def sample_test(app):
    """Create sample test for testing."""
    with app.app_context():
        test = Test(
            name='Sample Test',
            class_name='TestSample',
            description='A sample test for testing',
            status='development',
            trial_columns={
                "trid": "integer",
                "label": "string",
                "type": "integer",
                "response_time": "integer",
                "response_type": "string"
            }
        )
        db.session.add(test)
        db.session.commit()
        return test


@pytest.fixture
def sample_experiment(app, sample_test):
    """Create sample experiment for testing."""
    with app.app_context():
        # Get the test from the database to avoid DetachedInstanceError
        test = Test.query.filter_by(name='Sample Test').first()
        if not test:
            test = Test(
                name='Sample Test',
                class_name='TestSample',
                description='A sample test for testing',
                status='development',
                trial_columns={
                    "trid": "integer",
                    "label": "string",
                    "type": "integer",
                    "response_time": "integer",
                    "response_type": "string"
                }
            )
            db.session.add(test)
            db.session.commit()
        
        from app.models.experiment import Experiment
        experiment = Experiment(
            test_id=test.id,
            exp_uid='TEST001_session_001',
            device_id='test_device',
            label='TEST001',
            age=25,
            gender=1,
            population=0,
            type=0,
            date='2024-01-01'
        )
        db.session.add(experiment)
        db.session.commit()
        return experiment