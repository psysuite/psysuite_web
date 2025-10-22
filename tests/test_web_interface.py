"""Web interface functionality tests."""
import json


class TestWebInterface:
    """Test web interface pages and functionality."""
    
    def test_dashboard_requires_login(self, client):
        """Test that dashboard requires login."""
        response = client.get('/dashboard')
        # Should redirect to login
        assert response.status_code == 302
        assert '/login' in response.location
    
    def test_dashboard_access_after_login(self, client, admin_user):
        """Test dashboard access after login."""
        # Login first
        client.post('/api/auth/login', json={
            'email': 'admin@test.com',
            'password': 'test-admin-password'
        })
        
        response = client.get('/dashboard')
        assert response.status_code == 200
        assert b'dashboard' in response.data.lower()
    
    def test_test_list_page(self, client, admin_user, app):
        """Test test list page (dashboard shows tests)."""
        # Create a test within the test context
        with app.app_context():
            from app.models.test import Test
            from app import db
            test = Test(
                name='Dashboard Test',
                class_name='test.dashboard.TestDashboard',
                description='Test for dashboard',
                status='development',
                trial_columns={'response_time': 'integer'}
            )
            db.session.add(test)
            db.session.commit()
            test_name = test.name
        
        # Login first
        client.post('/api/auth/login', json={
            'email': 'admin@test.com',
            'password': 'test-admin-password'
        })
        
        # Dashboard shows the test list
        response = client.get('/dashboard')
        assert response.status_code == 200
        # Should contain test name
        assert test_name.encode() in response.data
    
    def test_test_detail_page(self, client, admin_user, app):
        """Test individual test experiments page."""
        # Create a test within the test context
        with app.app_context():
            from app.models.test import Test
            from app import db
            test = Test(
                name='Detail Test',
                class_name='test.detail.TestDetail',
                description='Test for detail view',
                status='development',
                trial_columns={'response_time': 'integer'}
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
        
        # Test experiments page
        response = client.get(f'/experiments/{test_id}')
        assert response.status_code == 200
        # Should contain test name
        assert test_name.encode() in response.data
    
    def test_experiment_list_page(self, client, admin_user, app):
        """Test experiment list page for a test."""
        # Create a test and experiment within the test context
        with app.app_context():
            from app.models.test import Test
            from app.models.experiment import Experiment
            from app import db
            
            test = Test(
                name='Experiment List Test',
                class_name='test.explist.TestExpList',
                description='Test for experiment list',
                status='development',
                trial_columns={'response_time': 'integer'}
            )
            db.session.add(test)
            db.session.commit()
            
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
            
            test_id = test.id
            participant_label = experiment.label
        
        # Login first
        client.post('/api/auth/login', json={
            'email': 'admin@test.com',
            'password': 'test-admin-password'
        })
        
        # Test experiments page shows experiments for the test
        response = client.get(f'/experiments/{test_id}')
        assert response.status_code == 200
        # Should contain the test name in the page title
        assert b'Experiment List Test' in response.data
    
    def test_experiment_detail_page(self, client, admin_user, app):
        """Test individual experiment detail page."""
        # Create a test and experiment within the test context
        with app.app_context():
            from app.models.test import Test
            from app.models.experiment import Experiment
            from app import db
            
            test = Test(
                name='Experiment Detail Test',
                class_name='test.expdetail.TestExpDetail',
                description='Test for experiment detail',
                status='development',
                trial_columns={'response_time': 'integer'}
            )
            db.session.add(test)
            db.session.commit()
            
            experiment = Experiment(
                test_id=test.id,
                exp_uid='DETAIL001_detail_session',
                device_id='detail_device',
                label='DETAIL001',
                age=30,
                gender=0,
                population=1,
                type=1,
                date='2024-01-02'
            )
            db.session.add(experiment)
            db.session.commit()
            
            experiment_id = experiment.id
            participant_label = experiment.label
        
        # Login first
        client.post('/api/auth/login', json={
            'email': 'admin@test.com',
            'password': 'test-admin-password'
        })
        
        # Single experiment page
        response = client.get(f'/experiment/{experiment_id}')
        assert response.status_code == 200
        # Should contain the experiment detail page content
        assert b'experiment' in response.data.lower()
    
    def test_test_creation_form(self, client, admin_user):
        """Test test creation form page."""
        # Login first
        client.post('/api/auth/login', json={
            'email': 'admin@test.com',
            'password': 'test-admin-password'
        })
        
        # Correct route for test creation
        response = client.get('/admin/test/new')
        assert response.status_code == 200
        # Should contain form elements
        assert b'form' in response.data.lower()
        assert b'name' in response.data.lower()
    
    def test_test_edit_form(self, client, admin_user, app):
        """Test test edit form page."""
        # Create a test within the test context
        with app.app_context():
            from app.models.test import Test
            from app import db
            test = Test(
                name='Edit Test',
                class_name='test.edit.TestEdit',
                description='Test for editing',
                status='development',
                trial_columns={'response_time': 'integer'}
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
        
        # Correct route for test editing
        response = client.get(f'/admin/test/{test_id}/edit')
        assert response.status_code == 200
        # Should contain form with existing data
        assert test_name.encode() in response.data
        assert b'form' in response.data.lower()
    
    def test_user_management_page(self, client, admin_user):
        """Test user management page (admin only)."""
        # Login as admin
        client.post('/api/auth/login', json={
            'email': 'admin@test.com',
            'password': 'test-admin-password'
        })
        
        # Correct route for user management
        response = client.get('/admin/users')
        assert response.status_code == 200
        # Should contain user management interface
        assert b'users' in response.data.lower()
    
    def test_researcher_cannot_access_user_management_page(self, client, app):
        """Test that researchers cannot access user management page."""
        # Create researcher user within test context
        with app.app_context():
            from app.models.user import User
            from app import db
            user = User(email='researcher_web@test.com', role='researcher')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
        
        # Login as researcher
        client.post('/api/auth/login', json={
            'email': 'researcher_web@test.com',
            'password': 'password123'
        })
        
        # Try to access admin users page
        response = client.get('/admin/users')
        assert response.status_code == 403
    
    def test_test_assignment_interface(self, client, admin_user, app):
        """Test test assignment interface."""
        # Create researcher user within test context
        with app.app_context():
            from app.models.user import User
            from app import db
            user = User(email='assign_web@test.com', role='researcher')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            user_id = user.id
        
        # Login as admin
        client.post('/api/auth/login', json={
            'email': 'admin@test.com',
            'password': 'test-admin-password'
        })
        
        # Correct route for test assignment
        response = client.get(f'/admin/user/{user_id}/assign-tests')
        assert response.status_code == 200
        # Should contain assignment interface
        assert b'assign' in response.data.lower()
    
    def test_logout_redirects_to_login(self, client, admin_user):
        """Test that logout redirects to login page."""
        # Login first
        client.post('/api/auth/login', json={
            'email': 'admin@test.com',
            'password': 'test-admin-password'
        })
        
        # Access logout via web interface
        response = client.get('/logout')
        assert response.status_code == 302
        assert '/login' in response.location