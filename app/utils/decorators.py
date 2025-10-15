from functools import wraps
from flask import abort, jsonify, request
from flask_login import current_user
import logging


def admin_required(f):
    """Decorator to require admin role for access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            abort(401)
        
        if current_user.role != 'admin':
            if request.is_json:
                return jsonify({'error': 'Admin access required'}), 403
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function


def researcher_required(f):
    """Decorator to require authenticated user (admin or researcher)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            abort(401)
        
        return f(*args, **kwargs)
    return decorated_function


def test_access_required(f):
    """Decorator to check if user has access to a specific test"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            abort(401)
        
        # Get test_id from URL parameters or request data
        test_id = kwargs.get('test_id') or kwargs.get('id')
        if not test_id:
            # Try to get from request data
            if request.is_json:
                test_id = request.get_json().get('test_id')
            else:
                test_id = request.form.get('test_id')
        
        if test_id and not current_user.has_test_access(test_id):
            if request.is_json:
                return jsonify({'error': 'Access to this test is not allowed'}), 403
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function


def log_access(action, resource=None):
    """Decorator to log user access to resources"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Execute the function first
                result = f(*args, **kwargs)
                
                # Log the access if user is authenticated
                if current_user.is_authenticated:
                    from app.models.user import AccessLog
                    from app import db
                    
                    # Determine resource from kwargs or request
                    log_resource = resource
                    if not log_resource:
                        # Try to extract resource from URL parameters
                        if 'test_id' in kwargs:
                            log_resource = f"test:{kwargs['test_id']}"
                        elif 'experiment_id' in kwargs:
                            log_resource = f"experiment:{kwargs['experiment_id']}"
                        elif 'id' in kwargs:
                            log_resource = f"id:{kwargs['id']}"
                    
                    access_log = AccessLog(
                        user_id=current_user.id,
                        action=action,
                        resource=log_resource,
                        ip_address=request.remote_addr,
                        user_agent=request.headers.get('User-Agent')
                    )
                    db.session.add(access_log)
                    db.session.commit()
                
                return result
                
            except Exception as e:
                logging.error(f"Access logging error: {e}")
                # Don't fail the request due to logging errors
                return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def validate_json(required_fields=None):
    """Decorator to validate JSON request data"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({'error': 'Content-Type must be application/json'}), 400
            
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No JSON data provided'}), 400
            
            if required_fields:
                missing_fields = []
                for field in required_fields:
                    if field not in data or not data[field]:
                        missing_fields.append(field)
                
                if missing_fields:
                    return jsonify({
                        'error': f'Missing required fields: {", ".join(missing_fields)}'
                    }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator