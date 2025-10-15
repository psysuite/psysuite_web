from flask import request, jsonify
from flask_login import current_user
from app.api import bp
from app.models.user import User, TestAssignment
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
        users = User.query.all()
        
        return jsonify({
            'users': [user.to_dict() for user in users]
        }), 200
        
    except Exception as e:
        logging.error(f"Get users error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/users/<int:user_id>', methods=['GET'])
@admin_required
@log_access('view_user')
def get_user(user_id):
    """Get specific user details"""
    try:
        user = User.query.get_or_404(user_id)
        
        user_data = user.to_dict()
        user_data['assigned_tests'] = [test.to_dict() for test in user.get_assigned_tests()]
        
        return jsonify(user_data), 200
        
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
        
        # Validate required fields
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        role = data.get('role', '').lower()
        
        if not email or not password or not role:
            return jsonify({'error': 'Email, password, and role are required'}), 400
        
        # Validate email format
        if '@' not in email or '.' not in email:
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Validate role
        if role not in ['admin', 'researcher']:
            return jsonify({'error': 'Role must be either "admin" or "researcher"'}), 400
        
        # Validate password length
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'error': 'User with this email already exists'}), 400
        
        # Create user
        user = User(
            email=email,
            role=role,
            is_active=data.get('is_active', True)
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'User created successfully',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        logging.error(f"Create user error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/users/<int:user_id>', methods=['PUT'])
@admin_required
@validate_json()
@log_access('update_user')
def update_user(user_id):
    """Update an existing user"""
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        # Prevent admin from changing their own role
        if user.id == current_user.id and 'role' in data and data['role'] != user.role:
            return jsonify({'error': 'Cannot change your own role'}), 400
        
        # Update fields
        if 'email' in data:
            new_email = data['email'].strip().lower()
            if new_email != user.email:
                # Validate email format
                if '@' not in new_email or '.' not in new_email:
                    return jsonify({'error': 'Invalid email format'}), 400
                
                # Check if email already exists
                existing_user = User.query.filter_by(email=new_email).first()
                if existing_user:
                    return jsonify({'error': 'User with this email already exists'}), 400
                
                user.email = new_email
        
        if 'role' in data:
            role = data['role'].lower()
            if role not in ['admin', 'researcher']:
                return jsonify({'error': 'Role must be either "admin" or "researcher"'}), 400
            user.role = role
        
        if 'is_active' in data:
            # Prevent admin from deactivating themselves
            if user.id == current_user.id and not data['is_active']:
                return jsonify({'error': 'Cannot deactivate your own account'}), 400
            user.is_active = data['is_active']
        
        if 'password' in data:
            password = data['password']
            if len(password) < 6:
                return jsonify({'error': 'Password must be at least 6 characters long'}), 400
            user.set_password(password)
        
        db.session.commit()
        
        return jsonify({
            'message': 'User updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        logging.error(f"Update user error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
@log_access('delete_user')
def delete_user(user_id):
    """Delete a user"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Prevent admin from deleting themselves
        if user.id == current_user.id:
            return jsonify({'error': 'Cannot delete your own account'}), 400
        
        # Check if this is the last admin
        if user.role == 'admin':
            admin_count = User.query.filter_by(role='admin', is_active=True).count()
            if admin_count <= 1:
                return jsonify({'error': 'Cannot delete the last admin user'}), 400
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'message': 'User deleted successfully'}), 200
        
    except Exception as e:
        logging.error(f"Delete user error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/users/<int:user_id>/tests', methods=['GET'])
@admin_required
@log_access('view_user_tests')
def get_user_tests(user_id):
    """Get user's assigned tests"""
    try:
        user = User.query.get_or_404(user_id)
        
        if user.is_admin():
            # Admin has access to all tests
            tests = Test.query.all()
            assigned_test_ids = [test.id for test in tests]
        else:
            # Get assigned tests for researcher
            assignments = TestAssignment.query.filter_by(user_id=user_id).all()
            tests = [assignment.test for assignment in assignments]
            assigned_test_ids = [test.id for test in tests]
        
        # Get all available tests for assignment interface
        all_tests = Test.query.all()
        
        return jsonify({
            'assigned_tests': [test.to_dict() for test in tests],
            'assigned_test_ids': assigned_test_ids,
            'all_tests': [test.to_dict() for test in all_tests]
        }), 200
        
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
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        test_ids = data.get('test_ids', [])
        
        # Validate test IDs
        if not isinstance(test_ids, list):
            return jsonify({'error': 'test_ids must be a list'}), 400
        
        # Admin users don't need explicit test assignments
        if user.is_admin():
            return jsonify({
                'message': 'Admin users have access to all tests automatically'
            }), 200
        
        # Validate that all test IDs exist
        if test_ids:
            existing_tests = Test.query.filter(Test.id.in_(test_ids)).all()
            if len(existing_tests) != len(test_ids):
                return jsonify({'error': 'One or more test IDs are invalid'}), 400
        
        # Remove existing assignments
        TestAssignment.query.filter_by(user_id=user_id).delete()
        
        # Add new assignments
        for test_id in test_ids:
            assignment = TestAssignment(user_id=user_id, test_id=test_id)
            db.session.add(assignment)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Test assignments updated successfully',
            'assigned_test_ids': test_ids
        }), 200
        
    except Exception as e:
        logging.error(f"Update user tests error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/users/search', methods=['GET'])
@admin_required
@log_access('search_users')
def search_users():
    """Search users by email"""
    try:
        query = request.args.get('q', '').strip()
        
        if not query:
            return jsonify({'users': []}), 200
        
        # Search users by email
        users = User.query.filter(User.email.contains(query)).all()
        
        return jsonify({
            'users': [user.to_dict() for user in users]
        }), 200
        
    except Exception as e:
        logging.error(f"Search users error: {e}")
        return jsonify({'error': 'Internal server error'}), 500