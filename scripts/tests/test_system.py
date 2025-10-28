#!/usr/bin/env python3
"""
Basic system test script for PsySuite Web Manager (need server on)
by default expect port 5001 (pycharm)
"""

import requests
import json
import sys
import time


def test_system(base_url="http://localhost:5001"):
    """Run basic system tests"""
    
    print(f"Testing PsySuite Web Manager at {base_url}")
    print("=" * 50)
    
    # Test 1: Health check
    print("1. Testing health check...")
    try:
        response = requests.get(f"{base_url}/api/health", timeout=10)
        if response.status_code == 200:
            print("✓ Health check passed")
            health_data = response.json()
            print(f"  Status: {health_data.get('status')}")
            print(f"  Database: {health_data.get('database')}")
        else:
            print(f"✗ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Health check error: {e}")
        return False
    
    # Test 2: Login page
    print("\n2. Testing login page...")
    try:
        response = requests.get(f"{base_url}/login", timeout=10)
        if response.status_code == 200:
            print("✓ Login page accessible")
        else:
            print(f"✗ Login page failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Login page error: {e}")
        return False
    
    # Test 3: API login
    print("\n3. Testing API login...")
    try:
        login_data = {
            "email": "alberto.inuggi@gmail.com",
            "password": "antares"
        }
        session = requests.Session()
        response = session.post(f"{base_url}/api/auth/login", 
                              json=login_data, 
                              timeout=10)
        
        if response.status_code == 200:
            print("✓ API login successful")
            user_data = response.json()
            print(f"  User: {user_data.get('user', {}).get('email')}")
            print(f"  Role: {user_data.get('user', {}).get('role')}")
        else:
            print(f"✗ API login failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ API login error: {e}")
        return False
    
    # Test 4: Get tests
    print("\n4. Testing tests API...")
    try:
        response = session.get(f"{base_url}/api/tests", timeout=10)
        if response.status_code == 200:
            print("✓ Tests API accessible")
            tests_data = response.json()
            print(f"  Tests count: {len(tests_data.get('tests', []))}")
        else:
            print(f"✗ Tests API failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Tests API error: {e}")
        return False
    
    # Test 5: Get experiments
    print("\n5. Testing experiments API...")
    try:
        response = session.get(f"{base_url}/api/experiments", timeout=10)
        if response.status_code == 200:
            print("✓ Experiments API accessible")
            exp_data = response.json()
            print(f"  Experiments count: {len(exp_data.get('experiments', []))}")
        else:
            print(f"✗ Experiments API failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Experiments API error: {e}")
        return False
    
    # Test 6: Dashboard access
    print("\n6. Testing dashboard access...")
    try:
        response = session.get(f"{base_url}/dashboard", timeout=10)
        if response.status_code == 200:
            print("✓ Dashboard accessible")
        else:
            print(f"✗ Dashboard failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Dashboard error: {e}")
        return False
    
    # Test 7: Upload validation
    print("\n7. Testing upload validation...")
    try:
        test_data = {
            "test_class_name": "TestDummy",
            "configuration": {
                "class_name": "TestDummy",
                "label": "test_subject"
            }
        }
        response = requests.post(f"{base_url}/api/upload/validate", 
                               json=test_data, 
                               timeout=10)
        
        if response.status_code == 200:
            validation_result = response.json()
            if validation_result.get('valid'):
                print("✓ Upload validation passed (test exists)")
            else:
                print("✓ Upload validation working (test not found - expected)")
                print(f"  Message: {validation_result.get('error')}")
        else:
            print(f"✗ Upload validation failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Upload validation error: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("✓ All basic tests passed!")
    print("\nSystem appears to be working correctly.")
    print("\nNext steps:")
    print("1. Access the web interface at:", base_url)
    print("2. Login with: alberto.inuggi@gmail.com / antares")
    print("3. Create a test and configure the Android app")
    print("4. Test data upload from the Android app")
    
    return True


if __name__ == '__main__':
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    
    print("Waiting for system to start...")
    time.sleep(2)
    
    success = test_system(base_url)
    sys.exit(0 if success else 1)