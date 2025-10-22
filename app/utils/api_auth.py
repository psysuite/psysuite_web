"""
API Authentication utilities for PsySuite Android app
"""
from functools import wraps
from flask import request, jsonify, current_app
import logging


def require_api_key(f):
    """
    Decorator to require API key authentication for PsySuite Android app endpoints.
    
    The API key should be provided in one of these ways:
    1. Header: X-API-Key: your-api-key
    2. Header: Authorization: Bearer your-api-key
    3. Query parameter: api_key=your-api-key
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = None
        
        # Try to get API key from different sources
        # 1. X-API-Key header
        api_key = request.headers.get('X-API-Key')
        
        # 2. Authorization Bearer header
        if not api_key:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                api_key = auth_header[7:]  # Remove 'Bearer ' prefix
        
        # 3. Query parameter
        if not api_key:
            api_key = request.args.get('api_key')
        
        # 4. JSON body (for POST requests)
        if not api_key and request.is_json:
            data = request.get_json(silent=True)
            if data:
                api_key = data.get('api_key')
        
        if not api_key:
            logging.warning(f"API key missing for {request.endpoint} from {request.remote_addr}")
            return jsonify({
                'error': 'API key required',
                'message': 'Please provide API key in X-API-Key header, Authorization Bearer header, or api_key parameter'
            }), 401
        
        # Validate API key
        expected_key = current_app.config.get('PSYSUITE_API_KEY')
        if api_key != expected_key:
            logging.warning(f"Invalid API key for {request.endpoint} from {request.remote_addr}: {api_key[:10]}...")
            return jsonify({
                'error': 'Invalid API key',
                'message': 'The provided API key is not valid'
            }), 401
        
        # API key is valid, proceed with the request
        logging.info(f"Valid API key used for {request.endpoint} from {request.remote_addr}")
        return f(*args, **kwargs)
    
    return decorated_function


def get_api_key_info():
    """
    Get information about API key configuration (for debugging/admin purposes)
    """
    expected_key = current_app.config.get('PSYSUITE_API_KEY')
    return {
        'api_key_configured': bool(expected_key),
        'api_key_length': len(expected_key) if expected_key else 0,
        'api_key_preview': expected_key[:8] + '...' if expected_key and len(expected_key) > 8 else 'Not configured'
    }