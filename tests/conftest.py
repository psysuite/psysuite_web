"""Test configuration and fixtures."""
import pytest
import tempfile
import os
from app import create_app, db
from app.models.user import User, TestAssignment, AccessLog
from app.models.test import Test
from app.models.experiment import Experiment


@pytest.fixture
def app():
    """Create application for testing."""
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key'
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
def runner(app):
    """Create test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def admin_user(app):
    """Create admin user for testing."""
    with app.app_context():
        user = User(
            email='admin@test.com',
            role='admin'
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def researcher_user(app):
    """Create researcher user for testing."""
    with app.app_context():
        user = User(
            email='researcher@test.com',
            role='researcher'
        )
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
            class_name='iit.uvip.psysuite.core.tests.sample.TestSample',
            description='A sample test for testing',
            status='development',
            default_parameters={
                'param1': 10,
                'param2': 'value'
            },
            trial_columns={
                'response_time': 'integer',
                'accuracy': 'float',
                'stimulus': 'string'
            }
        )
        db.session.add(test)
        db.session.commit()
        return test


@pytest.fixture
def sample_experiment(app, sample_test):
    """Create sample experiment for testing."""
    with app.app_context():
        experiment = Experiment(
            unique_id='exp_test_001',
            test_id=sample_test.id,
            subject_label='subject_001',
            subject_age=25,
            subject_gender=1,
            subject_population=0,
            test_type=240,
            test_block=-1,
            completion_status='completed',
            device_info={
                'os': '15',
                'device': 'test_device',
                'manufacturer': 'test_manufacturer'
            },
            app_version=61,
            stimuli_delays={'a1': 0, 'a2': 0},
            configuration={
                'classes': ['iit.uvip.psysuite.core.tests.sample.TestSample'],
                'label': 'subject_001',
                'age': 25
            }
        )
        db.session.add(experiment)
        db.session.commit()
        return experiment