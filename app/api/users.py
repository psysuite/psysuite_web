from flask import request, jsonify
from flask_login import current_user
from app.api import bp
from app.models.user import User
from app.models.test import Test
from app.utils.decorators import admin_required, log_access, validate_json
from app import db
import logging


@bp.route('/users', methods=['GET'])
@admin_required
@log_access('view_users')
def get_users():
    """Get all users (admin only)"""
    try:
        from app.services.user_service import get_all_users_service
        success, result, error_code = get_all_users_service()
        
        if not success:
            return jsonify({'error': result}), error_code
        
        return jsonify({'users': result}), 200
        
    except Exception as e:
        logging.error(f"Get users error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/users/<int:user_id>', methods=['GET'])
@admin_required
@log_access('view_user')
def get_user(user_id):
    """Get specific user details"""
    try:
        from app.services.user_service import get_user_by_id_service
        success, result, error_code = get_user_by_id_service(user_id)
        
        if not success:
            return jsonify({'error': result}), error_code
        
        return jsonify(result), 200
        
    except Exception as e:
        logging.error(f"Get user error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/users', methods=['POST'])
@admin_required
@validate_json(['email', 'password', 'role'])
@log_access('create_user')
def create_user():
    """Create a new user"""
    try:
        data = request.get_json()
        
        # Extract data
        email = data.get('email', '')
        password = data.get('password', '')
        role = data.get('role', '')
        is_active = data.get('is_active', True)
        
        # Use service to create user
        from app.services.user_service import create_user_service
        success, result, error_code = create_user_service(
            email=email,
            password=password,
            role=role,
            is_active=is_active
        )
        
        if not success:
            return jsonify({'error': result}), error_code
        
        return jsonify({
            'message': 'User created successfully',
            'user': result.to_dict()
        }), 201
        
    except Exception as e:
        logging.error(f"Create user error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/users/<int:user_id>', methods=['PUT'])
@admin_required
@validate_json()
@log_access('update_user')
def update_user(user_id):
    """Update an existing user"""
    try:
        data = request.get_json()
        
        # Extract data
        email = data.get('email')
        password = data.get('password')
        role = data.get('role')
        is_active = data.get('is_active')
        
        # Use service to update user
        from app.services.user_service import update_user_service
        success, result, error_code = update_user_service(
            user_id=user_id,
            email=email,
            password=password,
            role=role,
            is_active=is_active,
            current_user_id=current_user.id
        )
        
        if not success:
            return jsonify({'error': result}), error_code
        
        return jsonify({
            'message': 'User updated successfully',
            'user': result.to_dict()
        }), 200
        
    except Exception as e:
        logging.error(f"Update user error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
@log_access('delete_user')
def delete_user(user_id):
    """Delete a user"""
    try:
        # Use service to delete user
        from app.services.user_service import delete_user_service
        success, message, error_code = delete_user_service(
            user_id=user_id,
            current_user_id=current_user.id
        )
        
        if not success:
            return jsonify({'error': message}), error_code
        
        return jsonify({'message': message}), 200
        
    except Exception as e:
        logging.error(f"Delete user error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/users/<int:user_id>/tests', methods=['GET'])
@admin_required
@log_access('view_user_tests')
def get_user_tests(user_id):
    """Get user's assigned tests"""
    try:
        from app.services.user_service import get_user_tests_service
        success, result, error_code = get_user_tests_service(user_id)
        
        if not success:
            return jsonify({'error': result}), error_code
        
        return jsonify(result), 200
        
    except Exception as e:
        logging.error(f"Get user tests error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/users/<int:user_id>/tests', methods=['PUT'])
@admin_required
@validate_json(['test_ids'])
@log_access('update_user_tests')
def update_user_tests(user_id):
    """Update user's test assignments"""
    try:
        data = request.get_json()
        test_ids = data.get('test_ids', [])
        
        # Use service to update user tests
        from app.services.user_service import update_user_tests_service
        success, result, error_code = update_user_tests_service(user_id, test_ids)
        
        if not success:
            return jsonify({'error': result}), error_code
        
        return jsonify(result), 200
        
    except Exception as e:
        logging.error(f"Update user tests error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/users/search', methods=['GET'])
@admin_required
@log_access('search_users')
def search_users():
    """Search users by email"""
    try:
        query = request.args.get('q', '')
        
        # Use service to search users
        from app.services.user_service import search_users_service
        success, result, error_code = search_users_service(query)
        
        if not success:
            return jsonify({'error': result}), error_code
        
        return jsonify({'users': result}), 200
        
    except Exception as e:
        logging.error(f"Search users error: {e}")
        return jsonify({'error': 'Internal server error'}), 500