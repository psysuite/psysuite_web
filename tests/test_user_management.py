"""User management functionality tests."""
import json
from app.models.user import User, TestAssignment
from app import db


class TestUserManagement:
    """Test user management and test assignment operations."""
    
    def test_get_all_users(self, client, admin_user):
        """Test getting all users (admin only)."""
        # Login as admin
        client.post('/api/auth/login', json={
            'email': 'admin@test.com',
            'password': 'test-admin-password'
        })
        
        response = client.get('/api/users')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'users' in data
        assert len(data['users']) >= 1
    
    def test_create_user(self, client, admin_user):
        """Test creating a new user."""
        # Login as admin
        client.post('/api/auth/login', json={
            'email': 'admin@test.com',
            'password': 'test-admin-password'
        })
        
        user_data = {
            'email': 'newuser@test.com',
            'role': 'researcher',
            'password': 'newpassword123'
        }
        
        response = client.post('/api/users', json=user_data)
        assert response.status_code == 201
        
        data = json.loads(response.data)
        assert data['user']['email'] == 'newuser@test.com'
        assert data['user']['role'] == 'researcher'
    
    def test_update_user(self, client, admin_user, app):
        """Test updating user information."""
        # Create a researcher user within the test context
        with app.app_context():
            user = User(email='update@test.com', role='researcher')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            user_id = user.id
        
        # Login as admin
        client.post('/api/auth/login', json={
            'email': 'admin@test.com',
            'password': 'test-admin-password'
        })
        
        update_data = {
            'role': 'admin',
            'is_active': False
        }
        
        response = client.put(f'/api/users/{user_id}', json=update_data)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['message'] == 'User updated successfully'
    
    def test_delete_user(self, client, admin_user, app):
        """Test deleting a user."""
        with app.app_context():
            # Create a user to delete
            user = User(
                email='delete@test.com',
                role='researcher',
                is_active=True
            )
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            user_id = user.id
        
        # Login as admin
        client.post('/api/auth/login', json={
            'email': 'admin@test.com',
            'password': 'test-admin-password'
        })
        
        response = client.delete(f'/api/users/{user_id}')
        assert response.status_code == 200
        
        # Verify user is deleted by checking the users list
        response = client.get('/api/users')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        user_emails = [user['email'] for user in data['users']]
        assert 'delete@test.com' not in user_emails
    
    def test_assign_test_to_user(self, client, admin_user, app):
        """Test assigning a test to a user."""
        # Create user and test within the test context
        with app.app_context():
            user = User(email='assign@test.com', role='researcher')
            user.set_password('password123')
            db.session.add(user)
            
            from app.models.test import Test
            test = Test(
                name='Assignment Test',
                class_name='test.class',
                description='Test for assignment',
                status='development'
            )
            db.session.add(test)
            db.session.commit()
            
            user_id = user.id
            test_id = test.id
        
        # Login as admin
        client.post('/api/auth/login', json={
            'email': 'admin@test.com',
            'password': 'test-admin-password'
        })
        
        assignment_data = {
            'test_ids': [test_id]
        }
        
        response = client.put(f'/api/users/{user_id}/tests', json=assignment_data)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'message' in data
    
    def test_get_user_assignments(self, client, admin_user, app):
        """Test getting all test assignments for a user."""
        with app.app_context():
            # Create user, test, and assignment
            user = User(email='assignments@test.com', role='researcher')
            user.set_password('password123')
            db.session.add(user)
            
            from app.models.test import Test
            test = Test(
                name='Assignment Test',
                class_name='test.class',
                description='Test for assignment',
                status='development'
            )
            db.session.add(test)
            db.session.commit()
            
            assignment = TestAssignment(
                user_id=user.id,
                test_id=test.id
            )
            db.session.add(assignment)
            db.session.commit()
            
            user_id = user.id
        
        # Login as admin
        client.post('/api/auth/login', json={
            'email': 'admin@test.com',
            'password': 'test-admin-password'
        })
        
        response = client.get(f'/api/users/{user_id}/tests')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'assigned_tests' in data
        assert len(data['assigned_tests']) >= 1
    
    def test_remove_test_assignment(self, client, admin_user, app):
        """Test removing a test assignment from a user."""
        with app.app_context():
            # Create user, test, and assignment
            user = User(email='remove@test.com', role='researcher')
            user.set_password('password123')
            db.session.add(user)
            
            from app.models.test import Test
            test = Test(
                name='Remove Test',
                class_name='test.class',
                description='Test for removal',
                status='development'
            )
            db.session.add(test)
            db.session.commit()
            
            assignment = TestAssignment(
                user_id=user.id,
                test_id=test.id
            )
            db.session.add(assignment)
            db.session.commit()
            
            user_id = user.id
        
        # Login as admin
        client.post('/api/auth/login', json={
            'email': 'admin@test.com',
            'password': 'test-admin-password'
        })
        
        # The API decorator doesn't allow empty test_ids, so let's test removal by
        # creating another test and then only assigning that one (effectively removing the first)
        with app.app_context():
            # Create another test
            test2 = Test(
                name='Another Test',
                class_name='test.class2',
                description='Another test',
                status='development'
            )
            db.session.add(test2)
            db.session.commit()
            test2_id = test2.id
        
        # Update assignments to only include the new test (removing the old one)
        response = client.put(f'/api/users/{user_id}/tests', json={'test_ids': [test2_id]})
        assert response.status_code == 200
        
        # Verify the original assignment is removed and only the new one remains
        response = client.get(f'/api/users/{user_id}/tests')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data['assigned_tests']) == 1
        assert data['assigned_tests'][0]['name'] == 'Another Test'
    
    def test_researcher_cannot_access_user_management(self, client, app):
        """Test that researchers cannot access user management endpoints."""
        # Create researcher user within test context
        with app.app_context():
            user = User(email='researcher_test@test.com', role='researcher')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
        
        # Login as researcher
        client.post('/api/auth/login', json={
            'email': 'researcher_test@test.com',
            'password': 'password123'
        })
        
        # Try to access users list
        response = client.get('/api/users')
        assert response.status_code == 403
        
        # Try to create user
        user_data = {'email': 'hack@test.com', 'role': 'admin', 'password': 'password123'}
        response = client.post('/api/users', json=user_data)
        assert response.status_code == 403
    
    def test_user_can_view_own_profile(self, client, app):
        """Test that users can view their own profile."""
        # Create researcher user within test context
        with app.app_context():
            user = User(email='profile@test.com', role='researcher')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
        
        # Login as researcher
        client.post('/api/auth/login', json={
            'email': 'profile@test.com',
            'password': 'password123'
        })
        
        response = client.get('/api/auth/me')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['user']['email'] == 'profile@test.com'
        assert data['user']['role'] == 'researcher'
    
    def test_user_can_reset_password(self, client, app):
        """Test that users can reset their password using the reset endpoint."""
        # Create researcher user within test context
        with app.app_context():
            user = User(email='reset@test.com', role='researcher')
            user.set_password('oldpassword123')
            db.session.add(user)
            db.session.commit()
        
        password_data = {
            'email': 'reset@test.com',
            'new_password': 'newpassword456',
            'confirm_password': 'newpassword456'
        }
        
        response = client.post('/api/auth/reset-password', json=password_data)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['message'] == 'Password reset successful'
        
        # Verify new password works
        response = client.post('/api/auth/login', json={
            'email': 'reset@test.com',
            'password': 'newpassword456'
        })
        assert response.status_code == 200