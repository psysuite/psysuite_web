"""Unit tests for user management system."""
import pytest
import json
from app import db
from app.models.user import User, TestAssignment


class TestUserCRUDAPI:
    """Test CRUD operations for user management."""
    
    def test_get_users_as_admin(self, client, app, admin_user, researcher_user):
        """Test getting all users as admin."""
        with app.app_context():
            # Login as admin
            client.post('/api/auth/login',
                json={
                    'email': 'admin@test.com',
                    'password': 'password123'
                })
            
            # Get users
            response = client.get('/api/users')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert 'users' in data
            assert len(data['users']) >= 2  # admin + researcher
            
            # Check user data structure
            user_emails = [user['email'] for user in data['users']]
            assert 'admin@test.com' in user_emails
            assert 'researcher@test.com' in user_emails
            
            # Verify sensitive data is not exposed
            for user in data['users']:
                assert 'password' not in user
                assert 'password_hash' not in user
    
    def test_get_users_as_researcher(self, client, app, researcher_user):
        """Test getting users as researcher (should fail)."""
        with app.app_context():
            # Login as researcher
            client.post('/api/auth/login',
                json={
                    'email': 'researcher@test.com',
                    'password': 'password123'
                })
            
            # Try to get users
            response = client.get('/api/users')
            assert response.status_code == 403
            
            data = json.loads(response.data)
            assert data['success'] is False
            assert 'Admin access required' in data['message']
    
    def test_get_users_unauthenticated(self, client, app):
        """Test getting users without authentication."""
        with app.app_context():
            response = client.get('/api/users')
            assert response.status_code == 401
    
    def test_create_user_as_admin(self, client, app, admin_user):
        """Test creating a new user as admin."""
        with app.app_context():
            # Login as admin
            client.post('/api/auth/login',
                json={
                    'email': 'admin@test.com',
                    'password': 'password123'
                })
            
            user_data = {
                'email': 'newuser@test.com',
                'password': 'newpassword123',
                'role': 'researcher'
            }
            
            # Create user
            response = client.post('/api/users', json=user_data)
            assert response.status_code == 201
            
            data = json.loads(response.data)
            assert data['success'] is True
            assert data['user']['email'] == 'newuser@test.com'
            assert data['user']['role'] == 'researcher'
            assert data['user']['is_active'] is True
            assert 'password' not in data['user']
            
            # Verify user was created in database
            user = User.query.filter_by(email='newuser@test.com').first()
            assert user is not None
            assert user.role == 'researcher'
            assert user.check_password('newpassword123')
    
    def test_create_user_as_researcher(self, client, app, researcher_user):
        """Test creating user as researcher (should fail)."""
        with app.app_context():
            # Login as researcher
            client.post('/api/auth/login',
                json={
                    'email': 'researcher@test.com',
                    'password': 'password123'
                })
            
            user_data = {
                'email': 'unauthorized@test.com',
                'password': 'password123',
                'role': 'researcher'
            }
            
            # Try to create user
            response = client.post('/api/users', json=user_data)
            assert response.status_code == 403
    
    def test_create_user_duplicate_email(self, client, app, admin_user, researcher_user):
        """Test creating user with duplicate email."""
        with app.app_context():
            # Login as admin
            client.post('/api/auth/login',
                json={
                    'email': 'admin@test.com',
                    'password': 'password123'
                })
            
            user_data = {
                'email': 'researcher@test.com',  # Already exists
                'password': 'password123',
                'role': 'researcher'
            }
            
            # Try to create user
            response = client.post('/api/users', json=user_data)
            assert response.status_code == 400
            
            data = json.loads(response.data)
            assert data['success'] is False
            assert 'already exists' in data['message']
    
    def test_create_user_invalid_data(self, client, app, admin_user):
        """Test creating user with invalid data."""
        with app.app_context():
            # Login as admin
            client.post('/api/auth/login',
                json={
                    'email': 'admin@test.com',
                    'password': 'password123'
                })
            
            # Missing required fields
            response = client.post('/api/users', json={})
            assert response.status_code == 400
            
            # Invalid email format
            response = client.post('/api/users', json={
                'email': 'invalid-email',
                'password': 'password123',
                'role': 'researcher'
            })
            assert response.status_code == 400
            
            # Invalid role
            response = client.post('/api/users', json={
                'email': 'test@test.com',
                'password': 'password123',
                'role': 'invalid_role'
            })
            assert response.status_code == 400
            
            # Weak password
            response = client.post('/api/users', json={
                'email': 'test@test.com',
                'password': '123',
                'role': 'researcher'
            })
            assert response.status_code == 400
    
    def test_get_single_user(self, client, app, admin_user, researcher_user):
        """Test getting a single user by ID."""
        with app.app_context():
            # Login as admin
            client.post('/api/auth/login',
                json={
                    'email': 'admin@test.com',
                    'password': 'password123'
                })
            
            # Get single user
            response = client.get(f'/api/users/{researcher_user.id}')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['user']['email'] == 'researcher@test.com'
            assert data['user']['role'] == 'researcher'
            assert data['user']['id'] == researcher_user.id
            assert 'password' not in data['user']
    
    def test_get_nonexistent_user(self, client, app, admin_user):
        """Test getting a nonexistent user."""
        with app.app_context():
            # Login as admin
            client.post('/api/auth/login',
                json={
                    'email': 'admin@test.com',
                    'password': 'password123'
                })
            
            # Get nonexistent user
            response = client.get('/api/users/99999')
            assert response.status_code == 404
    
    def test_update_user(self, client, app, admin_user, researcher_user):
        """Test updating a user."""
        with app.app_context():
            # Login as admin
            client.post('/api/auth/login',
                json={
                    'email': 'admin@test.com',
                    'password': 'password123'
                })
            
            update_data = {
                'email': 'updated@test.com',
                'role': 'admin',
                'is_active': False
            }
            
            # Update user
            response = client.put(f'/api/users/{researcher_user.id}', json=update_data)
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['success'] is True
            
            # Verify update in database
            user = User.query.get(researcher_user.id)
            assert user.email == 'updated@test.com'
            assert user.role == 'admin'
            assert user.is_active is False
    
    def test_update_user_password(self, client, app, admin_user, researcher_user):
        """Test updating user password."""
        with app.app_context():
            # Login as admin
            client.post('/api/auth/login',
                json={
                    'email': 'admin@test.com',
                    'password': 'password123'
                })
            
            update_data = {
                'password': 'newpassword456'
            }
            
            # Update user password
            response = client.put(f'/api/users/{researcher_user.id}', json=update_data)
            assert response.status_code == 200
            
            # Verify password was updated
            user = User.query.get(researcher_user.id)
            assert user.check_password('newpassword456')
            assert not user.check_password('password123')
    
    def test_update_user_as_researcher(self, client, app, researcher_user, admin_user):
        """Test updating user as researcher (should fail)."""
        with app.app_context():
            # Login as researcher
            client.post('/api/auth/login',
                json={
                    'email': 'researcher@test.com',
                    'password': 'password123'
                })
            
            # Try to update admin user
            response = client.put(f'/api/users/{admin_user.id}', 
                json={'email': 'unauthorized@test.com'})
            assert response.status_code == 403
    
    def test_delete_user(self, client, app, admin_user):
        """Test deleting a user."""
        with app.app_context():
            # Create user to delete
            user = User(email='delete@test.com', role='researcher')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            user_id = user.id
            
            # Login as admin
            client.post('/api/auth/login',
                json={
                    'email': 'admin@test.com',
                    'password': 'password123'
                })
            
            # Delete user
            response = client.delete(f'/api/users/{user_id}')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['success'] is True
            
            # Verify deletion
            deleted_user = User.query.get(user_id)
            assert deleted_user is None
    
    def test_delete_user_as_researcher(self, client, app, researcher_user, admin_user):
        """Test deleting user as researcher (should fail)."""
        with app.app_context():
            # Login as researcher
            client.post('/api/auth/login',
                json={
                    'email': 'researcher@test.com',
                    'password': 'password123'
                })
            
            # Try to delete admin user
            response = client.delete(f'/api/users/{admin_user.id}')
            assert response.status_code == 403


class TestTestAssignmentSystem:
    """Test test assignment functionality."""
    
    def test_get_user_tests(self, client, app, admin_user, researcher_user, sample_test):
        """Test getting user's assigned tests."""
        with app.app_context():
            # Assign test to researcher
            assignment = TestAssignment(
                user_id=researcher_user.id,
                test_id=sample_test.id
            )
            db.session.add(assignment)
            db.session.commit()
            
            # Login as admin
            client.post('/api/auth/login',
                json={
                    'email': 'admin@test.com',
                    'password': 'password123'
                })
            
            # Get user's tests
            response = client.get(f'/api/users/{researcher_user.id}/tests')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert 'tests' in data
            assert len(data['tests']) == 1
            assert data['tests'][0]['name'] == 'Sample Test'
    
    def test_get_user_tests_empty(self, client, app, admin_user, researcher_user):
        """Test getting user's tests when none assigned."""
        with app.app_context():
            # Login as admin
            client.post('/api/auth/login',
                json={
                    'email': 'admin@test.com',
                    'password': 'password123'
                })
            
            # Get user's tests
            response = client.get(f'/api/users/{researcher_user.id}/tests')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['tests'] == []
    
    def test_update_user_test_assignments(self, client, app, admin_user, researcher_user, sample_test):
        """Test updating user's test assignments."""
        with app.app_context():
            # Create additional test
            from app.models.test import Test
            test2 = Test(
                name='Second Test',
                class_name='test.second',
                status='development'
            )
            db.session.add(test2)
            db.session.commit()
            
            # Login as admin
            client.post('/api/auth/login',
                json={
                    'email': 'admin@test.com',
                    'password': 'password123'
                })
            
            # Assign tests to user
            assignment_data = {
                'test_ids': [sample_test.id, test2.id]
            }
            
            response = client.put(f'/api/users/{researcher_user.id}/tests', 
                json=assignment_data)
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['success'] is True
            
            # Verify assignments in database
            assignments = TestAssignment.query.filter_by(user_id=researcher_user.id).all()
            assert len(assignments) == 2
            assigned_test_ids = [a.test_id for a in assignments]
            assert sample_test.id in assigned_test_ids
            assert test2.id in assigned_test_ids
    
    def test_update_user_test_assignments_remove(self, client, app, admin_user, researcher_user, sample_test):
        """Test removing test assignments from user."""
        with app.app_context():
            # Initially assign test
            assignment = TestAssignment(
                user_id=researcher_user.id,
                test_id=sample_test.id
            )
            db.session.add(assignment)
            db.session.commit()
            
            # Login as admin
            client.post('/api/auth/login',
                json={
                    'email': 'admin@test.com',
                    'password': 'password123'
                })
            
            # Remove all assignments
            assignment_data = {
                'test_ids': []
            }
            
            response = client.put(f'/api/users/{researcher_user.id}/tests', 
                json=assignment_data)
            assert response.status_code == 200
            
            # Verify assignments were removed
            assignments = TestAssignment.query.filter_by(user_id=researcher_user.id).all()
            assert len(assignments) == 0
    
    def test_update_test_assignments_invalid_test_id(self, client, app, admin_user, researcher_user):
        """Test updating assignments with invalid test ID."""
        with app.app_context():
            # Login as admin
            client.post('/api/auth/login',
                json={
                    'email': 'admin@test.com',
                    'password': 'password123'
                })
            
            # Try to assign nonexistent test
            assignment_data = {
                'test_ids': [99999]
            }
            
            response = client.put(f'/api/users/{researcher_user.id}/tests', 
                json=assignment_data)
            assert response.status_code == 400
            
            data = json.loads(response.data)
            assert data['success'] is False
            assert 'Invalid test ID' in data['message']
    
    def test_update_test_assignments_as_researcher(self, client, app, researcher_user, admin_user):
        """Test updating test assignments as researcher (should fail)."""
        with app.app_context():
            # Login as researcher
            client.post('/api/auth/login',
                json={
                    'email': 'researcher@test.com',
                    'password': 'password123'
                })
            
            # Try to update assignments
            response = client.put(f'/api/users/{admin_user.id}/tests', 
                json={'test_ids': []})
            assert response.status_code == 403


class TestPasswordRecoverySystem:
    """Test password recovery functionality."""
    
    def test_password_reset_request(self, client, app, researcher_user):
        """Test password reset request."""
        with app.app_context():
            # Request password reset
            response = client.post('/api/auth/reset-password',
                json={'email': 'researcher@test.com'})
            
            # Should succeed even if we don't have email configured
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'reset instructions' in data['message']
    
    def test_password_reset_nonexistent_user(self, client, app):
        """Test password reset for nonexistent user."""
        with app.app_context():
            # Request password reset for nonexistent user
            response = client.post('/api/auth/reset-password',
                json={'email': 'nonexistent@test.com'})
            
            # Should still return success for security reasons
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['success'] is True
    
    def test_password_reset_invalid_email(self, client, app):
        """Test password reset with invalid email format."""
        with app.app_context():
            # Request password reset with invalid email
            response = client.post('/api/auth/reset-password',
                json={'email': 'invalid-email'})
            
            assert response.status_code == 400
            
            data = json.loads(response.data)
            assert data['success'] is False
            assert 'Invalid email format' in data['message']
    
    def test_password_reset_missing_email(self, client, app):
        """Test password reset without email."""
        with app.app_context():
            # Request password reset without email
            response = client.post('/api/auth/reset-password', json={})
            
            assert response.status_code == 400
            
            data = json.loads(response.data)
            assert data['success'] is False
            assert 'Email is required' in data['message']


class TestUserValidation:
    """Test user data validation."""
    
    def test_email_validation(self, client, app, admin_user):
        """Test email format validation."""
        with app.app_context():
            # Login as admin
            client.post('/api/auth/login',
                json={
                    'email': 'admin@test.com',
                    'password': 'password123'
                })
            
            invalid_emails = [
                'invalid-email',
                '@test.com',
                'test@',
                'test..test@example.com',
                'test@.com',
                ''
            ]
            
            for invalid_email in invalid_emails:
                response = client.post('/api/users', json={
                    'email': invalid_email,
                    'password': 'password123',
                    'role': 'researcher'
                })
                assert response.status_code == 400
    
    def test_password_validation(self, client, app, admin_user):
        """Test password strength validation."""
        with app.app_context():
            # Login as admin
            client.post('/api/auth/login',
                json={
                    'email': 'admin@test.com',
                    'password': 'password123'
                })
            
            weak_passwords = [
                '',
                '123',
                'abc',
                '12345',
                'password'  # Too common
            ]
            
            for weak_password in weak_passwords:
                response = client.post('/api/users', json={
                    'email': 'test@example.com',
                    'password': weak_password,
                    'role': 'researcher'
                })
                assert response.status_code == 400
    
    def test_role_validation(self, client, app, admin_user):
        """Test role validation."""
        with app.app_context():
            # Login as admin
            client.post('/api/auth/login',
                json={
                    'email': 'admin@test.com',
                    'password': 'password123'
                })
            
            # Valid roles
            for role in ['admin', 'researcher']:
                response = client.post('/api/users', json={
                    'email': f'{role}@example.com',
                    'password': 'validpassword123',
                    'role': role
                })
                assert response.status_code == 201
            
            # Invalid role
            response = client.post('/api/users', json={
                'email': 'invalid@example.com',
                'password': 'validpassword123',
                'role': 'invalid_role'
            })
            assert response.status_code == 400


class TestUserManagementIntegration:
    """Test user management integration with other components."""
    
    def test_user_deletion_cleans_up_assignments(self, client, app, admin_user, sample_test):
        """Test that user deletion cleans up test assignments."""
        with app.app_context():
            # Create user with test assignment
            user = User(email='cleanup@test.com', role='researcher')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            
            assignment = TestAssignment(
                user_id=user.id,
                test_id=sample_test.id
            )
            db.session.add(assignment)
            db.session.commit()
            
            user_id = user.id
            
            # Login as admin
            client.post('/api/auth/login',
                json={
                    'email': 'admin@test.com',
                    'password': 'password123'
                })
            
            # Delete user
            response = client.delete(f'/api/users/{user_id}')
            assert response.status_code == 200
            
            # Verify assignments were cleaned up
            assignments = TestAssignment.query.filter_by(user_id=user_id).all()
            assert len(assignments) == 0
    
    def test_user_deactivation_prevents_login(self, client, app, admin_user):
        """Test that deactivated users cannot login."""
        with app.app_context():
            # Create active user
            user = User(email='deactivate@test.com', role='researcher')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            user_id = user.id
            
            # Verify user can login initially
            response = client.post('/api/auth/login',
                json={
                    'email': 'deactivate@test.com',
                    'password': 'password123'
                })
            assert response.status_code == 200
            
            # Logout
            client.post('/api/auth/logout')
            
            # Login as admin and deactivate user
            client.post('/api/auth/login',
                json={
                    'email': 'admin@test.com',
                    'password': 'password123'
                })
            
            response = client.put(f'/api/users/{user_id}', 
                json={'is_active': False})
            assert response.status_code == 200
            
            # Logout admin
            client.post('/api/auth/logout')
            
            # Try to login as deactivated user
            response = client.post('/api/auth/login',
                json={
                    'email': 'deactivate@test.com',
                    'password': 'password123'
                })
            assert response.status_code == 401
            
            data = json.loads(response.data)
            assert 'Account is inactive' in data['message']