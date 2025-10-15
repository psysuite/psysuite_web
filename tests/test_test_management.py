"""Unit tests for test management API."""
import pytest
import json
from app import db
from app.models.test import Test
from app.models.user import TestAssignment
from app.models.dynamic_models import get_trial_model


class TestTestCRUDAPI:
    """Test CRUD operations for test management."""
    
    def test_get_tests_as_admin(self, client, app, admin_user, sample_test):
        """Test getting all tests as admin."""
        with app.app_context():
            # Login as admin
            client.post('/api/auth/login',
                json={
                    'email': 'admin@test.com',
                    'password': 'password123'
                })
            
            # Get tests
            response = client.get('/api/tests')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert 'tests' in data
            assert len(data['tests']) >= 1
            
            # Find our sample test
            test_found = False
            for test in data['tests']:
                if test['name'] == 'Sample Test':
                    test_found = True
                    assert test['class_name'] == 'iit.uvip.psysuite.core.tests.sample.TestSample'
                    assert test['status'] == 'development'
                    assert 'default_parameters' in test
                    assert 'trial_columns' in test
            
            assert test_found
    
    def test_get_tests_as_researcher(self, client, app, researcher_user, sample_test):
        """Test getting tests as researcher (only assigned tests)."""
        with app.app_context():
            # Assign test to researcher
            assignment = TestAssignment(
                user_id=researcher_user.id,
                test_id=sample_test.id
            )
            db.session.add(assignment)
            db.session.commit()
            
            # Login as researcher
            client.post('/api/auth/login',
                json={
                    'email': 'researcher@test.com',
                    'password': 'password123'
                })
            
            # Get tests
            response = client.get('/api/tests')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert len(data['tests']) == 1
            assert data['tests'][0]['name'] == 'Sample Test'
    
    def test_get_tests_unauthenticated(self, client, app):
        """Test getting tests without authentication."""
        with app.app_context():
            response = client.get('/api/tests')
            assert response.status_code == 401
    
    def test_create_test_as_admin(self, client, app, admin_user):
        """Test creating a new test as admin."""
        with app.app_context():
            # Login as admin
            client.post('/api/auth/login',
                json={
                    'email': 'admin@test.com',
                    'password': 'password123'
                })
            
            test_data = {
                'name': 'New Test',
                'class_name': 'iit.uvip.psysuite.core.tests.new.TestNew',
                'description': 'A new test for testing',
                'status': 'development',
                'default_parameters': {
                    'param1': 100,
                    'param2': 'test_value'
                },
                'trial_columns': {
                    'reaction_time': 'integer',
                    'accuracy': 'float',
                    'stimulus': 'string',
                    'correct': 'boolean'
                }
            }
            
            # Create test
            response = client.post('/api/tests', json=test_data)
            assert response.status_code == 201
            
            data = json.loads(response.data)
            assert data['success'] is True
            assert data['test']['name'] == 'New Test'
            assert data['test']['class_name'] == 'iit.uvip.psysuite.core.tests.new.TestNew'
            
            # Verify test was created in database
            test = Test.query.filter_by(name='New Test').first()
            assert test is not None
            assert test.default_parameters['param1'] == 100
            assert test.trial_columns['reaction_time'] == 'integer'
    
    def test_create_test_as_researcher(self, client, app, researcher_user):
        """Test creating test as researcher (should fail)."""
        with app.app_context():
            # Login as researcher
            client.post('/api/auth/login',
                json={
                    'email': 'researcher@test.com',
                    'password': 'password123'
                })
            
            test_data = {
                'name': 'Unauthorized Test',
                'class_name': 'test.class',
                'status': 'development'
            }
            
            # Try to create test
            response = client.post('/api/tests', json=test_data)
            assert response.status_code == 403
    
    def test_create_test_duplicate_name(self, client, app, admin_user, sample_test):
        """Test creating test with duplicate name."""
        with app.app_context():
            # Login as admin
            client.post('/api/auth/login',
                json={
                    'email': 'admin@test.com',
                    'password': 'password123'
                })
            
            test_data = {
                'name': 'Sample Test',  # Same name as existing test
                'class_name': 'test.class',
                'status': 'development'
            }
            
            # Try to create test
            response = client.post('/api/tests', json=test_data)
            assert response.status_code == 400
            
            data = json.loads(response.data)
            assert data['success'] is False
            assert 'already exists' in data['message']
    
    def test_create_test_invalid_data(self, client, app, admin_user):
        """Test creating test with invalid data."""
        with app.app_context():
            # Login as admin
            client.post('/api/auth/login',
                json={
                    'email': 'admin@test.com',
                    'password': 'password123'
                })
            
            # Missing required fields
            response = client.post('/api/tests', json={})
            assert response.status_code == 400
            
            # Invalid status
            response = client.post('/api/tests', json={
                'name': 'Invalid Test',
                'class_name': 'test.class',
                'status': 'invalid_status'
            })
            assert response.status_code == 400
    
    def test_get_single_test(self, client, app, admin_user, sample_test):
        """Test getting a single test by ID."""
        with app.app_context():
            # Login as admin
            client.post('/api/auth/login',
                json={
                    'email': 'admin@test.com',
                    'password': 'password123'
                })
            
            # Get single test
            response = client.get(f'/api/tests/{sample_test.id}')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['test']['name'] == 'Sample Test'
            assert data['test']['id'] == sample_test.id
    
    def test_get_nonexistent_test(self, client, app, admin_user):
        """Test getting a nonexistent test."""
        with app.app_context():
            # Login as admin
            client.post('/api/auth/login',
                json={
                    'email': 'admin@test.com',
                    'password': 'password123'
                })
            
            # Get nonexistent test
            response = client.get('/api/tests/99999')
            assert response.status_code == 404
    
    def test_update_test(self, client, app, admin_user, sample_test):
        """Test updating a test."""
        with app.app_context():
            # Login as admin
            client.post('/api/auth/login',
                json={
                    'email': 'admin@test.com',
                    'password': 'password123'
                })
            
            update_data = {
                'description': 'Updated description',
                'default_parameters': {
                    'new_param': 'new_value'
                }
            }
            
            # Update test
            response = client.put(f'/api/tests/{sample_test.id}', json=update_data)
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['success'] is True
            
            # Verify update in database
            test = Test.query.get(sample_test.id)
            assert test.description == 'Updated description'
            assert test.default_parameters['new_param'] == 'new_value'
    
    def test_update_test_as_researcher(self, client, app, researcher_user, sample_test):
        """Test updating test as researcher (should fail)."""
        with app.app_context():
            # Login as researcher
            client.post('/api/auth/login',
                json={
                    'email': 'researcher@test.com',
                    'password': 'password123'
                })
            
            # Try to update test
            response = client.put(f'/api/tests/{sample_test.id}', 
                json={'description': 'Unauthorized update'})
            assert response.status_code == 403
    
    def test_delete_test(self, client, app, admin_user):
        """Test deleting a test."""
        with app.app_context():
            # Create test to delete
            test = Test(
                name='Test to Delete',
                class_name='test.delete',
                status='development'
            )
            db.session.add(test)
            db.session.commit()
            test_id = test.id
            
            # Login as admin
            client.post('/api/auth/login',
                json={
                    'email': 'admin@test.com',
                    'password': 'password123'
                })
            
            # Delete test
            response = client.delete(f'/api/tests/{test_id}')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['success'] is True
            
            # Verify deletion
            deleted_test = Test.query.get(test_id)
            assert deleted_test is None
    
    def test_delete_test_as_researcher(self, client, app, researcher_user, sample_test):
        """Test deleting test as researcher (should fail)."""
        with app.app_context():
            # Login as researcher
            client.post('/api/auth/login',
                json={
                    'email': 'researcher@test.com',
                    'password': 'password123'
                })
            
            # Try to delete test
            response = client.delete(f'/api/tests/{sample_test.id}')
            assert response.status_code == 403


class TestTestStatusManagement:
    """Test test status management functionality."""
    
    def test_update_test_status(self, client, app, admin_user, sample_test):
        """Test updating test status."""
        with app.app_context():
            # Login as admin
            client.post('/api/auth/login',
                json={
                    'email': 'admin@test.com',
                    'password': 'password123'
                })
            
            # Update status to production
            response = client.put(f'/api/tests/{sample_test.id}/status',
                json={'status': 'production'})
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['success'] is True
            
            # Verify status update
            test = Test.query.get(sample_test.id)
            assert test.status == 'production'
    
    def test_invalid_status_transition(self, client, app, admin_user, sample_test):
        """Test invalid status values."""
        with app.app_context():
            # Login as admin
            client.post('/api/auth/login',
                json={
                    'email': 'admin@test.com',
                    'password': 'password123'
                })
            
            # Try invalid status
            response = client.put(f'/api/tests/{sample_test.id}/status',
                json={'status': 'invalid_status'})
            assert response.status_code == 400
    
    def test_status_progression(self, client, app, admin_user, sample_test):
        """Test valid status progression."""
        with app.app_context():
            # Login as admin
            client.post('/api/auth/login',
                json={
                    'email': 'admin@test.com',
                    'password': 'password123'
                })
            
            # Development -> Production
            response = client.put(f'/api/tests/{sample_test.id}/status',
                json={'status': 'production'})
            assert response.status_code == 200
            
            # Production -> Finalized
            response = client.put(f'/api/tests/{sample_test.id}/status',
                json={'status': 'finalized'})
            assert response.status_code == 200
            
            # Verify final status
            test = Test.query.get(sample_test.id)
            assert test.status == 'finalized'


class TestDynamicTableManagement:
    """Test dynamic table creation and management."""
    
    def test_table_creation_on_test_creation(self, client, app, admin_user):
        """Test that dynamic tables are created when tests are created."""
        with app.app_context():
            # Login as admin
            client.post('/api/auth/login',
                json={
                    'email': 'admin@test.com',
                    'password': 'password123'
                })
            
            test_data = {
                'name': 'Dynamic Table Test',
                'class_name': 'test.dynamic',
                'status': 'development',
                'trial_columns': {
                    'response_time': 'integer',
                    'accuracy': 'float',
                    'stimulus_type': 'string'
                }
            }
            
            # Create test
            response = client.post('/api/tests', json=test_data)
            assert response.status_code == 201
            
            # Verify dynamic model was created
            trial_model = get_trial_model('DynamicTableTest')
            assert trial_model is not None
            assert hasattr(trial_model, 'response_time')
            assert hasattr(trial_model, 'accuracy')
            assert hasattr(trial_model, 'stimulus_type')
    
    def test_table_modification_on_test_update(self, client, app, admin_user, sample_test):
        """Test that dynamic tables are modified when test trial columns are updated."""
        with app.app_context():
            # Login as admin
            client.post('/api/auth/login',
                json={
                    'email': 'admin@test.com',
                    'password': 'password123'
                })
            
            # Update trial columns
            update_data = {
                'trial_columns': {
                    'response_time': 'integer',
                    'accuracy': 'float',
                    'new_column': 'string'
                }
            }
            
            response = client.put(f'/api/tests/{sample_test.id}', json=update_data)
            assert response.status_code == 200
            
            # Verify model was updated
            trial_model = get_trial_model('SampleTest')
            assert hasattr(trial_model, 'new_column')
    
    def test_table_cleanup_on_test_deletion(self, client, app, admin_user):
        """Test that dynamic tables are cleaned up when tests are deleted."""
        with app.app_context():
            # Create test with dynamic table
            test = Test(
                name='Cleanup Test',
                class_name='test.cleanup',
                status='development',
                trial_columns={
                    'test_column': 'integer'
                }
            )
            db.session.add(test)
            db.session.commit()
            test_id = test.id
            
            # Login as admin
            client.post('/api/auth/login',
                json={
                    'email': 'admin@test.com',
                    'password': 'password123'
                })
            
            # Delete test
            response = client.delete(f'/api/tests/{test_id}')
            assert response.status_code == 200
            
            # Verify test and associated data are cleaned up
            deleted_test = Test.query.get(test_id)
            assert deleted_test is None


class TestRoleBasedTestAccess:
    """Test role-based access to test endpoints."""
    
    def test_researcher_access_to_assigned_test(self, client, app, researcher_user, sample_test):
        """Test researcher can access assigned test details."""
        with app.app_context():
            # Assign test to researcher
            assignment = TestAssignment(
                user_id=researcher_user.id,
                test_id=sample_test.id
            )
            db.session.add(assignment)
            db.session.commit()
            
            # Login as researcher
            client.post('/api/auth/login',
                json={
                    'email': 'researcher@test.com',
                    'password': 'password123'
                })
            
            # Access assigned test
            response = client.get(f'/api/tests/{sample_test.id}')
            assert response.status_code == 200
    
    def test_researcher_access_to_unassigned_test(self, client, app, researcher_user, sample_test):
        """Test researcher cannot access unassigned test details."""
        with app.app_context():
            # Login as researcher (no test assignment)
            client.post('/api/auth/login',
                json={
                    'email': 'researcher@test.com',
                    'password': 'password123'
                })
            
            # Try to access unassigned test
            response = client.get(f'/api/tests/{sample_test.id}')
            assert response.status_code == 403
    
    def test_admin_access_to_all_tests(self, client, app, admin_user, sample_test):
        """Test admin can access all tests."""
        with app.app_context():
            # Login as admin
            client.post('/api/auth/login',
                json={
                    'email': 'admin@test.com',
                    'password': 'password123'
                })
            
            # Access any test
            response = client.get(f'/api/tests/{sample_test.id}')
            assert response.status_code == 200


class TestTestValidation:
    """Test test data validation."""
    
    def test_required_fields_validation(self, client, app, admin_user):
        """Test validation of required fields."""
        with app.app_context():
            # Login as admin
            client.post('/api/auth/login',
                json={
                    'email': 'admin@test.com',
                    'password': 'password123'
                })
            
            # Missing name
            response = client.post('/api/tests', json={
                'class_name': 'test.class',
                'status': 'development'
            })
            assert response.status_code == 400
            
            # Missing class_name
            response = client.post('/api/tests', json={
                'name': 'Test Name',
                'status': 'development'
            })
            assert response.status_code == 400
    
    def test_json_field_validation(self, client, app, admin_user):
        """Test validation of JSON fields."""
        with app.app_context():
            # Login as admin
            client.post('/api/auth/login',
                json={
                    'email': 'admin@test.com',
                    'password': 'password123'
                })
            
            # Valid JSON fields
            test_data = {
                'name': 'JSON Test',
                'class_name': 'test.json',
                'status': 'development',
                'default_parameters': {'param': 'value'},
                'trial_columns': {'col': 'string'}
            }
            
            response = client.post('/api/tests', json=test_data)
            assert response.status_code == 201
    
    def test_trial_columns_validation(self, client, app, admin_user):
        """Test validation of trial columns data types."""
        with app.app_context():
            # Login as admin
            client.post('/api/auth/login',
                json={
                    'email': 'admin@test.com',
                    'password': 'password123'
                })
            
            # Valid column types
            test_data = {
                'name': 'Column Test',
                'class_name': 'test.columns',
                'status': 'development',
                'trial_columns': {
                    'int_col': 'integer',
                    'float_col': 'float',
                    'str_col': 'string',
                    'bool_col': 'boolean'
                }
            }
            
            response = client.post('/api/tests', json=test_data)
            assert response.status_code == 201
            
            # Invalid column type
            test_data['trial_columns']['invalid_col'] = 'invalid_type'
            response = client.post('/api/tests', json=test_data)
            assert response.status_code == 400