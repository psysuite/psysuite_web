from flask import request, jsonify, session
from flask_login import login_user, logout_user, current_user, login_required
from app.api import bp
from app.models.user import User, AccessLog
from app import db
import logging


@bp.route('/auth/login', methods=['POST'])
def login():
    """Login endpoint"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            # Log failed login attempt
            log_access('login_failed', f'email:{email}', request.remote_addr, request.headers.get('User-Agent'))
            return jsonify({'error': 'Invalid email or password'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'Account is disabled'}), 401
        
        # Login user
        login_user(user, remember=True)
        
        # Log successful login
        log_access('login', None, request.remote_addr, request.headers.get('User-Agent'), user.id)
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        logging.error(f"Login error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/auth/logout', methods=['POST'])
@login_required
def logout():
    """Logout endpoint"""
    try:
        # Log logout
        log_access('logout', None, request.remote_addr, request.headers.get('User-Agent'))
        
        logout_user()
        session.clear()
        
        return jsonify({'message': 'Logout successful'}), 200
        
    except Exception as e:
        logging.error(f"Logout error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/auth/me', methods=['GET'])
@login_required
def get_current_user():
    """Get current user information"""
    try:
        return jsonify({
            'user': current_user.to_dict(),
            'assigned_tests': [test.to_dict() for test in current_user.get_assigned_tests()]
        }), 200
        
    except Exception as e:
        logging.error(f"Get current user error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/auth/reset-password', methods=['POST'])
def reset_password():
    """Reset password endpoint (basic implementation)"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        email = data.get('email', '').strip().lower()
        new_password = data.get('new_password', '')
        confirm_password = data.get('confirm_password', '')
        
        if not email or not new_password or not confirm_password:
            return jsonify({'error': 'Email, new password, and confirmation are required'}), 400
        
        if new_password != confirm_password:
            return jsonify({'error': 'Passwords do not match'}), 400
        
        if len(new_password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Update password
        user.set_password(new_password)
        db.session.commit()
        
        # Log password reset
        log_access('password_reset', f'email:{email}', request.remote_addr, request.headers.get('User-Agent'))
        
        return jsonify({'message': 'Password reset successful'}), 200
        
    except Exception as e:
        logging.error(f"Password reset error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500


def log_access(action, resource=None, ip_address=None, user_agent=None, user_id=None):
    """Helper function to log user access"""
    try:
        if not user_id and current_user.is_authenticated:
            user_id = current_user.id
        
        if user_id:
            access_log = AccessLog(
                user_id=user_id,
                action=action,
                resource=resource,
                ip_address=ip_address,
                user_agent=user_agent
            )
            db.session.add(access_log)
            db.session.commit()
    except Exception as e:
        logging.error(f"Access logging error: {e}")
        db.session.rollback()