"""Test management functionality tests."""
import json
from app.models.test import Test
from app import db


class TestTestManagement:
    """Test CRUD operations for tests."""
    
    def test_create_test(self, client, admin_user):
        """Test creating a new test."""
        # Login first
        client.post('/api/auth/login', json={
            'email': 'admin@test.com',
            'password': 'test-admin-password'
        })
        
        test_data = {
            'name': 'New Test',
            'class_name': 'iit.uvip.psysuite.core.tests.new.TestNew',
            'description': 'A new test for testing',
            'status': 'development',
            'trial_columns': {
                'response_time': 'integer',
                'accuracy': 'float',
                'stimulus_type': 'string'
            }
        }
        
        response = client.post('/api/tests', json=test_data)
        assert response.status_code == 201
        
        data = json.loads(response.data)
        assert data['test']['name'] == 'New Test'
        assert data['test']['class_name'] == 'iit.uvip.psysuite.core.tests.new.TestNew'
    
    def test_get_all_tests(self, client, admin_user, sample_test):
        """Test getting all tests."""
        # Login first
        client.post('/api/auth/login', json={
            'email': 'admin@test.com',
            'password': 'test-admin-password'
        })
        
        response = client.get('/api/tests')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'tests' in data
        assert len(data['tests']) >= 1
    
    def test_get_single_test(self, client, admin_user, app):
        """Test getting a single test by ID."""
        # Create a test within the test context
        with app.app_context():
            test = Test(
                name='Single Test',
                class_name='test.single.TestSingle',
                description='Test for single retrieval',
                status='development',
                trial_columns={
                    'response_time': 'integer',
                    'accuracy': 'float'
                }
            )
            db.session.add(test)
            db.session.commit()
            test_id = test.id
            test_name = test.name
        
        # Login first
        client.post('/api/auth/login', json={
            'email': 'admin@test.com',
            'password': 'test-admin-password'
        })
        
        response = client.get(f'/api/tests/{test_id}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['name'] == test_name
        assert data['id'] == test_id
    
    def test_update_test(self, client, admin_user, app):
        """Test updating an existing test."""
        # Create a test within the test context
        with app.app_context():
            test = Test(
                name='Update Test',
                class_name='test.update.TestUpdate',
                description='Original description',
                status='development',
                trial_columns={
                    'response_time': 'integer',
                    'accuracy': 'float'
                }
            )
            db.session.add(test)
            db.session.commit()
            test_id = test.id
        
        # Login first
        client.post('/api/auth/login', json={
            'email': 'admin@test.com',
            'password': 'test-admin-password'
        })
        
        update_data = {
            'description': 'Updated description'
        }
        
        response = client.put(f'/api/tests/{test_id}', json=update_data)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['test']['description'] == 'Updated description'
        
        # Update status using the dedicated endpoint
        status_data = {'status': 'production'}
        response = client.put(f'/api/tests/{test_id}/status', json=status_data)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['test']['status'] == 'production'
    
    def test_delete_test(self, client, admin_user, app):
        """Test deleting a test."""
        with app.app_context():
            # Create a test to delete
            test = Test(
                name='Test to Delete',
                class_name='test.delete.TestDelete',
                description='Will be deleted',
                status='development'
            )
            db.session.add(test)
            db.session.commit()
            test_id = test.id
        
        # Login first
        client.post('/api/auth/login', json={
            'email': 'admin@test.com',
            'password': 'test-admin-password'
        })
        
        response = client.delete(f'/api/tests/{test_id}')
        assert response.status_code == 200
        
        # Verify test is deleted by checking the tests list
        response = client.get('/api/tests')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        test_ids = [test['id'] for test in data['tests']]
        assert test_id not in test_ids
    
    def test_get_test_parameters(self, client, admin_user, app):
        """Test getting test parameters/configuration."""
        # Create a test within the test context
        with app.app_context():
            trial_columns = {
                'response_time': 'integer',
                'accuracy': 'float',
                'stimulus': 'string'
            }
            test = Test(
                name='Parameters Test',
                class_name='test.params.TestParams',
                description='Test for parameters',
                status='development',
                trial_columns=trial_columns
            )
            db.session.add(test)
            db.session.commit()
            test_id = test.id
        
        # Login first
        client.post('/api/auth/login', json={
            'email': 'admin@test.com',
            'password': 'test-admin-password'
        })
        
        response = client.get(f'/api/tests/{test_id}/parameters')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'trial_columns' in data
        assert data['trial_columns'] == trial_columns
    
    def test_researcher_cannot_create_test(self, client, app):
        """Test that researchers cannot create tests."""
        # Create researcher user within test context
        with app.app_context():
            from app.models.user import User
            user = User(email='researcher_create@test.com', role='researcher')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
        
        # Login as researcher
        client.post('/api/auth/login', json={
            'email': 'researcher_create@test.com',
            'password': 'password123'
        })
        
        test_data = {
            'name': 'Unauthorized Test',
            'class_name': 'test.unauthorized.TestUnauth',
            'description': 'Should not be created'
        }
        
        response = client.post('/api/tests', json=test_data)
        assert response.status_code == 403
    
    def test_researcher_can_view_experiments_from_assigned_projects(self, client, app):
        """Test that researchers can view experiments from their assigned projects."""
        with app.app_context():
            # Create researcher user, project, and experiment
            from app.models.user import User, ProjectAssignment
            from app.models.project import Project
            from app.models.experiment import Experiment
            
            user = User(email='researcher_view@test.com', role='researcher')
            user.set_password('password123')
            db.session.add(user)
            
            test = Test(
                name='Project Test',
                class_name='test.project.TestProject',
                description='Test for project-based access',
                status='production',
                trial_columns={
                    'response_time': 'integer',
                    'accuracy': 'float'
                }
            )
            db.session.add(test)
            
            project = Project(name='Researcher Project', created_by='admin')
            db.session.add(project)
            db.session.commit()
            
            # Assign project to researcher
            assignment = ProjectAssignment(
                user_id=user.id,
                project_id=project.id
            )
            db.session.add(assignment)
            
            # Create experiment in the project
            experiment = Experiment(
                exp_uid='test_exp_001',
                test_id=test.id,
                project_name=project.name,
                label='Test Subject',
                age=25,
                gender=1
            )
            db.session.add(experiment)
            db.session.commit()
        
        # Login as researcher
        client.post('/api/auth/login', json={
            'email': 'researcher_view@test.com',
            'password': 'password123'
        })
        
        response = client.get('/api/experiments')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        # Should see experiments from assigned projects
        experiment_uids = [exp['exp_uid'] for exp in data['experiments']]
        assert 'test_exp_001' in experiment_uids