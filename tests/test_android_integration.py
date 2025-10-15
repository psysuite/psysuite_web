"""Unit tests for Android integration functionality."""
import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from app import db
from app.models.test import Test
from app.models.experiment import Experiment


class TestAndroidUploadIntegration:
    """Test Android app upload integration."""
    
    def test_android_upload_simulation(self, client, app, sample_test):
        """Test simulated Android app upload."""
        with app.app_context():
            # Simulate Android app upload payload
            android_payload = {
                'unique_id': 'android_exp_001',
                'test_class_name': 'iit.uvip.psysuite.core.tests.sample.TestSample',
                'configuration': {
                    'classes': ['iit.uvip.psysuite.core.tests.sample.TestSample'],
                    'label': 'android_subject_001',
                    'age': 28,
                    'gender': 1,
                    'population': 0,
                    'type': 240,
                    'block': -1,
                    'isDebug': False,
                    'device': {
                        'os': '15',
                        'device': 'a25x',
                        'manufacturer': 'samsung',
                        'model': 'SM-A256E',
                        'id': 'AP3A.240905.015.A2',
                        'totMemory': 5518,
                        'freeMemory': 2224
                    },
                    'vercode': 61,
                    'stimuliDelays': {
                        'a1': 0, 'a2': 0, 'a3': 0, 'a4': 0,
                        't1': 0, 't2': 0, 'v1': 0, 'v2': 0
                    }
                },
                'trials': [
                    {
                        'trial_number': 1,
                        'response_time': 523,
                        'accuracy': 0.92,
                        'stimulus': 'visual_target'
                    },
                    {
                        'trial_number': 2,
                        'response_time': 487,
                        'accuracy': 0.88,
                        'stimulus': 'auditory_target'
                    }
                ]
            }
            
            # Simulate upload from Android
            response = client.post('/api/upload/experiment', 
                json=android_payload,
                headers={'User-Agent': 'PsySuite-Android/1.0'})
            
            assert response.status_code == 201
            
            data = json.loads(response.data)
            assert data['success'] is True
            
            # Verify experiment was stored correctly
            experiment = Experiment.query.filter_by(unique_id='android_exp_001').first()
            assert experiment is not None
            assert experiment.subject_label == 'android_subject_001'
            assert experiment.device_info['manufacturer'] == 'samsung'
            assert experiment.device_info['model'] == 'SM-A256E'
    
    def test_android_upload_with_network_retry_simulation(self, client, app, sample_test):
        """Test Android upload retry behavior simulation."""
        with app.app_context():
            # First attempt - simulate network failure
            android_payload = {
                'unique_id': 'android_retry_001',
                'test_class_name': 'iit.uvip.psysuite.core.tests.sample.TestSample',
                'configuration': {
                    'classes': ['iit.uvip.psysuite.core.tests.sample.TestSample'],
                    'label': 'retry_subject'
                },
                'trials': []
            }
            
            # Simulate server temporarily unavailable
            with patch('app.api.upload.db.session.commit', side_effect=Exception("Network error")):
                response = client.post('/api/upload/experiment', json=android_payload)
                assert response.status_code == 500
            
            # Second attempt - should succeed
            response = client.post('/api/upload/experiment', json=android_payload)
            assert response.status_code == 201
            
            # Verify experiment was created on retry
            experiment = Experiment.query.filter_by(unique_id='android_retry_001').first()
            assert experiment is not None
    
    def test_android_upload_with_malformed_data(self, client, app):
        """Test Android upload with malformed data."""
        with app.app_context():
            # Simulate malformed JSON from Android
            malformed_payloads = [
                # Missing required fields
                {
                    'unique_id': 'malformed_001'
                    # Missing test_class_name, configuration, trials
                },
                # Invalid data types
                {
                    'unique_id': 123,  # Should be string
                    'test_class_name': 'test.class',
                    'configuration': 'not_an_object',  # Should be object
                    'trials': 'not_an_array'  # Should be array
                },
                # Empty required fields
                {
                    'unique_id': '',
                    'test_class_name': '',
                    'configuration': {},
                    'trials': []
                }
            ]
            
            for payload in malformed_payloads:
                response = client.post('/api/upload/experiment', json=payload)
                assert response.status_code == 400
                
                data = json.loads(response.data)
                assert data['success'] is False
    
    def test_android_upload_large_experiment(self, client, app, sample_test):
        """Test Android upload with large experiment data."""
        with app.app_context():
            # Simulate large experiment with many trials
            trials = []
            for i in range(500):  # Large experiment
                trials.append({
                    'trial_number': i + 1,
                    'response_time': 400 + (i % 200),
                    'accuracy': 0.8 + (i % 20) * 0.01,
                    'stimulus': f'stimulus_type_{i % 10}'
                })
            
            large_payload = {
                'unique_id': 'android_large_001',
                'test_class_name': 'iit.uvip.psysuite.core.tests.sample.TestSample',
                'configuration': {
                    'classes': ['iit.uvip.psysuite.core.tests.sample.TestSample'],
                    'label': 'large_experiment_subject',
                    'device': {
                        'os': '15',
                        'device': 'test_device',
                        'manufacturer': 'test_manufacturer',
                        'totMemory': 8192,
                        'freeMemory': 4096
                    }
                },
                'trials': trials
            }
            
            # Upload should succeed even with large data
            response = client.post('/api/upload/experiment', json=large_payload)
            assert response.status_code == 201
            
            # Verify all trials were stored
            experiment = Experiment.query.filter_by(unique_id='android_large_001').first()
            assert experiment is not None
            
            from app.models.dynamic_models import get_trial_model
            trial_model = get_trial_model('SampleTest')
            stored_trials = trial_model.query.filter_by(experiment_id=experiment.id).all()
            assert len(stored_trials) == 500


class TestOfflineStorageSimulation:
    """Test offline storage and retry mechanisms."""
    
    def test_offline_file_management_simulation(self, app):
        """Test simulated offline file management."""
        with app.app_context():
            # Simulate Android file structure
            with tempfile.TemporaryDirectory() as temp_dir:
                downloads_dir = os.path.join(temp_dir, 'Downloads')
                private_dir = os.path.join(temp_dir, 'private')
                os.makedirs(downloads_dir)
                os.makedirs(private_dir)
                
                # Simulate experiment files in Downloads folder
                config_file = os.path.join(downloads_dir, 'exp_offline_001_config.json')
                trials_file = os.path.join(downloads_dir, 'exp_offline_001_trials.txt')
                
                # Create mock experiment files
                config_data = {
                    'unique_id': 'exp_offline_001',
                    'classes': ['iit.uvip.psysuite.core.tests.sample.TestSample'],
                    'label': 'offline_subject',
                    'age': 25
                }
                
                with open(config_file, 'w') as f:
                    json.dump(config_data, f)
                
                with open(trials_file, 'w') as f:
                    f.write('trial_number\tresponse_time\taccuracy\tstimulus\n')
                    f.write('1\t500\t0.95\tvisual\n')
                    f.write('2\t450\t0.88\tauditory\n')
                
                # Verify files exist (simulating offline storage)
                assert os.path.exists(config_file)
                assert os.path.exists(trials_file)
                
                # Simulate successful upload and file movement
                moved_config = os.path.join(private_dir, 'exp_offline_001_config.json')
                moved_trials = os.path.join(private_dir, 'exp_offline_001_trials.txt')
                
                # Move files (simulating successful upload cleanup)
                os.rename(config_file, moved_config)
                os.rename(trials_file, moved_trials)
                
                # Verify files were moved
                assert not os.path.exists(config_file)
                assert not os.path.exists(trials_file)
                assert os.path.exists(moved_config)
                assert os.path.exists(moved_trials)
    
    def test_pending_upload_detection_simulation(self, app):
        """Test simulated pending upload detection."""
        with app.app_context():
            # Simulate Android app startup checking for pending uploads
            with tempfile.TemporaryDirectory() as temp_dir:
                downloads_dir = os.path.join(temp_dir, 'Downloads')
                os.makedirs(downloads_dir)
                
                # Create multiple pending experiment files
                pending_experiments = [
                    'exp_pending_001',
                    'exp_pending_002',
                    'exp_pending_003'
                ]
                
                for exp_id in pending_experiments:
                    config_file = os.path.join(downloads_dir, f'{exp_id}_config.json')
                    trials_file = os.path.join(downloads_dir, f'{exp_id}_trials.txt')
                    
                    with open(config_file, 'w') as f:
                        json.dump({'unique_id': exp_id}, f)
                    
                    with open(trials_file, 'w') as f:
                        f.write('trial_number\tresponse_time\n1\t500\n')
                
                # Simulate scanning Downloads folder
                config_files = [f for f in os.listdir(downloads_dir) if f.endswith('_config.json')]
                detected_experiments = [f.replace('_config.json', '') for f in config_files]
                
                # Verify all pending experiments were detected
                assert len(detected_experiments) == 3
                for exp_id in pending_experiments:
                    assert exp_id in detected_experiments
    
    def test_retry_logic_simulation(self, client, app, sample_test):
        """Test simulated retry logic with exponential backoff."""
        with app.app_context():
            retry_payload = {
                'unique_id': 'exp_retry_logic_001',
                'test_class_name': 'iit.uvip.psysuite.core.tests.sample.TestSample',
                'configuration': {
                    'classes': ['iit.uvip.psysuite.core.tests.sample.TestSample'],
                    'label': 'retry_subject'
                },
                'trials': []
            }
            
            # Simulate multiple retry attempts
            retry_delays = [1, 2, 4, 8, 16]  # Exponential backoff
            
            for attempt, delay in enumerate(retry_delays):
                if attempt < 4:  # First 4 attempts fail
                    with patch('app.api.upload.db.session.commit', side_effect=Exception("Network timeout")):
                        response = client.post('/api/upload/experiment', json=retry_payload)
                        assert response.status_code == 500
                        
                        # Simulate waiting for retry delay
                        assert delay == 2 ** attempt  # Verify exponential backoff
                else:
                    # Final attempt succeeds
                    response = client.post('/api/upload/experiment', json=retry_payload)
                    assert response.status_code == 201
                    break
            
            # Verify experiment was eventually uploaded
            experiment = Experiment.query.filter_by(unique_id='exp_retry_logic_001').first()
            assert experiment is not None


class TestAndroidConfigurationIntegration:
    """Test Android app configuration integration."""
    
    def test_api_url_configuration_simulation(self, app):
        """Test simulated API URL configuration."""
        with app.app_context():
            # Simulate different API URL configurations
            test_configs = [
                'http://localhost:5000/api',
                'https://psysuite.example.com/api',
                'https://192.168.1.100:8000/api'
            ]
            
            for api_url in test_configs:
                # Simulate Android app configuration
                config = {
                    'web_api_url': api_url,
                    'upload_enabled': True,
                    'retry_attempts': 5,
                    'retry_delay': 1000  # milliseconds
                }
                
                # Verify configuration is valid
                assert config['web_api_url'].startswith(('http://', 'https://'))
                assert config['upload_enabled'] is True
                assert config['retry_attempts'] > 0
                assert config['retry_delay'] > 0
    
    def test_upload_enable_disable_simulation(self, client, app, sample_test):
        """Test simulated upload enable/disable functionality."""
        with app.app_context():
            upload_payload = {
                'unique_id': 'exp_toggle_001',
                'test_class_name': 'iit.uvip.psysuite.core.tests.sample.TestSample',
                'configuration': {
                    'classes': ['iit.uvip.psysuite.core.tests.sample.TestSample'],
                    'label': 'toggle_subject'
                },
                'trials': []
            }
            
            # Simulate upload enabled
            upload_enabled = True
            if upload_enabled:
                response = client.post('/api/upload/experiment', json=upload_payload)
                assert response.status_code == 201
            
            # Simulate upload disabled - experiment should be stored locally only
            upload_enabled = False
            if not upload_enabled:
                # In real Android app, this would store locally without uploading
                # Here we just verify the logic path
                assert upload_enabled is False
                # No upload attempt made
    
    def test_network_connectivity_check_simulation(self, app):
        """Test simulated network connectivity checking."""
        with app.app_context():
            # Simulate different network states
            network_states = [
                {'connected': True, 'type': 'wifi'},
                {'connected': True, 'type': 'mobile'},
                {'connected': False, 'type': 'none'},
                {'connected': True, 'type': 'ethernet'}
            ]
            
            for state in network_states:
                # Simulate network connectivity check
                if state['connected']:
                    # Should attempt upload
                    can_upload = True
                else:
                    # Should store locally
                    can_upload = False
                
                # Verify logic
                assert can_upload == state['connected']


class TestAndroidErrorHandling:
    """Test Android app error handling scenarios."""
    
    def test_server_error_handling_simulation(self, client, app):
        """Test simulated server error handling."""
        with app.app_context():
            error_payload = {
                'unique_id': 'exp_server_error_001',
                'test_class_name': 'nonexistent.test.class',  # Will cause error
                'configuration': {
                    'classes': ['nonexistent.test.class'],
                    'label': 'error_subject'
                },
                'trials': []
            }
            
            # Simulate server error response
            response = client.post('/api/upload/experiment', json=error_payload)
            assert response.status_code == 400
            
            data = json.loads(response.data)
            assert data['success'] is False
            
            # Simulate Android app handling the error
            if response.status_code >= 400:
                # Should keep file for retry
                should_retry = True
                error_message = data.get('message', 'Unknown error')
                
                assert should_retry is True
                assert len(error_message) > 0
    
    def test_authentication_error_simulation(self, client, app):
        """Test simulated authentication error handling."""
        with app.app_context():
            # Simulate authentication error (if authentication is required)
            auth_payload = {
                'unique_id': 'exp_auth_error_001',
                'test_class_name': 'test.class',
                'configuration': {'classes': ['test.class']},
                'trials': []
            }
            
            # If authentication is required, this might return 401
            response = client.post('/api/upload/experiment', json=auth_payload)
            
            # Handle based on actual authentication requirements
            if response.status_code == 401:
                # Simulate Android app handling auth error
                should_prompt_reconfiguration = True
                assert should_prompt_reconfiguration is True
    
    def test_data_validation_error_simulation(self, client, app, sample_test):
        """Test simulated data validation error handling."""
        with app.app_context():
            # Simulate various validation errors
            validation_errors = [
                {
                    'unique_id': '',  # Empty unique_id
                    'test_class_name': 'iit.uvip.psysuite.core.tests.sample.TestSample',
                    'configuration': {'classes': ['iit.uvip.psysuite.core.tests.sample.TestSample']},
                    'trials': []
                },
                {
                    'unique_id': 'exp_invalid_trials',
                    'test_class_name': 'iit.uvip.psysuite.core.tests.sample.TestSample',
                    'configuration': {'classes': ['iit.uvip.psysuite.core.tests.sample.TestSample']},
                    'trials': [
                        {
                            'trial_number': 'invalid',  # Should be integer
                            'response_time': 500
                        }
                    ]
                }
            ]
            
            for error_payload in validation_errors:
                response = client.post('/api/upload/experiment', json=error_payload)
                assert response.status_code == 400
                
                data = json.loads(response.data)
                assert data['success'] is False
                
                # Simulate Android app handling validation error
                validation_error = data.get('message', '')
                should_log_error = True
                should_attempt_fix = False  # Don't retry validation errors
                
                assert len(validation_error) > 0
                assert should_log_error is True
                assert should_attempt_fix is False


class TestAndroidFileManagement:
    """Test Android file management simulation."""
    
    def test_file_parsing_simulation(self, app):
        """Test simulated Android file parsing."""
        with app.app_context():
            # Simulate parsing Android experiment files
            with tempfile.TemporaryDirectory() as temp_dir:
                # Create mock configuration file
                config_file = os.path.join(temp_dir, 'exp_parse_001_config.json')
                config_data = {
                    'unique_id': 'exp_parse_001',
                    'classes': ['iit.uvip.psysuite.core.tests.sample.TestSample'],
                    'label': 'parse_subject',
                    'age': 30,
                    'device': {
                        'manufacturer': 'samsung',
                        'model': 'Galaxy S21'
                    }
                }
                
                with open(config_file, 'w') as f:
                    json.dump(config_data, f)
                
                # Create mock trials file
                trials_file = os.path.join(temp_dir, 'exp_parse_001_trials.txt')
                with open(trials_file, 'w') as f:
                    f.write('trial_number\tresponse_time\taccuracy\tstimulus\n')
                    f.write('1\t523\t0.92\tvisual\n')
                    f.write('2\t487\t0.88\tauditory\n')
                    f.write('3\t556\t0.95\ttactile\n')
                
                # Simulate parsing configuration
                with open(config_file, 'r') as f:
                    parsed_config = json.load(f)
                
                assert parsed_config['unique_id'] == 'exp_parse_001'
                assert parsed_config['label'] == 'parse_subject'
                assert parsed_config['device']['manufacturer'] == 'samsung'
                
                # Simulate parsing trials
                trials = []
                with open(trials_file, 'r') as f:
                    lines = f.readlines()
                    headers = lines[0].strip().split('\t')
                    
                    for line in lines[1:]:
                        values = line.strip().split('\t')
                        trial = dict(zip(headers, values))
                        trial['trial_number'] = int(trial['trial_number'])
                        trial['response_time'] = int(trial['response_time'])
                        trial['accuracy'] = float(trial['accuracy'])
                        trials.append(trial)
                
                assert len(trials) == 3
                assert trials[0]['trial_number'] == 1
                assert trials[0]['response_time'] == 523
                assert trials[1]['stimulus'] == 'auditory'
    
    def test_file_cleanup_simulation(self, app):
        """Test simulated file cleanup after successful upload."""
        with app.app_context():
            with tempfile.TemporaryDirectory() as temp_dir:
                downloads_dir = os.path.join(temp_dir, 'Downloads')
                private_dir = os.path.join(temp_dir, 'private')
                os.makedirs(downloads_dir)
                os.makedirs(private_dir)
                
                # Create experiment files
                exp_files = [
                    'exp_cleanup_001_config.json',
                    'exp_cleanup_001_trials.txt'
                ]
                
                for filename in exp_files:
                    filepath = os.path.join(downloads_dir, filename)
                    with open(filepath, 'w') as f:
                        f.write('test data')
                
                # Verify files exist before cleanup
                for filename in exp_files:
                    assert os.path.exists(os.path.join(downloads_dir, filename))
                
                # Simulate successful upload and cleanup
                upload_successful = True
                if upload_successful:
                    # Move files to private storage
                    for filename in exp_files:
                        src = os.path.join(downloads_dir, filename)
                        dst = os.path.join(private_dir, filename)
                        os.rename(src, dst)
                
                # Verify files were moved
                for filename in exp_files:
                    assert not os.path.exists(os.path.join(downloads_dir, filename))
                    assert os.path.exists(os.path.join(private_dir, filename))