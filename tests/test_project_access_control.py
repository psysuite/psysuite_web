"""Project-based access control tests."""
import json
from app.models.user import User, ProjectAssignment
from app.models.project import Project
from app.models.test import Test
from app.models.experiment import Experiment
from app import db


class TestProjectAccessControl:
    """Test project-based access control functionality."""
    
    def test_admin_can_see_all_experiments(self, client, admin_user, app):
        """Test that admins can see all experiments regardless of project."""
        with app.app_context():
            # Create test and projects
            test = Test(
                name='Access Test',
                class_name='test.access.TestAccess',
                description='Test for access control',
                status='production'
            )
            db.session.add(test)
            
            project1 = Project(name='Project 1', created_by='admin')
            project2 = Project(name='Project 2', created_by='admin')
            db.session.add_all([project1, project2])
            db.session.commit()
            
            # Create experiments in different projects
            exp1 = Experiment(
                exp_uid='exp_001',
                test_id=test.id,
                project_name=project1.name,
                label='Subject 1'
            )
            exp2 = Experiment(
                exp_uid='exp_002',
                test_id=test.id,
                project_name=project2.name,
                label='Subject 2'
            )
            db.session.add_all([exp1, exp2])
            db.session.commit()
        
        # Login as admin
        client.post('/api/auth/login', json={
            'email': 'admin@test.com',
            'password': 'test-admin-password'
        })
        
        response = client.get('/api/experiments')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        experiment_uids = [exp['exp_uid'] for exp in data['experiments']]
        
        # Admin should see both experiments
        assert 'exp_001' in experiment_uids
        assert 'exp_002' in experiment_uids
    
    def test_researcher_sees_only_assigned_project_experiments(self, client, app):
        """Test that researchers only see experiments from their assigned projects."""
        with app.app_context():
            # Create researcher user
            researcher = User(email='researcher@test.com', role='researcher')
            researcher.set_password('password123')
            db.session.add(researcher)
            
            # Create test and projects
            test = Test(
                name='Access Test',
                class_name='test.access.TestAccess',
                description='Test for access control',
                status='production'
            )
            db.session.add(test)
            
            project1 = Project(name='Assigned Project', created_by='admin')
            project2 = Project(name='Other Project', created_by='admin')
            db.session.add_all([project1, project2])
            db.session.commit()
            
            # Assign only project1 to researcher
            assignment = ProjectAssignment(
                user_id=researcher.id,
                project_id=project1.id
            )
            db.session.add(assignment)
            
            # Create experiments in both projects
            exp1 = Experiment(
                exp_uid='assigned_exp',
                test_id=test.id,
                project_name=project1.name,
                label='Assigned Subject'
            )
            exp2 = Experiment(
                exp_uid='other_exp',
                test_id=test.id,
                project_name=project2.name,
                label='Other Subject'
            )
            db.session.add_all([exp1, exp2])
            db.session.commit()
        
        # Login as researcher
        client.post('/api/auth/login', json={
            'email': 'researcher@test.com',
            'password': 'password123'
        })
        
        response = client.get('/api/experiments')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        experiment_uids = [exp['exp_uid'] for exp in data['experiments']]
        
        # Researcher should only see experiment from assigned project
        assert 'assigned_exp' in experiment_uids
        assert 'other_exp' not in experiment_uids
    
    def test_researcher_cannot_see_experiments_without_project(self, client, app):
        """Test that researchers cannot see experiments without project assignment."""
        with app.app_context():
            # Create researcher user (no project assignments)
            researcher = User(email='researcher_no_projects@test.com', role='researcher')
            researcher.set_password('password123')
            db.session.add(researcher)
            
            # Create test and experiment without project
            test = Test(
                name='Access Test',
                class_name='test.access.TestAccess',
                description='Test for access control',
                status='production'
            )
            db.session.add(test)
            db.session.commit()
            
            exp = Experiment(
                exp_uid='no_project_exp',
                test_id=test.id,
                project_name=None,  # No project
                label='No Project Subject'
            )
            db.session.add(exp)
            db.session.commit()
        
        # Login as researcher
        client.post('/api/auth/login', json={
            'email': 'researcher_no_projects@test.com',
            'password': 'password123'
        })
        
        response = client.get('/api/experiments')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        experiment_uids = [exp['exp_uid'] for exp in data['experiments']]
        
        # Researcher should not see any experiments
        assert 'no_project_exp' not in experiment_uids
        assert len(experiment_uids) == 0
    
    def test_project_assignment_crud(self, client, admin_user, app):
        """Test project assignment CRUD operations."""
        with app.app_context():
            # Create researcher and project
            researcher = User(email='assign_test@test.com', role='researcher')
            researcher.set_password('password123')
            db.session.add(researcher)
            
            project = Project(name='Assignment Test Project', created_by='admin')
            db.session.add(project)
            db.session.commit()
            
            user_id = researcher.id
            project_id = project.id
        
        # Login as admin
        client.post('/api/auth/login', json={
            'email': 'admin@test.com',
            'password': 'test-admin-password'
        })
        
        # Test assignment
        response = client.put(f'/api/users/{user_id}/projects', json={
            'project_ids': [project_id]
        })
        assert response.status_code == 200
        
        # Verify assignment
        response = client.get(f'/api/users/{user_id}/projects')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data['assigned_projects']) == 1
        assert data['assigned_projects'][0]['name'] == 'Assignment Test Project'
        
        # Test removal (assign empty list)
        response = client.put(f'/api/users/{user_id}/projects', json={
            'project_ids': []
        })
        assert response.status_code == 200
        
        # Verify removal
        response = client.get(f'/api/users/{user_id}/projects')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data['assigned_projects']) == 0