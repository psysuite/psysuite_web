"""Unit tests for authentication system."""
import pytest
import json
from flask import url_for
from app import db
from app.models.user import User, AccessLog


class TestAuthenticationAPI:
    """Test authentication API endpoints."""
    
    def test_login_success(self, client, app, admin_user):
        """Test successful login."""
        with app.app_context():
            response = client.post('/api/auth/login', 
                json={
                    'email': 'admin@test.com',
                    'password': 'password123'
                })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert data['user']['email'] == 'admin@test.com'
            assert data['user']['role'] == 'admin'
            assert 'password' not in data['user']
            assert 'password_hash' not in data['user']
    
    def test_login_invalid_email(self, client, app):
        """Test login with invalid email."""
        with app.app_context():
            response = client.post('/api/auth/login',
                json={
                    'email': 'nonexistent@test.com',
                    'password': 'password123'
                })
            
            assert response.status_code == 401
            data = json.loads(response.data)
            assert data['success'] is False
            assert 'Invalid email or password' in data['message']
    
    def test_login_invalid_password(self, client, app, admin_user):
        """Test login with invalid password."""
        with app.app_context():
            response = client.post('/api/auth/login',
                json={
                    'email': 'admin@test.com',
                    'password': 'wrongpassword'
                })
            
            assert response.status_code == 401
            data = json.loads(response.data)
            assert data['success'] is False
            assert 'Invalid email or password' in data['message']
    
    def test_login_missing_fields(self, client, app):
        """Test login with missing fields."""
        with app.app_context():
            # Missing password
            response = client.post('/api/auth/login',
                json={'email': 'admin@test.com'})
            
            assert response.status_code == 400
            
            # Missing email
            response = client.post('/api/auth/login',
                json={'password': 'password123'})
            
            assert response.status_code == 400
            
            # Empty request
            response = client.post('/api/auth/login', json={})
            assert response.status_code == 400
    
    def test_login_creates_access_log(self, client, app, admin_user):
        """Test that login creates access log entry."""
        with app.app_context():
            # Count initial logs
            initial_count = AccessLog.query.count()
            
            response = client.post('/api/auth/login',
                json={
                    'email': 'admin@test.com',
                    'password': 'password123'
                })
            
            assert response.status_code == 200
            
            # Check that access log was created
            final_count = AccessLog.query.count()
            assert final_count == initial_count + 1
            
            # Verify log details
            log = AccessLog.query.order_by(AccessLog.timestamp.desc()).first()
            assert log.user_id == admin_user.id
            assert log.action == 'login'
    
    def test_logout(self, client, app, admin_user):
        """Test logout functionality."""
        with app.app_context():
            # Login first
            client.post('/api/auth/login',
                json={
                    'email': 'admin@test.com',
                    'password': 'password123'
                })
            
            # Then logout
            response = client.post('/api/auth/logout')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['success'] is True
            assert data['message'] == 'Logged out successfully'
    
    def test_logout_creates_access_log(self, client, app, admin_user):
        """Test that logout creates access log entry."""
        with app.app_context():
            # Login first
            client.post('/api/auth/login',
                json={
                    'email': 'admin@test.com',
                    'password': 'password123'
                })
            
            # Count logs before logout
            initial_count = AccessLog.query.count()
            
            # Logout
            response = client.post('/api/auth/logout')
            assert response.status_code == 200
            
            # Check that access log was created
            final_count = AccessLog.query.count()
            assert final_count == initial_count + 1
            
            # Verify log details
            log = AccessLog.query.order_by(AccessLog.timestamp.desc()).first()
            assert log.user_id == admin_user.id
            assert log.action == 'logout'
    
    def test_get_current_user_authenticated(self, client, app, admin_user):
        """Test getting current user when authenticated."""
        with app.app_context():
            # Login first
            client.post('/api/auth/login',
                json={
                    'email': 'admin@test.com',
                    'password': 'password123'
                })
            
            # Get current user
            response = client.get('/api/auth/me')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['user']['email'] == 'admin@test.com'
            assert data['user']['role'] == 'admin'
            assert 'password' not in data['user']
            assert 'password_hash' not in data['user']
    
    def test_get_current_user_unauthenticated(self, client, app):
        """Test getting current user when not authenticated."""
        with app.app_context():
            response = client.get('/api/auth/me')
            assert response.status_code == 401
            
            data = json.loads(response.data)
            assert data['success'] is False
            assert 'Not authenticated' in data['message']


class TestRoleBasedAccessControl:
    """Test role-based access control decorators."""
    
    def test_admin_required_with_admin(self, client, app, admin_user):
        """Test admin-required endpoint with admin user."""
        with app.app_context():
            # Login as admin
            client.post('/api/auth/login',
                json={
                    'email': 'admin@test.com',
                    'password': 'password123'
                })
            
            # Access admin-only endpoint (users list)
            response = client.get('/api/users')
            assert response.status_code == 200
    
    def test_admin_required_with_researcher(self, client, app, researcher_user):
        """Test admin-required endpoint with researcher user."""
        with app.app_context():
            # Login as researcher
            client.post('/api/auth/login',
                json={
                    'email': 'researcher@test.com',
                    'password': 'password123'
                })
            
            # Try to access admin-only endpoint
            response = client.get('/api/users')
            assert response.status_code == 403
            
            data = json.loads(response.data)
            assert data['success'] is False
            assert 'Admin access required' in data['message']
    
    def test_admin_required_unauthenticated(self, client, app):
        """Test admin-required endpoint without authentication."""
        with app.app_context():
            response = client.get('/api/users')
            assert response.status_code == 401
    
    def test_researcher_required_with_researcher(self, client, app, researcher_user):
        """Test researcher-required endpoint with researcher user."""
        with app.app_context():
            # Login as researcher
            client.post('/api/auth/login',
                json={
                    'email': 'researcher@test.com',
                    'password': 'password123'
                })
            
            # Access researcher endpoint (experiments list)
            response = client.get('/api/experiments')
            assert response.status_code == 200
    
    def test_researcher_required_with_admin(self, client, app, admin_user):
        """Test researcher-required endpoint with admin user."""
        with app.app_context():
            # Login as admin
            client.post('/api/auth/login',
                json={
                    'email': 'admin@test.com',
                    'password': 'password123'
                })
            
            # Access researcher endpoint (should work for admin too)
            response = client.get('/api/experiments')
            assert response.status_code == 200
    
    def test_researcher_required_unauthenticated(self, client, app):
        """Test researcher-required endpoint without authentication."""
        with app.app_context():
            response = client.get('/api/experiments')
            assert response.status_code == 401


class TestSessionManagement:
    """Test session management and security."""
    
    def test_session_persistence(self, client, app, admin_user):
        """Test that session persists across requests."""
        with app.app_context():
            # Login
            response = client.post('/api/auth/login',
                json={
                    'email': 'admin@test.com',
                    'password': 'password123'
                })
            assert response.status_code == 200
            
            # Make authenticated request
            response = client.get('/api/auth/me')
            assert response.status_code == 200
            
            # Make another authenticated request
            response = client.get('/api/tests')
            assert response.status_code == 200
    
    def test_session_cleared_on_logout(self, client, app, admin_user):
        """Test that session is cleared on logout."""
        with app.app_context():
            # Login
            client.post('/api/auth/login',
                json={
                    'email': 'admin@test.com',
                    'password': 'password123'
                })
            
            # Verify authenticated
            response = client.get('/api/auth/me')
            assert response.status_code == 200
            
            # Logout
            client.post('/api/auth/logout')
            
            # Verify no longer authenticated
            response = client.get('/api/auth/me')
            assert response.status_code == 401
    
    def test_inactive_user_cannot_login(self, client, app):
        """Test that inactive users cannot login."""
        with app.app_context():
            # Create inactive user
            user = User(email='inactive@test.com', role='researcher', is_active=False)
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            
            # Try to login
            response = client.post('/api/auth/login',
                json={
                    'email': 'inactive@test.com',
                    'password': 'password123'
                })
            
            assert response.status_code == 401
            data = json.loads(response.data)
            assert data['success'] is False
            assert 'Account is inactive' in data['message']


class TestPasswordSecurity:
    """Test password security features."""
    
    def test_password_hashing_on_creation(self, app):
        """Test that passwords are hashed on user creation."""
        with app.app_context():
            user = User(email='test@example.com', role='researcher')
            user.set_password('plaintext_password')
            
            # Password should be hashed
            assert user.password_hash != 'plaintext_password'
            assert len(user.password_hash) > 50  # bcrypt hashes are long
            assert user.password_hash.startswith('$2b$')  # bcrypt prefix
    
    def test_password_verification(self, app):
        """Test password verification."""
        with app.app_context():
            user = User(email='test@example.com', role='researcher')
            user.set_password('correct_password')
            
            # Correct password should verify
            assert user.check_password('correct_password')
            
            # Incorrect passwords should not verify
            assert not user.check_password('wrong_password')
            assert not user.check_password('')
            assert not user.check_password('CORRECT_PASSWORD')  # Case sensitive
    
    def test_password_change(self, app):
        """Test password change functionality."""
        with app.app_context():
            user = User(email='test@example.com', role='researcher')
            user.set_password('old_password')
            old_hash = user.password_hash
            
            # Change password
            user.set_password('new_password')
            
            # Hash should be different
            assert user.password_hash != old_hash
            
            # Old password should not work
            assert not user.check_password('old_password')
            
            # New password should work
            assert user.check_password('new_password')


class TestAuthenticationIntegration:
    """Test authentication integration with other components."""
    
    def test_login_with_test_access(self, client, app, researcher_user, sample_test):
        """Test login and access to assigned tests."""
        with app.app_context():
            # Assign test to researcher
            from app.models.user import TestAssignment
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
            
            # Should be able to access tests
            response = client.get('/api/tests')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert len(data['tests']) == 1
            assert data['tests'][0]['name'] == 'Sample Test'
    
    def test_access_logging_integration(self, client, app, admin_user):
        """Test that authentication actions are properly logged."""
        with app.app_context():
            initial_log_count = AccessLog.query.count()
            
            # Login
            client.post('/api/auth/login',
                json={
                    'email': 'admin@test.com',
                    'password': 'password123'
                })
            
            # Access some endpoints
            client.get('/api/tests')
            client.get('/api/users')
            
            # Logout
            client.post('/api/auth/logout')
            
            # Check that logs were created
            final_log_count = AccessLog.query.count()
            assert final_log_count > initial_log_count
            
            # Verify specific log entries
            logs = AccessLog.query.filter_by(user_id=admin_user.id).all()
            actions = [log.action for log in logs]
            assert 'login' in actions
            assert 'logout' in actions