"""Comprehensive integration tests for the entire system."""
import pytest
import json
import tempfile
import os
from unittest.mock import patch, MagicMock
from app import db
from app.models.user import User, TestAssignment, AccessLog
from app.models.test import Test
from app.models.experiment import Experiment
from app.models.dynamic_models import get_trial_model


class TestCompleteUserWorkflows:
    """Test complete user workflows from start to finish."""
    
    def test_admin_complete_workflow(self, client, app):
        """Test complete admin workflow: login -> create test -> create user -> assign test -> view data."""
        with app.app_context():
            # Create admin user
            admin = User(email='admin@integration.com', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            
            # Step 1: Admin login
            response = client.post('/api/auth/login', json={
                'email': 'admin@integration.com',
                'password': 'admin123'
            })
            assert response.status_code == 200
            
            # Step 2: Create a new test
            test_data = {
                'name': 'Integration Test',
                'class_name': 'iit.uvip.psysuite.core.tests.integration.TestIntegration',
                'description': 'Test for integration testing',
                'status': 'development',
                'default_parameters': {
                    'param1': 100,
                    'param2': 'test_value'
                },
                'trial_columns': {
                    'response_time': 'integer',
                    'accuracy': 'float',
                    'stimulus_type': 'string',
                    'correct': 'boolean'
                }
            }
            
            response = client.post('/api/tests', json=test_data)
            assert response.status_code == 201
            test_id = json.loads(response.data)['test']['id']
            
            # Step 3: Create a researcher user
            user_data = {
                'email': 'researcher@integration.com',
                'password': 'researcher123',
                'role': 'researcher'
            }
            
            response = client.post('/api/users', json=user_data)
            assert response.status_code == 201
            user_id = json.loads(response.data)['user']['id']
            
            # Step 4: Assign test to researcher
            assignment_data = {
                'test_ids': [test_id]
            }
            
            response = client.put(f'/api/users/{user_id}/tests', json=assignment_data)
            assert response.status_code == 200
            
            # Step 5: Upload experiment data (simulating Android app)
            experiment_data = {
                'unique_id': 'integration_exp_001',
                'test_class_name': 'iit.uvip.psysuite.core.tests.integration.TestIntegration',
                'configuration': {
                    'classes': ['iit.uvip.psysuite.core.tests.integration.TestIntegration'],
                    'label': 'integration_subject',
                    'age': 25,
                    'gender': 1
                },
                'trials': [
                    {
                        'trial_number': 1,
                        'response_time': 500,
                        'accuracy': 0.95,
                        'stimulus_type': 'visual',
                        'correct': True
                    },
                    {
                        'trial_number': 2,
                        'response_time': 450,
                        'accuracy': 0.88,
                        'stimulus_type': 'auditory',
                        'correct': False
                    }
                ]
            }
            
            response = client.post('/api/upload/experiment', json=experiment_data)
            assert response.status_code == 201
            experiment_id = json.loads(response.data)['experiment_id']
            
            # Step 6: View experiments
            response = client.get('/api/experiments')
            assert response.status_code == 200
            experiments = json.loads(response.data)['experiments']
            assert len(experiments) == 1
            assert experiments[0]['unique_id'] == 'integration_exp_001'
            
            # Step 7: Get experiment details
            response = client.get(f'/api/experiments/{experiment_id}')
            assert response.status_code == 200
            experiment_details = json.loads(response.data)['experiment']
            assert experiment_details['subject_label'] == 'integration_subject'
            
            # Step 8: Get trial data
            response = client.get(f'/api/experiments/{experiment_id}/trials')
            assert response.status_code == 200
            trials = json.loads(response.data)['trials']
            assert len(trials) == 2
            assert trials[0]['response_time'] == 500
            assert trials[1]['stimulus_type'] == 'auditory'
            
            # Step 9: Download experiment data
            response = client.get(f'/api/experiments/download?experiment_ids={experiment_id}')
            assert response.status_code == 200
            assert response.headers['Content-Type'] == 'application/zip'
            
            # Step 10: Logout
            response = client.post('/api/auth/logout')
            assert response.status_code == 200
    
    def test_researcher_complete_workflow(self, client, app):
        """Test complete researcher workflow: login -> view assigned tests -> view experiments -> download data."""
        with app.app_context():
            # Setup: Create admin, test, researcher, and assignment
            admin = User(email='admin@researcher.com', role='admin')
            admin.set_password('admin123')
            
            researcher = User(email='researcher@researcher.com', role='researcher')
            researcher.set_password('researcher123')
            
            test = Test(
                name='Researcher Test',
                class_name='test.researcher',
                status='production',
                trial_columns={
                    'response_time': 'integer',
                    'accuracy': 'float'
                }
            )
            
            db.session.add_all([admin, researcher, test])
            db.session.commit()
            
            assignment = TestAssignment(
                user_id=researcher.id,
                test_id=test.id
            )
            db.session.add(assignment)
            
            # Create experiment
            experiment = Experiment(
                unique_id='researcher_exp_001',
                test_id=test.id,
                subject_label='researcher_subject',
                subject_age=30
            )
            db.session.add(experiment)
            db.session.commit()
            
            # Step 1: Researcher login
            response = client.post('/api/auth/login', json={
                'email': 'researcher@researcher.com',
                'password': 'researcher123'
            })
            assert response.status_code == 200
            
            # Step 2: View assigned tests (should only see assigned test)
            response = client.get('/api/tests')
            assert response.status_code == 200
            tests = json.loads(response.data)['tests']
            assert len(tests) == 1
            assert tests[0]['name'] == 'Researcher Test'
            
            # Step 3: View experiments (should only see experiments from assigned tests)
            response = client.get('/api/experiments')
            assert response.status_code == 200
            experiments = json.loads(response.data)['experiments']
            assert len(experiments) == 1
            assert experiments[0]['unique_id'] == 'researcher_exp_001'
            
            # Step 4: View experiment details
            response = client.get(f'/api/experiments/{experiment.id}')
            assert response.status_code == 200
            
            # Step 5: Download experiment data
            response = client.get(f'/api/experiments/download?experiment_ids={experiment.id}')
            assert response.status_code == 200
            
            # Step 6: Try to access admin functionality (should fail)
            response = client.get('/api/users')
            assert response.status_code == 403
            
            response = client.post('/api/tests', json={'name': 'Unauthorized Test'})
            assert response.status_code == 403
    
    def test_android_to_web_complete_workflow(self, client, app):
        """Test complete Android to web workflow: upload -> process -> view -> download."""
        with app.app_context():
            # Setup: Create test and admin user
            admin = User(email='admin@android.com', role='admin')
            admin.set_password('admin123')
            
            test = Test(
                name='Android Test',
                class_name='iit.uvip.psysuite.core.tests.android.TestAndroid',
                status='production',
                trial_columns={
                    'response_time': 'integer',
                    'accuracy': 'float',
                    'stimulus_type': 'string',
                    'difficulty': 'integer'
                }
            )
            
            db.session.add_all([admin, test])
            db.session.commit()
            
            # Step 1: Android app uploads experiment data
            android_payload = {
                'unique_id': 'android_complete_001',
                'test_class_name': 'iit.uvip.psysuite.core.tests.android.TestAndroid',
                'configuration': {
                    'classes': ['iit.uvip.psysuite.core.tests.android.TestAndroid'],
                    'label': 'android_subject_001',
                    'age': 28,
                    'gender': 1,
                    'population': 0,
                    'type': 240,
                    'block': -1,
                    'isDebug': False,
                    'device': {
                        'os': '15',
                        'device': 'pixel',
                        'manufacturer': 'google',
                        'model': 'Pixel 7',
                        'totMemory': 8192,
                        'freeMemory': 4096
                    },
                    'vercode': 62,
                    'stimuliDelays': {
                        'a1': 0, 'a2': 5, 'a3': 10, 'a4': 15,
                        't1': 0, 't2': 5, 'v1': 0, 'v2': 5
                    }
                },
                'trials': [
                    {
                        'trial_number': 1,
                        'response_time': 523,
                        'accuracy': 0.92,
                        'stimulus_type': 'visual',
                        'difficulty': 1
                    },
                    {
                        'trial_number': 2,
                        'response_time': 487,
                        'accuracy': 0.88,
                        'stimulus_type': 'auditory',
                        'difficulty': 2
                    },
                    {
                        'trial_number': 3,
                        'response_time': 556,
                        'accuracy': 0.95,
                        'stimulus_type': 'tactile',
                        'difficulty': 1
                    }
                ]
            }
            
            response = client.post('/api/upload/experiment', json=android_payload)
            assert response.status_code == 201
            experiment_id = json.loads(response.data)['experiment_id']
            
            # Step 2: Verify experiment was stored correctly
            experiment = Experiment.query.get(experiment_id)
            assert experiment is not None
            assert experiment.unique_id == 'android_complete_001'
            assert experiment.subject_label == 'android_subject_001'
            assert experiment.device_info['manufacturer'] == 'google'
            
            # Step 3: Verify trial data was stored
            trial_model = get_trial_model('AndroidTest')
            trials = trial_model.query.filter_by(experiment_id=experiment_id).all()
            assert len(trials) == 3
            
            # Step 4: Admin logs in to view data
            response = client.post('/api/auth/login', json={
                'email': 'admin@android.com',
                'password': 'admin123'
            })
            assert response.status_code == 200
            
            # Step 5: Admin views experiments
            response = client.get('/api/experiments')
            assert response.status_code == 200
            experiments = json.loads(response.data)['experiments']
            assert len(experiments) == 1
            assert experiments[0]['unique_id'] == 'android_complete_001'
            
            # Step 6: Admin views trial data
            response = client.get(f'/api/experiments/{experiment_id}/trials')
            assert response.status_code == 200
            trial_data = json.loads(response.data)['trials']
            assert len(trial_data) == 3
            assert trial_data[0]['response_time'] == 523
            assert trial_data[1]['stimulus_type'] == 'auditory'
            assert trial_data[2]['difficulty'] == 1
            
            # Step 7: Admin downloads data
            response = client.get(f'/api/experiments/download?experiment_ids={experiment_id}')
            assert response.status_code == 200
            assert response.headers['Content-Type'] == 'application/zip'


class TestSystemDataFlow:
    """Test complete data flow through the system."""
    
    def test_test_lifecycle_data_flow(self, client, app):
        """Test complete test lifecycle: create -> configure -> use -> finalize."""
        with app.app_context():
            # Setup admin
            admin = User(email='admin@lifecycle.com', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            
            # Login
            client.post('/api/auth/login', json={
                'email': 'admin@lifecycle.com',
                'password': 'admin123'
            })
            
            # Step 1: Create test in development
            test_data = {
                'name': 'Lifecycle Test',
                'class_name': 'test.lifecycle',
                'status': 'development',
                'trial_columns': {
                    'response_time': 'integer',
                    'accuracy': 'float'
                }
            }
            
            response = client.post('/api/tests', json=test_data)
            assert response.status_code == 201
            test_id = json.loads(response.data)['test']['id']
            
            # Step 2: Update test configuration
            update_data = {
                'description': 'Updated lifecycle test',
                'default_parameters': {
                    'trials_count': 50,
                    'timeout': 5000
                },
                'trial_columns': {
                    'response_time': 'integer',
                    'accuracy': 'float',
                    'reaction_type': 'string'  # Added new column
                }
            }
            
            response = client.put(f'/api/tests/{test_id}', json=update_data)
            assert response.status_code == 200
            
            # Step 3: Move to production
            response = client.put(f'/api/tests/{test_id}/status', json={'status': 'production'})
            assert response.status_code == 200
            
            # Step 4: Upload experiment data
            experiment_data = {
                'unique_id': 'lifecycle_exp_001',
                'test_class_name': 'test.lifecycle',
                'configuration': {
                    'classes': ['test.lifecycle'],
                    'label': 'lifecycle_subject'
                },
                'trials': [
                    {
                        'trial_number': 1,
                        'response_time': 500,
                        'accuracy': 0.95,
                        'reaction_type': 'fast'
                    }
                ]
            }
            
            response = client.post('/api/upload/experiment', json=experiment_data)
            assert response.status_code == 201
            
            # Step 5: Move to finalized (should still work with existing data)
            response = client.put(f'/api/tests/{test_id}/status', json={'status': 'finalized'})
            assert response.status_code == 200
            
            # Step 6: Verify data integrity throughout lifecycle
            response = client.get('/api/experiments')
            assert response.status_code == 200
            experiments = json.loads(response.data)['experiments']
            assert len(experiments) == 1
            
            # Verify trial data with new column
            experiment_id = experiments[0]['id']
            response = client.get(f'/api/experiments/{experiment_id}/trials')
            assert response.status_code == 200
            trials = json.loads(response.data)['trials']
            assert trials[0]['reaction_type'] == 'fast'
    
    def test_user_permission_data_flow(self, client, app):
        """Test data flow with user permissions."""
        with app.app_context():
            # Setup users and tests
            admin = User(email='admin@permission.com', role='admin')
            admin.set_password('admin123')
            
            researcher1 = User(email='researcher1@permission.com', role='researcher')
            researcher1.set_password('researcher123')
            
            researcher2 = User(email='researcher2@permission.com', role='researcher')
            researcher2.set_password('researcher123')
            
            test1 = Test(name='Test 1', class_name='test.one', status='production')
            test2 = Test(name='Test 2', class_name='test.two', status='production')
            
            db.session.add_all([admin, researcher1, researcher2, test1, test2])
            db.session.commit()
            
            # Admin assigns tests
            client.post('/api/auth/login', json={
                'email': 'admin@permission.com',
                'password': 'admin123'
            })
            
            # Assign test1 to researcher1, test2 to researcher2
            client.put(f'/api/users/{researcher1.id}/tests', json={'test_ids': [test1.id]})
            client.put(f'/api/users/{researcher2.id}/tests', json={'test_ids': [test2.id]})
            
            # Upload experiments for both tests
            for i, test in enumerate([test1, test2], 1):
                experiment_data = {
                    'unique_id': f'permission_exp_00{i}',
                    'test_class_name': test.class_name,
                    'configuration': {
                        'classes': [test.class_name],
                        'label': f'permission_subject_{i}'
                    },
                    'trials': []
                }
                client.post('/api/upload/experiment', json=experiment_data)
            
            client.post('/api/auth/logout')
            
            # Test researcher1 access
            client.post('/api/auth/login', json={
                'email': 'researcher1@permission.com',
                'password': 'researcher123'
            })
            
            # Should only see test1
            response = client.get('/api/tests')
            tests = json.loads(response.data)['tests']
            assert len(tests) == 1
            assert tests[0]['name'] == 'Test 1'
            
            # Should only see experiments from test1
            response = client.get('/api/experiments')
            experiments = json.loads(response.data)['experiments']
            assert len(experiments) == 1
            assert experiments[0]['unique_id'] == 'permission_exp_001'
            
            client.post('/api/auth/logout')
            
            # Test researcher2 access
            client.post('/api/auth/login', json={
                'email': 'researcher2@permission.com',
                'password': 'researcher123'
            })
            
            # Should only see test2
            response = client.get('/api/tests')
            tests = json.loads(response.data)['tests']
            assert len(tests) == 1
            assert tests[0]['name'] == 'Test 2'
            
            # Should only see experiments from test2
            response = client.get('/api/experiments')
            experiments = json.loads(response.data)['experiments']
            assert len(experiments) == 1
            assert experiments[0]['unique_id'] == 'permission_exp_002'


class TestErrorHandlingAndRecovery:
    """Test error handling and recovery scenarios."""
    
    def test_database_transaction_rollback(self, client, app):
        """Test database transaction rollback on errors."""
        with app.app_context():
            admin = User(email='admin@rollback.com', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            
            client.post('/api/auth/login', json={
                'email': 'admin@rollback.com',
                'password': 'admin123'
            })
            
            # Create test
            test_data = {
                'name': 'Rollback Test',
                'class_name': 'test.rollback',
                'status': 'development',
                'trial_columns': {
                    'response_time': 'integer'
                }
            }
            
            response = client.post('/api/tests', json=test_data)
            test_id = json.loads(response.data)['test']['id']
            
            # Try to upload experiment with invalid trial data
            experiment_data = {
                'unique_id': 'rollback_exp_001',
                'test_class_name': 'test.rollback',
                'configuration': {
                    'classes': ['test.rollback'],
                    'label': 'rollback_subject'
                },
                'trials': [
                    {
                        'trial_number': 1,
                        'response_time': 'invalid_integer'  # This should cause rollback
                    }
                ]
            }
            
            response = client.post('/api/upload/experiment', json=experiment_data)
            assert response.status_code == 400
            
            # Verify no experiment was created (rollback worked)
            experiment = Experiment.query.filter_by(unique_id='rollback_exp_001').first()
            assert experiment is None
            
            # Verify test still exists (partial rollback)
            test = Test.query.get(test_id)
            assert test is not None
    
    def test_concurrent_access_handling(self, client, app):
        """Test handling of concurrent access scenarios."""
        with app.app_context():
            # Create admin and test
            admin = User(email='admin@concurrent.com', role='admin')
            admin.set_password('admin123')
            
            test = Test(
                name='Concurrent Test',
                class_name='test.concurrent',
                status='production',
                trial_columns={'response_time': 'integer'}
            )
            
            db.session.add_all([admin, test])
            db.session.commit()
            
            # Simulate concurrent experiment uploads
            experiment_data_1 = {
                'unique_id': 'concurrent_exp_001',
                'test_class_name': 'test.concurrent',
                'configuration': {
                    'classes': ['test.concurrent'],
                    'label': 'concurrent_subject_1'
                },
                'trials': [
                    {'trial_number': 1, 'response_time': 500}
                ]
            }
            
            experiment_data_2 = {
                'unique_id': 'concurrent_exp_002',
                'test_class_name': 'test.concurrent',
                'configuration': {
                    'classes': ['test.concurrent'],
                    'label': 'concurrent_subject_2'
                },
                'trials': [
                    {'trial_number': 1, 'response_time': 450}
                ]
            }
            
            # Both uploads should succeed
            response1 = client.post('/api/upload/experiment', json=experiment_data_1)
            response2 = client.post('/api/upload/experiment', json=experiment_data_2)
            
            assert response1.status_code == 201
            assert response2.status_code == 201
            
            # Verify both experiments were created
            experiments = Experiment.query.filter_by(test_id=test.id).all()
            assert len(experiments) == 2
    
    def test_system_recovery_after_failure(self, client, app):
        """Test system recovery after various failure scenarios."""
        with app.app_context():
            admin = User(email='admin@recovery.com', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            
            client.post('/api/auth/login', json={
                'email': 'admin@recovery.com',
                'password': 'admin123'
            })
            
            # Create test
            test_data = {
                'name': 'Recovery Test',
                'class_name': 'test.recovery',
                'status': 'development',
                'trial_columns': {'response_time': 'integer'}
            }
            
            response = client.post('/api/tests', json=test_data)
            test_id = json.loads(response.data)['test']['id']
            
            # Simulate system failure during experiment upload
            with patch('app.api.upload.db.session.commit', side_effect=Exception("System failure")):
                experiment_data = {
                    'unique_id': 'recovery_exp_001',
                    'test_class_name': 'test.recovery',
                    'configuration': {
                        'classes': ['test.recovery'],
                        'label': 'recovery_subject'
                    },
                    'trials': [
                        {'trial_number': 1, 'response_time': 500}
                    ]
                }
                
                response = client.post('/api/upload/experiment', json=experiment_data)
                assert response.status_code == 500
            
            # System should recover and allow subsequent operations
            experiment_data['unique_id'] = 'recovery_exp_002'
            response = client.post('/api/upload/experiment', json=experiment_data)
            assert response.status_code == 201
            
            # Verify system is fully functional
            response = client.get('/api/experiments')
            assert response.status_code == 200
            experiments = json.loads(response.data)['experiments']
            assert len(experiments) == 1
            assert experiments[0]['unique_id'] == 'recovery_exp_002'


class TestSecurityAndAccessControl:
    """Test security and access control across the system."""
    
    def test_comprehensive_access_control(self, client, app):
        """Test comprehensive access control across all endpoints."""
        with app.app_context():
            # Setup users
            admin = User(email='admin@security.com', role='admin')
            admin.set_password('admin123')
            
            researcher = User(email='researcher@security.com', role='researcher')
            researcher.set_password('researcher123')
            
            test = Test(name='Security Test', class_name='test.security', status='production')
            
            db.session.add_all([admin, researcher, test])
            db.session.commit()
            
            # Test unauthenticated access (should be denied)
            protected_endpoints = [
                ('GET', '/api/tests'),
                ('POST', '/api/tests'),
                ('GET', '/api/users'),
                ('POST', '/api/users'),
                ('GET', '/api/experiments'),
                ('GET', f'/api/experiments/{1}'),
            ]
            
            for method, endpoint in protected_endpoints:
                if method == 'GET':
                    response = client.get(endpoint)
                elif method == 'POST':
                    response = client.post(endpoint, json={})
                
                assert response.status_code in [401, 403]
            
            # Test researcher access (limited)
            client.post('/api/auth/login', json={
                'email': 'researcher@security.com',
                'password': 'researcher123'
            })
            
            # Should have access to basic endpoints
            response = client.get('/api/tests')
            assert response.status_code == 200
            
            response = client.get('/api/experiments')
            assert response.status_code == 200
            
            # Should NOT have access to admin endpoints
            admin_endpoints = [
                ('GET', '/api/users'),
                ('POST', '/api/users'),
                ('POST', '/api/tests'),
                ('DELETE', f'/api/tests/{test.id}'),
            ]
            
            for method, endpoint in admin_endpoints:
                if method == 'GET':
                    response = client.get(endpoint)
                elif method == 'POST':
                    response = client.post(endpoint, json={})
                elif method == 'DELETE':
                    response = client.delete(endpoint)
                
                assert response.status_code == 403
            
            client.post('/api/auth/logout')
            
            # Test admin access (full)
            client.post('/api/auth/login', json={
                'email': 'admin@security.com',
                'password': 'admin123'
            })
            
            # Should have access to all endpoints
            response = client.get('/api/users')
            assert response.status_code == 200
            
            response = client.get('/api/tests')
            assert response.status_code == 200
    
    def test_data_isolation_between_users(self, client, app):
        """Test that users can only access their assigned data."""
        with app.app_context():
            # Setup multiple researchers with different test assignments
            admin = User(email='admin@isolation.com', role='admin')
            admin.set_password('admin123')
            
            researcher1 = User(email='researcher1@isolation.com', role='researcher')
            researcher1.set_password('researcher123')
            
            researcher2 = User(email='researcher2@isolation.com', role='researcher')
            researcher2.set_password('researcher123')
            
            test1 = Test(name='Isolation Test 1', class_name='test.isolation1', status='production')
            test2 = Test(name='Isolation Test 2', class_name='test.isolation2', status='production')
            
            db.session.add_all([admin, researcher1, researcher2, test1, test2])
            db.session.commit()
            
            # Admin assigns tests
            client.post('/api/auth/login', json={
                'email': 'admin@isolation.com',
                'password': 'admin123'
            })
            
            client.put(f'/api/users/{researcher1.id}/tests', json={'test_ids': [test1.id]})
            client.put(f'/api/users/{researcher2.id}/tests', json={'test_ids': [test2.id]})
            
            # Create experiments for both tests
            exp1_data = {
                'unique_id': 'isolation_exp_001',
                'test_class_name': 'test.isolation1',
                'configuration': {
                    'classes': ['test.isolation1'],
                    'label': 'isolation_subject_1'
                },
                'trials': []
            }
            
            exp2_data = {
                'unique_id': 'isolation_exp_002',
                'test_class_name': 'test.isolation2',
                'configuration': {
                    'classes': ['test.isolation2'],
                    'label': 'isolation_subject_2'
                },
                'trials': []
            }
            
            client.post('/api/upload/experiment', json=exp1_data)
            client.post('/api/upload/experiment', json=exp2_data)
            
            client.post('/api/auth/logout')
            
            # Test researcher1 isolation
            client.post('/api/auth/login', json={
                'email': 'researcher1@isolation.com',
                'password': 'researcher123'
            })
            
            # Should only see test1 and its experiments
            response = client.get('/api/tests')
            tests = json.loads(response.data)['tests']
            assert len(tests) == 1
            assert tests[0]['name'] == 'Isolation Test 1'
            
            response = client.get('/api/experiments')
            experiments = json.loads(response.data)['experiments']
            assert len(experiments) == 1
            assert experiments[0]['unique_id'] == 'isolation_exp_001'
            
            # Should not be able to access test2's experiment directly
            exp2 = Experiment.query.filter_by(unique_id='isolation_exp_002').first()
            response = client.get(f'/api/experiments/{exp2.id}')
            assert response.status_code == 403
            
            client.post('/api/auth/logout')
            
            # Test researcher2 isolation
            client.post('/api/auth/login', json={
                'email': 'researcher2@isolation.com',
                'password': 'researcher123'
            })
            
            # Should only see test2 and its experiments
            response = client.get('/api/tests')
            tests = json.loads(response.data)['tests']
            assert len(tests) == 1
            assert tests[0]['name'] == 'Isolation Test 2'
            
            response = client.get('/api/experiments')
            experiments = json.loads(response.data)['experiments']
            assert len(experiments) == 1
            assert experiments[0]['unique_id'] == 'isolation_exp_002'
    
    def test_audit_logging_comprehensive(self, client, app):
        """Test comprehensive audit logging across all operations."""
        with app.app_context():
            admin = User(email='admin@audit.com', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            
            initial_log_count = AccessLog.query.count()
            
            # Perform various operations that should be logged
            client.post('/api/auth/login', json={
                'email': 'admin@audit.com',
                'password': 'admin123'
            })
            
            # Create test
            test_data = {
                'name': 'Audit Test',
                'class_name': 'test.audit',
                'status': 'development'
            }
            client.post('/api/tests', json=test_data)
            
            # Create user
            user_data = {
                'email': 'newuser@audit.com',
                'password': 'newuser123',
                'role': 'researcher'
            }
            client.post('/api/users', json=user_data)
            
            # View experiments
            client.get('/api/experiments')
            
            # Logout
            client.post('/api/auth/logout')
            
            # Verify logs were created
            final_log_count = AccessLog.query.count()
            assert final_log_count > initial_log_count
            
            # Verify specific log entries
            logs = AccessLog.query.filter_by(user_id=admin.id).all()
            log_actions = [log.action for log in logs]
            
            expected_actions = ['login', 'logout']
            for action in expected_actions:
                assert action in log_actions


class TestPerformanceAndScalability:
    """Test performance and scalability aspects."""
    
    def test_large_dataset_handling(self, client, app):
        """Test handling of large datasets."""
        with app.app_context():
            admin = User(email='admin@performance.com', role='admin')
            admin.set_password('admin123')
            
            test = Test(
                name='Performance Test',
                class_name='test.performance',
                status='production',
                trial_columns={
                    'response_time': 'integer',
                    'accuracy': 'float',
                    'stimulus_id': 'integer'
                }
            )
            
            db.session.add_all([admin, test])
            db.session.commit()
            
            # Upload large experiment
            trials = []
            for i in range(1000):  # Large number of trials
                trials.append({
                    'trial_number': i + 1,
                    'response_time': 400 + (i % 200),
                    'accuracy': 0.8 + (i % 20) * 0.01,
                    'stimulus_id': i % 50
                })
            
            large_experiment = {
                'unique_id': 'performance_exp_001',
                'test_class_name': 'test.performance',
                'configuration': {
                    'classes': ['test.performance'],
                    'label': 'performance_subject',
                    'device': {
                        'manufacturer': 'test',
                        'model': 'performance'
                    }
                },
                'trials': trials
            }
            
            # Upload should succeed even with large data
            response = client.post('/api/upload/experiment', json=large_experiment)
            assert response.status_code == 201
            
            # Login and verify data retrieval performance
            client.post('/api/auth/login', json={
                'email': 'admin@performance.com',
                'password': 'admin123'
            })
            
            # Should be able to retrieve experiment list efficiently
            response = client.get('/api/experiments')
            assert response.status_code == 200
            
            # Should be able to retrieve trial data efficiently
            experiment_id = json.loads(response.data)['experiments'][0]['id']
            response = client.get(f'/api/experiments/{experiment_id}/trials')
            assert response.status_code == 200
            
            trial_data = json.loads(response.data)['trials']
            assert len(trial_data) == 1000
    
    def test_multiple_concurrent_uploads(self, client, app):
        """Test multiple concurrent experiment uploads."""
        with app.app_context():
            test = Test(
                name='Concurrent Test',
                class_name='test.concurrent',
                status='production',
                trial_columns={'response_time': 'integer'}
            )
            db.session.add(test)
            db.session.commit()
            
            # Simulate multiple concurrent uploads
            upload_results = []
            for i in range(10):
                experiment_data = {
                    'unique_id': f'concurrent_exp_{i:03d}',
                    'test_class_name': 'test.concurrent',
                    'configuration': {
                        'classes': ['test.concurrent'],
                        'label': f'concurrent_subject_{i}'
                    },
                    'trials': [
                        {'trial_number': 1, 'response_time': 500 + i}
                    ]
                }
                
                response = client.post('/api/upload/experiment', json=experiment_data)
                upload_results.append(response.status_code)
            
            # All uploads should succeed
            assert all(status == 201 for status in upload_results)
            
            # Verify all experiments were created
            experiments = Experiment.query.filter_by(test_id=test.id).all()
            assert len(experiments) == 10