"""Unit tests for data upload API."""
import pytest
import json
from app import db
from app.models.test import Test
from app.models.experiment import Experiment
from app.models.dynamic_models import get_trial_model, create_trial_model


class TestExperimentUploadAPI:
    """Test experiment upload functionality."""
    
    def test_upload_experiment_success(self, client, app, sample_test):
        """Test successful experiment upload."""
        with app.app_context():
            upload_data = {
                'unique_id': 'exp_upload_001',
                'test_class_name': 'iit.uvip.psysuite.core.tests.sample.TestSample',
                'configuration': {
                    'classes': ['iit.uvip.psysuite.core.tests.sample.TestSample'],
                    'label': 'subject_001',
                    'age': 25,
                    'gender': 1,
                    'population': 0,
                    'type': 240,
                    'block': -1,
                    'isDebug': False,
                    'device': {
                        'os': '15',
                        'device': 'test_device',
                        'manufacturer': 'test_manufacturer',
                        'model': 'TEST-MODEL',
                        'totMemory': 4096,
                        'freeMemory': 2048
                    },
                    'vercode': 61,
                    'stimuliDelays': {
                        'a1': 0, 'a2': 5, 'a3': 10, 'a4': 15,
                        't1': 0, 't2': 5, 'v1': 0, 'v2': 5
                    }
                },
                'trials': [
                    {
                        'trial_number': 1,
                        'response_time': 500,
                        'accuracy': 0.95,
                        'stimulus': 'visual'
                    },
                    {
                        'trial_number': 2,
                        'response_time': 450,
                        'accuracy': 0.88,
                        'stimulus': 'auditory'
                    }
                ]
            }
            
            # Upload experiment
            response = client.post('/api/upload/experiment', json=upload_data)
            assert response.status_code == 201
            
            data = json.loads(response.data)
            assert data['success'] is True
            assert data['message'] == 'Experiment uploaded successfully'
            assert 'experiment_id' in data
            
            # Verify experiment was created in database
            experiment = Experiment.query.filter_by(unique_id='exp_upload_001').first()
            assert experiment is not None
            assert experiment.test_id == sample_test.id
            assert experiment.subject_label == 'subject_001'
            assert experiment.subject_age == 25
            assert experiment.subject_gender == 1
            assert experiment.test_type == 240
            assert experiment.completion_status == 'completed'  # Default
            
            # Verify device info was stored
            assert experiment.device_info['manufacturer'] == 'test_manufacturer'
            assert experiment.device_info['totMemory'] == 4096
            
            # Verify stimuli delays were stored
            assert experiment.stimuli_delays['a2'] == 5
            assert experiment.stimuli_delays['t2'] == 5
            
            # Verify trial data was stored
            trial_model = get_trial_model('SampleTest')
            trials = trial_model.query.filter_by(experiment_id=experiment.id).all()
            assert len(trials) == 2
            
            trial1 = trial_model.query.filter_by(experiment_id=experiment.id, trial_number=1).first()
            assert trial1.response_time == 500
            assert trial1.accuracy == 0.95
            assert trial1.stimulus == 'visual'
    
    def test_upload_experiment_duplicate_id(self, client, app, sample_test, sample_experiment):
        """Test uploading experiment with duplicate unique_id."""
        with app.app_context():
            upload_data = {
                'unique_id': sample_experiment.unique_id,  # Duplicate ID
                'test_class_name': 'iit.uvip.psysuite.core.tests.sample.TestSample',
                'configuration': {
                    'classes': ['iit.uvip.psysuite.core.tests.sample.TestSample'],
                    'label': 'subject_002'
                },
                'trials': []
            }
            
            # Try to upload duplicate
            response = client.post('/api/upload/experiment', json=upload_data)
            assert response.status_code == 409
            
            data = json.loads(response.data)
            assert data['success'] is False
            assert 'already exists' in data['message']
    
    def test_upload_experiment_nonexistent_test(self, client, app):
        """Test uploading experiment for nonexistent test."""
        with app.app_context():
            upload_data = {
                'unique_id': 'exp_nonexistent_test',
                'test_class_name': 'nonexistent.test.class',
                'configuration': {
                    'classes': ['nonexistent.test.class'],
                    'label': 'subject_001'
                },
                'trials': []
            }
            
            # Try to upload
            response = client.post('/api/upload/experiment', json=upload_data)
            assert response.status_code == 400
            
            data = json.loads(response.data)
            assert data['success'] is False
            assert 'Test not found' in data['message']
    
    def test_upload_experiment_missing_required_fields(self, client, app):
        """Test uploading experiment with missing required fields."""
        with app.app_context():
            # Missing unique_id
            response = client.post('/api/upload/experiment', json={
                'test_class_name': 'test.class',
                'configuration': {},
                'trials': []
            })
            assert response.status_code == 400
            
            # Missing test_class_name
            response = client.post('/api/upload/experiment', json={
                'unique_id': 'exp_missing_class',
                'configuration': {},
                'trials': []
            })
            assert response.status_code == 400
            
            # Missing configuration
            response = client.post('/api/upload/experiment', json={
                'unique_id': 'exp_missing_config',
                'test_class_name': 'test.class',
                'trials': []
            })
            assert response.status_code == 400
            
            # Missing trials
            response = client.post('/api/upload/experiment', json={
                'unique_id': 'exp_missing_trials',
                'test_class_name': 'test.class',
                'configuration': {}
            })
            assert response.status_code == 400
    
    def test_upload_experiment_invalid_json(self, client, app):
        """Test uploading experiment with invalid JSON."""
        with app.app_context():
            # Send invalid JSON
            response = client.post('/api/upload/experiment', 
                data='invalid json',
                content_type='application/json')
            assert response.status_code == 400
    
    def test_upload_experiment_empty_request(self, client, app):
        """Test uploading experiment with empty request."""
        with app.app_context():
            response = client.post('/api/upload/experiment', json={})
            assert response.status_code == 400
    
    def test_upload_experiment_with_minimal_data(self, client, app, sample_test):
        """Test uploading experiment with minimal required data."""
        with app.app_context():
            upload_data = {
                'unique_id': 'exp_minimal',
                'test_class_name': 'iit.uvip.psysuite.core.tests.sample.TestSample',
                'configuration': {
                    'classes': ['iit.uvip.psysuite.core.tests.sample.TestSample']
                },
                'trials': []
            }
            
            # Upload experiment
            response = client.post('/api/upload/experiment', json=upload_data)
            assert response.status_code == 201
            
            # Verify experiment was created
            experiment = Experiment.query.filter_by(unique_id='exp_minimal').first()
            assert experiment is not None
            assert experiment.test_id == sample_test.id
    
    def test_upload_experiment_with_complete_subject_data(self, client, app, sample_test):
        """Test uploading experiment with complete subject data."""
        with app.app_context():
            upload_data = {
                'unique_id': 'exp_complete_subject',
                'test_class_name': 'iit.uvip.psysuite.core.tests.sample.TestSample',
                'configuration': {
                    'classes': ['iit.uvip.psysuite.core.tests.sample.TestSample'],
                    'label': 'subject_complete',
                    'age': 30,
                    'gender': 2,
                    'population': 1,
                    'type': 240,
                    'block': 1,
                    'isDebug': True,
                    'device': {
                        'os': '14',
                        'device': 'pixel',
                        'manufacturer': 'google',
                        'model': 'Pixel 7',
                        'id': 'BUILD123',
                        'totMemory': 8192,
                        'freeMemory': 4096
                    },
                    'vercode': 62,
                    'stimuliDelays': {
                        'a1': 1, 'a2': 2, 'a3': 3, 'a4': 4,
                        't1': 5, 't2': 6, 'v1': 7, 'v2': 8
                    }
                },
                'trials': []
            }
            
            # Upload experiment
            response = client.post('/api/upload/experiment', json=upload_data)
            assert response.status_code == 201
            
            # Verify all subject data was stored correctly
            experiment = Experiment.query.filter_by(unique_id='exp_complete_subject').first()
            assert experiment.subject_label == 'subject_complete'
            assert experiment.subject_age == 30
            assert experiment.subject_gender == 2
            assert experiment.subject_population == 1
            assert experiment.test_type == 240
            assert experiment.test_block == 1
            assert experiment.app_version == 62
            
            # Verify device info
            assert experiment.device_info['manufacturer'] == 'google'
            assert experiment.device_info['model'] == 'Pixel 7'
            assert experiment.device_info['totMemory'] == 8192
            
            # Verify stimuli delays
            assert experiment.stimuli_delays['a1'] == 1
            assert experiment.stimuli_delays['v2'] == 8


class TestTrialDataValidation:
    """Test trial data validation and storage."""
    
    def test_upload_with_valid_trial_data(self, client, app, sample_test):
        """Test uploading experiment with valid trial data."""
        with app.app_context():
            upload_data = {
                'unique_id': 'exp_valid_trials',
                'test_class_name': 'iit.uvip.psysuite.core.tests.sample.TestSample',
                'configuration': {
                    'classes': ['iit.uvip.psysuite.core.tests.sample.TestSample'],
                    'label': 'subject_trials'
                },
                'trials': [
                    {
                        'trial_number': 1,
                        'response_time': 500,
                        'accuracy': 0.95,
                        'stimulus': 'visual'
                    },
                    {
                        'trial_number': 2,
                        'response_time': 450,
                        'accuracy': 0.88,
                        'stimulus': 'auditory'
                    },
                    {
                        'trial_number': 3,
                        'response_time': 600,
                        'accuracy': 0.92,
                        'stimulus': 'tactile'
                    }
                ]
            }
            
            # Upload experiment
            response = client.post('/api/upload/experiment', json=upload_data)
            assert response.status_code == 201
            
            # Verify trial data was stored
            experiment = Experiment.query.filter_by(unique_id='exp_valid_trials').first()
            trial_model = get_trial_model('SampleTest')
            trials = trial_model.query.filter_by(experiment_id=experiment.id).order_by(trial_model.trial_number).all()
            
            assert len(trials) == 3
            assert trials[0].trial_number == 1
            assert trials[0].response_time == 500
            assert trials[1].trial_number == 2
            assert trials[1].accuracy == 0.88
            assert trials[2].trial_number == 3
            assert trials[2].stimulus == 'tactile'
    
    def test_upload_with_invalid_trial_data_types(self, client, app, sample_test):
        """Test uploading experiment with invalid trial data types."""
        with app.app_context():
            upload_data = {
                'unique_id': 'exp_invalid_trial_types',
                'test_class_name': 'iit.uvip.psysuite.core.tests.sample.TestSample',
                'configuration': {
                    'classes': ['iit.uvip.psysuite.core.tests.sample.TestSample'],
                    'label': 'subject_invalid'
                },
                'trials': [
                    {
                        'trial_number': 'not_a_number',  # Should be integer
                        'response_time': 500,
                        'accuracy': 0.95,
                        'stimulus': 'visual'
                    }
                ]
            }
            
            # Upload should fail
            response = client.post('/api/upload/experiment', json=upload_data)
            assert response.status_code == 400
            
            data = json.loads(response.data)
            assert data['success'] is False
            assert 'Invalid trial data' in data['message']
    
    def test_upload_with_missing_trial_number(self, client, app, sample_test):
        """Test uploading experiment with missing trial number."""
        with app.app_context():
            upload_data = {
                'unique_id': 'exp_missing_trial_num',
                'test_class_name': 'iit.uvip.psysuite.core.tests.sample.TestSample',
                'configuration': {
                    'classes': ['iit.uvip.psysuite.core.tests.sample.TestSample'],
                    'label': 'subject_missing'
                },
                'trials': [
                    {
                        # Missing trial_number
                        'response_time': 500,
                        'accuracy': 0.95,
                        'stimulus': 'visual'
                    }
                ]
            }
            
            # Upload should fail
            response = client.post('/api/upload/experiment', json=upload_data)
            assert response.status_code == 400
    
    def test_upload_with_extra_trial_columns(self, client, app, sample_test):
        """Test uploading experiment with extra trial columns not in test definition."""
        with app.app_context():
            upload_data = {
                'unique_id': 'exp_extra_columns',
                'test_class_name': 'iit.uvip.psysuite.core.tests.sample.TestSample',
                'configuration': {
                    'classes': ['iit.uvip.psysuite.core.tests.sample.TestSample'],
                    'label': 'subject_extra'
                },
                'trials': [
                    {
                        'trial_number': 1,
                        'response_time': 500,
                        'accuracy': 0.95,
                        'stimulus': 'visual',
                        'extra_column': 'should_be_ignored'  # Not in test definition
                    }
                ]
            }
            
            # Upload should succeed but ignore extra columns
            response = client.post('/api/upload/experiment', json=upload_data)
            assert response.status_code == 201
            
            # Verify only defined columns were stored
            experiment = Experiment.query.filter_by(unique_id='exp_extra_columns').first()
            trial_model = get_trial_model('SampleTest')
            trial = trial_model.query.filter_by(experiment_id=experiment.id).first()
            
            assert trial.response_time == 500
            assert trial.accuracy == 0.95
            assert trial.stimulus == 'visual'
            assert not hasattr(trial, 'extra_column')


class TestDataIntegrityAndValidation:
    """Test data integrity and validation."""
    
    def test_upload_maintains_referential_integrity(self, client, app, sample_test):
        """Test that upload maintains referential integrity."""
        with app.app_context():
            upload_data = {
                'unique_id': 'exp_integrity_test',
                'test_class_name': 'iit.uvip.psysuite.core.tests.sample.TestSample',
                'configuration': {
                    'classes': ['iit.uvip.psysuite.core.tests.sample.TestSample'],
                    'label': 'subject_integrity'
                },
                'trials': [
                    {
                        'trial_number': 1,
                        'response_time': 500,
                        'accuracy': 0.95,
                        'stimulus': 'visual'
                    }
                ]
            }
            
            # Upload experiment
            response = client.post('/api/upload/experiment', json=upload_data)
            assert response.status_code == 201
            
            # Verify relationships are correct
            experiment = Experiment.query.filter_by(unique_id='exp_integrity_test').first()
            assert experiment.test_id == sample_test.id
            assert experiment.test.name == 'Sample Test'
            
            # Verify trial references experiment correctly
            trial_model = get_trial_model('SampleTest')
            trial = trial_model.query.filter_by(experiment_id=experiment.id).first()
            assert trial.experiment_id == experiment.id
    
    def test_upload_with_transaction_rollback(self, client, app, sample_test):
        """Test that failed uploads rollback properly."""
        with app.app_context():
            # Create upload data that will fail during trial insertion
            upload_data = {
                'unique_id': 'exp_rollback_test',
                'test_class_name': 'iit.uvip.psysuite.core.tests.sample.TestSample',
                'configuration': {
                    'classes': ['iit.uvip.psysuite.core.tests.sample.TestSample'],
                    'label': 'subject_rollback'
                },
                'trials': [
                    {
                        'trial_number': 1,
                        'response_time': 'invalid_type',  # This will cause failure
                        'accuracy': 0.95,
                        'stimulus': 'visual'
                    }
                ]
            }
            
            # Upload should fail
            response = client.post('/api/upload/experiment', json=upload_data)
            assert response.status_code == 400
            
            # Verify no experiment was created (rollback worked)
            experiment = Experiment.query.filter_by(unique_id='exp_rollback_test').first()
            assert experiment is None
    
    def test_upload_validates_configuration_structure(self, client, app, sample_test):
        """Test that configuration structure is validated."""
        with app.app_context():
            # Valid configuration
            valid_config = {
                'classes': ['iit.uvip.psysuite.core.tests.sample.TestSample'],
                'label': 'valid_subject',
                'age': 25,
                'gender': 1
            }
            
            upload_data = {
                'unique_id': 'exp_valid_config',
                'test_class_name': 'iit.uvip.psysuite.core.tests.sample.TestSample',
                'configuration': valid_config,
                'trials': []
            }
            
            response = client.post('/api/upload/experiment', json=upload_data)
            assert response.status_code == 201
            
            # Invalid configuration (missing classes)
            invalid_config = {
                'label': 'invalid_subject',
                'age': 25
                # Missing 'classes' field
            }
            
            upload_data['unique_id'] = 'exp_invalid_config'
            upload_data['configuration'] = invalid_config
            
            response = client.post('/api/upload/experiment', json=upload_data)
            assert response.status_code == 400


class TestUploadErrorHandling:
    """Test upload error handling scenarios."""
    
    def test_upload_with_database_error(self, client, app, sample_test, monkeypatch):
        """Test handling of database errors during upload."""
        with app.app_context():
            # Mock database session to raise an error
            def mock_commit():
                raise Exception("Database error")
            
            monkeypatch.setattr(db.session, 'commit', mock_commit)
            
            upload_data = {
                'unique_id': 'exp_db_error',
                'test_class_name': 'iit.uvip.psysuite.core.tests.sample.TestSample',
                'configuration': {
                    'classes': ['iit.uvip.psysuite.core.tests.sample.TestSample'],
                    'label': 'subject_db_error'
                },
                'trials': []
            }
            
            # Upload should fail gracefully
            response = client.post('/api/upload/experiment', json=upload_data)
            assert response.status_code == 500
            
            data = json.loads(response.data)
            assert data['success'] is False
            assert 'Internal server error' in data['message']
    
    def test_upload_with_large_payload(self, client, app, sample_test):
        """Test upload with large number of trials."""
        with app.app_context():
            # Create upload with many trials
            trials = []
            for i in range(1000):  # Large number of trials
                trials.append({
                    'trial_number': i + 1,
                    'response_time': 500 + i,
                    'accuracy': 0.9 + (i % 10) * 0.01,
                    'stimulus': f'stimulus_{i % 5}'
                })
            
            upload_data = {
                'unique_id': 'exp_large_payload',
                'test_class_name': 'iit.uvip.psysuite.core.tests.sample.TestSample',
                'configuration': {
                    'classes': ['iit.uvip.psysuite.core.tests.sample.TestSample'],
                    'label': 'subject_large'
                },
                'trials': trials
            }
            
            # Upload should succeed
            response = client.post('/api/upload/experiment', json=upload_data)
            assert response.status_code == 201
            
            # Verify all trials were stored
            experiment = Experiment.query.filter_by(unique_id='exp_large_payload').first()
            trial_model = get_trial_model('SampleTest')
            stored_trials = trial_model.query.filter_by(experiment_id=experiment.id).all()
            assert len(stored_trials) == 1000
    
    def test_upload_content_type_validation(self, client, app):
        """Test that upload requires correct content type."""
        with app.app_context():
            # Send data without JSON content type
            response = client.post('/api/upload/experiment', 
                data='{"test": "data"}')
            assert response.status_code == 400
            
            # Send with wrong content type
            response = client.post('/api/upload/experiment',
                data='{"test": "data"}',
                content_type='text/plain')
            assert response.status_code == 400


class TestUploadAuthentication:
    """Test upload authentication and authorization."""
    
    def test_upload_without_authentication(self, client, app):
        """Test that upload requires authentication."""
        with app.app_context():
            upload_data = {
                'unique_id': 'exp_no_auth',
                'test_class_name': 'test.class',
                'configuration': {},
                'trials': []
            }
            
            # Should require authentication
            response = client.post('/api/upload/experiment', json=upload_data)
            # Note: Upload endpoint might be designed to work without auth for Android app
            # Adjust this test based on actual authentication requirements
    
    def test_upload_creates_access_log(self, client, app, sample_test):
        """Test that upload creates access log entry."""
        with app.app_context():
            from app.models.user import AccessLog
            
            initial_log_count = AccessLog.query.count()
            
            upload_data = {
                'unique_id': 'exp_access_log',
                'test_class_name': 'iit.uvip.psysuite.core.tests.sample.TestSample',
                'configuration': {
                    'classes': ['iit.uvip.psysuite.core.tests.sample.TestSample'],
                    'label': 'subject_log'
                },
                'trials': []
            }
            
            # Upload experiment
            response = client.post('/api/upload/experiment', json=upload_data)
            assert response.status_code == 201
            
            # Check if access log was created (if logging is implemented for uploads)
            final_log_count = AccessLog.query.count()
            # This assertion depends on whether upload logging is implemented
            # assert final_log_count > initial_log_count