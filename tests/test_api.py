"""API endpoint tests."""
import json


def test_tests_api_requires_auth(client):
    """Test that tests API requires authentication."""
    response = client.get('/api/tests')
    # Should redirect to login or return 401
    assert response.status_code in [302, 401]


def test_experiments_api_requires_auth(client):
    """Test that experiments API requires authentication."""
    response = client.get('/api/experiments')
    # Should redirect to login or return 401
    assert response.status_code in [302, 401]


def test_authenticated_tests_api(client, admin_user):
    """Test tests API with authentication."""
    # Login first
    client.post('/api/auth/login', 
        json={
            'email': 'admin@test.com',
            'password': 'test-admin-password'
        })
    
    # Now access tests API
    response = client.get('/api/tests')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'tests' in data


def test_authenticated_experiments_api(client, admin_user):
    """Test experiments API with authentication."""
    # Login first
    client.post('/api/auth/login', 
        json={
            'email': 'admin@test.com',
            'password': 'test-admin-password'
        })
    
    # Now access experiments API
    response = client.get('/api/experiments')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'experiments' in data


def test_logout(client, admin_user):
    """Test logout functionality."""
    # Login first
    client.post('/api/auth/login', 
        json={
            'email': 'admin@test.com',
            'password': 'test-admin-password'
        })
    
    # Then logout
    response = client.post('/api/auth/logout')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'message' in data


def test_upload_validation(client):
    """Test upload validation endpoint."""
    test_data = {
        "test_class_name": "org.albaspazio.psysuite.tests.sample.TestSample",
        "configuration": {
            "classes": ["org.albaspazio.psysuite.tests.sample.TestSample"],
            "label": "test_subject"
        }
    }
    
    response = client.post('/api/upload/validate', 
                         json=test_data,
                         headers={'X-API-Key': 'test-api-key'})
    
    # Should work with API key authentication
    assert response.status_code == 200
    
    validation_result = response.json
    # Should indicate test not found (expected for non-existent test)
    assert 'valid' in validation_result