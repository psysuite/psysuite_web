"""Unit tests for database models."""
import pytest
from datetime import datetime
from app import db
from app.models.user import User, TestAssignment, AccessLog
from app.models.test import Test
from app.models.experiment import Experiment
from app.models.dynamic_models import create_trial_model, get_trial_model


class TestUserModel:
    """Test User model functionality."""
    
    def test_user_creation(self, app):
        """Test basic user creation."""
        with app.app_context():
            user = User(email='test@example.com', role='researcher')
            user.set_password('password123')
            
            assert user.email == 'test@example.com'
            assert user.role == 'researcher'
            assert user.check_password('password123')
            assert not user.check_password('wrongpassword')
            assert user.is_active is True
            assert user.created_at is not None
    
    def test_password_hashing(self, app):
        """Test password hashing and verification."""
        with app.app_context():
            user = User(email='test@example.com', role='admin')
            user.set_password('mysecretpassword')
            
            # Password should be hashed
            assert user.password_hash != 'mysecretpassword'
            assert len(user.password_hash) > 50  # bcrypt hashes are long
            
            # Should verify correct password
            assert user.check_password('mysecretpassword')
            
            # Should reject incorrect password
            assert not user.check_password('wrongpassword')
            assert not user.check_password('')
    
    def test_user_roles(self, app):
        """Test user role validation."""
        with app.app_context():
            admin = User(email='admin@test.com', role='admin')
            researcher = User(email='researcher@test.com', role='researcher')
            
            assert admin.role == 'admin'
            assert researcher.role == 'researcher'
    
    def test_user_relationships(self, app, admin_user, sample_test):
        """Test user relationships with test assignments and access logs."""
        with app.app_context():
            # Create test assignment
            assignment = TestAssignment(
                user_id=admin_user.id,
                test_id=sample_test.id
            )
            db.session.add(assignment)
            
            # Create access log
            log = AccessLog(
                user_id=admin_user.id,
                action='login',
                details='User logged in'
            )
            db.session.add(log)
            db.session.commit()
            
            # Test relationships
            user = User.query.get(admin_user.id)
            assert len(user.test_assignments) == 1
            assert len(user.access_logs) == 1
            assert user.test_assignments[0].test_id == sample_test.id
            assert user.access_logs[0].action == 'login'


class TestTestModel:
    """Test Test model functionality."""
    
    def test_test_creation(self, app):
        """Test basic test creation."""
        with app.app_context():
            test = Test(
                name='Test TSP',
                class_name='iit.uvip.psysuite.core.tests.tsp.TestTSP',
                description='Temporal Sensitivity Paradigm test',
                status='development'
            )
            db.session.add(test)
            db.session.commit()
            
            assert test.name == 'Test TSP'
            assert test.class_name == 'iit.uvip.psysuite.core.tests.tsp.TestTSP'
            assert test.status == 'development'
            assert test.created_at is not None
    
    def test_json_fields(self, app):
        """Test JSON field handling."""
        with app.app_context():
            parameters = {
                'nextTrailModality': -1,
                'whitenoise': 0,
                'showResult': 1
            }
            columns = {
                'response_time': 'integer',
                'accuracy': 'float',
                'stimulus_type': 'string',
                'correct': 'boolean'
            }
            
            test = Test(
                name='JSON Test',
                class_name='test.class',
                default_parameters=parameters,
                trial_columns=columns
            )
            db.session.add(test)
            db.session.commit()
            
            # Retrieve and verify JSON data
            retrieved_test = Test.query.filter_by(name='JSON Test').first()
            assert retrieved_test.default_parameters == parameters
            assert retrieved_test.trial_columns == columns
            assert retrieved_test.default_parameters['nextTrailModality'] == -1
            assert retrieved_test.trial_columns['response_time'] == 'integer'
    
    def test_status_values(self, app):
        """Test valid status values."""
        with app.app_context():
            # Test all valid status values
            for status in ['development', 'production', 'finalized']:
                test = Test(
                    name=f'Test {status}',
                    class_name='test.class',
                    status=status
                )
                db.session.add(test)
            
            db.session.commit()
            
            dev_test = Test.query.filter_by(status='development').first()
            prod_test = Test.query.filter_by(status='production').first()
            final_test = Test.query.filter_by(status='finalized').first()
            
            assert dev_test is not None
            assert prod_test is not None
            assert final_test is not None
    
    def test_test_relationships(self, app, sample_test, admin_user):
        """Test test relationships with experiments and assignments."""
        with app.app_context():
            # Create experiment
            experiment = Experiment(
                unique_id='exp_rel_test',
                test_id=sample_test.id,
                subject_label='test_subject'
            )
            db.session.add(experiment)
            
            # Create assignment
            assignment = TestAssignment(
                user_id=admin_user.id,
                test_id=sample_test.id
            )
            db.session.add(assignment)
            db.session.commit()
            
            # Test relationships
            test = Test.query.get(sample_test.id)
            assert len(test.experiments) == 1
            assert len(test.assignments) == 1
            assert test.experiments[0].unique_id == 'exp_rel_test'


class TestExperimentModel:
    """Test Experiment model functionality."""
    
    def test_experiment_creation(self, app, sample_test):
        """Test basic experiment creation."""
        with app.app_context():
            experiment = Experiment(
                unique_id='exp_create_test',
                test_id=sample_test.id,
                subject_label='subject_123',
                subject_age=30,
                subject_gender=2,
                subject_population=1,
                test_type=240,
                test_block=1,
                completion_status='completed'
            )
            db.session.add(experiment)
            db.session.commit()
            
            assert experiment.unique_id == 'exp_create_test'
            assert experiment.test_id == sample_test.id
            assert experiment.subject_label == 'subject_123'
            assert experiment.subject_age == 30
            assert experiment.completion_status == 'completed'
            assert experiment.uploaded_at is not None
    
    def test_json_fields(self, app, sample_test):
        """Test JSON field handling in experiments."""
        with app.app_context():
            device_info = {
                'os': '15',
                'device': 'samsung_a25x',
                'manufacturer': 'samsung',
                'model': 'SM-A256E',
                'totMemory': 5518,
                'freeMemory': 2224
            }
            
            stimuli_delays = {
                'a1': 0, 'a2': 5, 'a3': 10, 'a4': 15,
                't1': 0, 't2': 5, 'v1': 0, 'v2': 5
            }
            
            configuration = {
                'classes': ['iit.uvip.psysuite.core.tests.tsp.TestTSP'],
                'label': 'subject_001',
                'age': 25,
                'gender': 1,
                'isDebug': False
            }
            
            experiment = Experiment(
                unique_id='exp_json_test',
                test_id=sample_test.id,
                device_info=device_info,
                stimuli_delays=stimuli_delays,
                configuration=configuration
            )
            db.session.add(experiment)
            db.session.commit()
            
            # Retrieve and verify JSON data
            retrieved_exp = Experiment.query.filter_by(unique_id='exp_json_test').first()
            assert retrieved_exp.device_info == device_info
            assert retrieved_exp.stimuli_delays == stimuli_delays
            assert retrieved_exp.configuration == configuration
            assert retrieved_exp.device_info['manufacturer'] == 'samsung'
            assert retrieved_exp.stimuli_delays['a2'] == 5
    
    def test_experiment_relationships(self, app, sample_experiment):
        """Test experiment relationships with test."""
        with app.app_context():
            experiment = Experiment.query.get(sample_experiment.id)
            assert experiment.test is not None
            assert experiment.test.name == 'Sample Test'
    
    def test_unique_id_constraint(self, app, sample_test):
        """Test unique_id constraint."""
        with app.app_context():
            # Create first experiment
            exp1 = Experiment(
                unique_id='unique_test_id',
                test_id=sample_test.id,
                subject_label='subject1'
            )
            db.session.add(exp1)
            db.session.commit()
            
            # Try to create second experiment with same unique_id
            exp2 = Experiment(
                unique_id='unique_test_id',
                test_id=sample_test.id,
                subject_label='subject2'
            )
            db.session.add(exp2)
            
            # Should raise integrity error
            with pytest.raises(Exception):
                db.session.commit()


class TestDynamicModels:
    """Test dynamic trial model functionality."""
    
    def test_create_trial_model(self, app):
        """Test dynamic trial model creation."""
        with app.app_context():
            columns = {
                'response_time': 'integer',
                'accuracy': 'float',
                'stimulus_type': 'string',
                'is_correct': 'boolean'
            }
            
            # Create dynamic model
            TrialModel = create_trial_model('TestTSP', columns)
            
            # Verify model attributes
            assert TrialModel.__tablename__ == 'testtsp_trials'
            assert hasattr(TrialModel, 'id')
            assert hasattr(TrialModel, 'experiment_id')
            assert hasattr(TrialModel, 'trial_number')
            assert hasattr(TrialModel, 'response_time')
            assert hasattr(TrialModel, 'accuracy')
            assert hasattr(TrialModel, 'stimulus_type')
            assert hasattr(TrialModel, 'is_correct')
    
    def test_dynamic_model_data_operations(self, app, sample_experiment):
        """Test data operations with dynamic models."""
        with app.app_context():
            columns = {
                'response_time': 'integer',
                'accuracy': 'float',
                'stimulus_type': 'string'
            }
            
            # Create and register dynamic model
            TrialModel = create_trial_model('SampleTest', columns)
            db.create_all()  # Create the table
            
            # Create trial data
            trial = TrialModel(
                experiment_id=sample_experiment.id,
                trial_number=1,
                response_time=500,
                accuracy=0.95,
                stimulus_type='visual'
            )
            db.session.add(trial)
            db.session.commit()
            
            # Retrieve and verify data
            retrieved_trial = TrialModel.query.filter_by(experiment_id=sample_experiment.id).first()
            assert retrieved_trial.trial_number == 1
            assert retrieved_trial.response_time == 500
            assert retrieved_trial.accuracy == 0.95
            assert retrieved_trial.stimulus_type == 'visual'
    
    def test_get_trial_model(self, app):
        """Test getting existing trial model."""
        with app.app_context():
            columns = {
                'response_time': 'integer',
                'accuracy': 'float'
            }
            
            # Create model first
            original_model = create_trial_model('GetTest', columns)
            
            # Get the same model
            retrieved_model = get_trial_model('GetTest')
            
            # Should be the same class
            assert retrieved_model == original_model
            assert retrieved_model.__tablename__ == 'gettest_trials'


class TestAccessLog:
    """Test AccessLog model functionality."""
    
    def test_access_log_creation(self, app, admin_user):
        """Test access log creation."""
        with app.app_context():
            log = AccessLog(
                user_id=admin_user.id,
                action='login',
                details='User logged in successfully',
                ip_address='192.168.1.1'
            )
            db.session.add(log)
            db.session.commit()
            
            assert log.user_id == admin_user.id
            assert log.action == 'login'
            assert log.details == 'User logged in successfully'
            assert log.ip_address == '192.168.1.1'
            assert log.timestamp is not None
    
    def test_access_log_relationship(self, app, admin_user):
        """Test access log relationship with user."""
        with app.app_context():
            log = AccessLog(
                user_id=admin_user.id,
                action='view_experiments',
                details='Viewed experiment list'
            )
            db.session.add(log)
            db.session.commit()
            
            # Test relationship
            assert log.user is not None
            assert log.user.email == admin_user.email


class TestTestAssignment:
    """Test TestAssignment model functionality."""
    
    def test_test_assignment_creation(self, app, admin_user, sample_test):
        """Test test assignment creation."""
        with app.app_context():
            assignment = TestAssignment(
                user_id=admin_user.id,
                test_id=sample_test.id
            )
            db.session.add(assignment)
            db.session.commit()
            
            assert assignment.user_id == admin_user.id
            assert assignment.test_id == sample_test.id
            assert assignment.assigned_at is not None
    
    def test_test_assignment_relationships(self, app, researcher_user, sample_test):
        """Test test assignment relationships."""
        with app.app_context():
            assignment = TestAssignment(
                user_id=researcher_user.id,
                test_id=sample_test.id
            )
            db.session.add(assignment)
            db.session.commit()
            
            # Test relationships
            assert assignment.user is not None
            assert assignment.test is not None
            assert assignment.user.email == researcher_user.email
            assert assignment.test.name == sample_test.name
    
    def test_unique_assignment_constraint(self, app, researcher_user, sample_test):
        """Test unique constraint on user-test assignments."""
        with app.app_context():
            # Create first assignment
            assignment1 = TestAssignment(
                user_id=researcher_user.id,
                test_id=sample_test.id
            )
            db.session.add(assignment1)
            db.session.commit()
            
            # Try to create duplicate assignment
            assignment2 = TestAssignment(
                user_id=researcher_user.id,
                test_id=sample_test.id
            )
            db.session.add(assignment2)
            
            # Should raise integrity error
            with pytest.raises(Exception):
                db.session.commit()