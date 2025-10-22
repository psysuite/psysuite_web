"""Basic functionality tests."""
import json


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get('/api/health')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    assert 'database' in data


def test_login_page(client):
    """Test login page is accessible."""
    response = client.get('/login')
    assert response.status_code == 200


def test_api_login_success(client, admin_user):
    """Test successful API login."""
    response = client.post('/api/auth/login', 
        json={
            'email': 'admin@test.com',
            'password': 'test-admin-password'
        })
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'user' in data
    assert data['user']['email'] == 'admin@test.com'


def test_api_login_invalid(client):
    """Test login with invalid credentials."""
    response = client.post('/api/auth/login',
        json={
            'email': 'nonexistent@test.com',
            'password': 'wrongpassword'
        })
    
    assert response.status_code == 401


def test_password_hashing(app):
    """Test password hashing works correctly."""
    from app.models.user import User
    
    with app.app_context():
        user = User(email='test@example.com', role='researcher')
        user.set_password('plaintext_password')
        
        # Password should be hashed
        assert user.password_hash != 'plaintext_password'
        assert len(user.password_hash) > 50
        assert user.password_hash.startswith('pbkdf2:')
        
        # Should verify correct password
        assert user.check_password('plaintext_password')
        assert not user.check_password('wrongpassword')


def test_user_model(app):
    """Test User model basic functionality."""
    from app.models.user import User
    
    with app.app_context():
        user = User(email='test@example.com', role='admin', is_active=True)
        user.set_password('password123')
        
        assert user.email == 'test@example.com'
        assert user.role == 'admin'
        assert user.is_admin()
        assert not user.is_researcher()
        assert user.is_active == True


def test_test_model(app):
    """Test Test model basic functionality."""
    from app.models.test import Test
    
    with app.app_context():
        test = Test(
            name='Test Model Test',
            class_name='test.class.TestModel',
            description='A test for testing',
            status='development',
            trial_columns={
                'response_time': 'integer',
                'accuracy': 'float'
            }
        )
        
        assert test.name == 'Test Model Test'
        assert test.class_name == 'test.class.TestModel'
        assert test.status == 'development'
        assert test.trial_columns == {'response_time': 'integer', 'accuracy': 'float'}
        assert test.can_accept_experiments()
        assert not test.is_finalized()