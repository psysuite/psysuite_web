"""
User service module containing business logic for user operations.
This separates the business logic from the API request handling.
"""
from app.models.user import User, ProjectAssignment
from app.models.project import Project
from app import db
import logging
import re


def get_all_users_service():
    """
    Get all users.
    
    Returns:
        tuple: (success: bool, result: list|str, error_code: int|None)
               - If success: (True, [user_dicts], None)
               - If error: (False, error_message, http_status_code)
    """
    try:
        users = User.query.all()
        return True, [user.to_dict() for user in users], None
        
    except Exception as e:
        logging.error(f"Get all users service error: {e}")
        return False, 'Internal server error', 500


def get_user_by_id_service(user_id):
    """
    Get a specific user by ID with assigned tests.
    
    Args:
        user_id (int): User ID
    
    Returns:
        tuple: (success: bool, result: dict|str, error_code: int|None)
    """
    try:
        user = User.query.get(user_id)
        if not user:
            return False, 'User not found', 404
        
        user_data = user.to_dict()
        user_data['assigned_projects'] = [assignment.project.to_dict() for assignment in user.project_assignments]
        
        return True, user_data, None
        
    except Exception as e:
        logging.error(f"Get user by ID service error: {e}")
        return False, 'Internal server error', 500


def create_user_service(email, password, role, is_active=True):
    """
    Create a new user with validation.
    
    Args:
        email (str): User email
        password (str): User password
        role (str): User role ('admin' or 'researcher')
        is_active (bool): Whether user is active
    
    Returns:
        tuple: (success: bool, result: User|str, error_code: int|None)
               - If success: (True, User instance, None)
               - If error: (False, error_message, http_status_code)
    """
    try:
        # Validate required fields
        if not email or not email.strip():
            return False, 'Email is required', 400
        
        if not password:
            return False, 'Password is required', 400
        
        if not role or not role.strip():
            return False, 'Role is required', 400
        
        # Clean and validate email
        email = email.strip().lower()
        if not _validate_email_format(email):
            return False, 'Invalid email format', 400
        
        # Validate role
        role = role.lower()
        if role not in ['admin', 'researcher']:
            return False, 'Role must be either "admin" or "researcher"', 400
        
        # Validate password length
        if len(password) < 6:
            return False, 'Password must be at least 6 characters long', 400
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return False, 'User with this email already exists', 400
        
        # Create user
        user = User(
            email=email,
            role=role,
            is_active=is_active
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        return True, user, None
        
    except Exception as e:
        logging.error(f"Create user service error: {e}")
        db.session.rollback()
        return False, 'Internal server error', 500


def update_user_service(user_id, email=None, password=None, role=None, is_active=None, current_user_id=None):
    """
    Update an existing user with validation.
    
    Args:
        user_id (int): User ID to update
        email (str, optional): New email
        password (str, optional): New password
        role (str, optional): New role
        is_active (bool, optional): New active status
        current_user_id (int, optional): ID of user making the change (for self-modification checks)
    
    Returns:
        tuple: (success: bool, result: User|str, error_code: int|None)
    """
    try:
        user = User.query.get(user_id)
        if not user:
            return False, 'User not found', 404
        
        # Prevent admin from changing their own role
        if current_user_id and user.id == current_user_id and role is not None and role != user.role:
            return False, 'Cannot change your own role', 400
        
        # Update email if provided
        if email is not None:
            new_email = email.strip().lower()
            if new_email != user.email:
                if not _validate_email_format(new_email):
                    return False, 'Invalid email format', 400
                
                # Check if email already exists
                existing_user = User.query.filter_by(email=new_email).first()
                if existing_user:
                    return False, 'User with this email already exists', 400
                
                user.email = new_email
        
        # Update role if provided
        if role is not None:
            role = role.lower()
            if role not in ['admin', 'researcher']:
                return False, 'Role must be either "admin" or "researcher"', 400
            user.role = role
        
        # Update active status if provided
        if is_active is not None:
            # Prevent admin from deactivating themselves
            if current_user_id and user.id == current_user_id and not is_active:
                return False, 'Cannot deactivate your own account', 400
            user.is_active = is_active
        
        # Update password if provided
        if password is not None:
            if len(password) < 6:
                return False, 'Password must be at least 6 characters long', 400
            user.set_password(password)
        
        db.session.commit()
        
        return True, user, None
        
    except Exception as e:
        logging.error(f"Update user service error: {e}")
        db.session.rollback()
        return False, 'Internal server error', 500


def delete_user_service(user_id, current_user_id=None):
    """
    Delete a user with validation.
    
    Args:
        user_id (int): User ID to delete
        current_user_id (int, optional): ID of user making the deletion (for self-deletion checks)
    
    Returns:
        tuple: (success: bool, message: str, error_code: int|None)
    """
    try:
        user = User.query.get(user_id)
        if not user:
            return False, 'User not found', 404
        
        # Prevent admin from deleting themselves
        if current_user_id and user.id == current_user_id:
            return False, 'Cannot delete your own account', 400
        
        # Check if this is the last admin
        if user.role == 'admin':
            admin_count = User.query.filter_by(role='admin', is_active=True).count()
            if admin_count <= 1:
                return False, 'Cannot delete the last admin user', 400
        
        db.session.delete(user)
        db.session.commit()
        
        return True, 'User deleted successfully', None
        
    except Exception as e:
        logging.error(f"Delete user service error: {e}")
        db.session.rollback()
        return False, 'Internal server error', 500


def get_user_tests_service(user_id):
    """
    Get user's assigned tests and all available tests.
    
    Args:
        user_id (int): User ID
    
    Returns:
        tuple: (success: bool, result: dict|str, error_code: int|None)
    """
    try:
        user = User.query.get(user_id)
        if not user:
            return False, 'User not found', 404
        
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
        
        return True, {
            'assigned_tests': [test.to_dict() for test in tests],
            'assigned_test_ids': assigned_test_ids,
            'all_tests': [test.to_dict() for test in all_tests]
        }, None
        
    except Exception as e:
        logging.error(f"Get user tests service error: {e}")
        return False, 'Internal server error', 500


def update_user_tests_service(user_id, test_ids):
    """
    Update user's test assignments.
    
    Args:
        user_id (int): User ID
        test_ids (list): List of test IDs to assign
    
    Returns:
        tuple: (success: bool, result: dict|str, error_code: int|None)
    """
    try:
        user = User.query.get(user_id)
        if not user:
            return False, 'User not found', 404
        
        # Validate test_ids
        if not isinstance(test_ids, list):
            return False, 'test_ids must be a list', 400
        
        # Admin users don't need explicit test assignments
        if user.is_admin():
            return True, {
                'message': 'Admin users have access to all tests automatically',
                'assigned_test_ids': []
            }, None
        
        # Validate that all test IDs exist
        if test_ids:
            existing_tests = Test.query.filter(Test.id.in_(test_ids)).all()
            if len(existing_tests) != len(test_ids):
                return False, 'One or more test IDs are invalid', 400
        
        # Remove existing assignments
        TestAssignment.query.filter_by(user_id=user_id).delete()
        
        # Add new assignments
        for test_id in test_ids:
            assignment = TestAssignment(user_id=user_id, test_id=test_id)
            db.session.add(assignment)
        
        db.session.commit()
        
        return True, {
            'message': 'Test assignments updated successfully',
            'assigned_test_ids': test_ids
        }, None
        
    except Exception as e:
        logging.error(f"Update user tests service error: {e}")
        db.session.rollback()
        return False, 'Internal server error', 500


def search_users_service(query):
    """
    Search users by email.
    
    Args:
        query (str): Search query
    
    Returns:
        tuple: (success: bool, result: list|str, error_code: int|None)
    """
    try:
        if not query or not query.strip():
            return True, [], None
        
        query = query.strip()
        
        # Search users by email
        users = User.query.filter(User.email.contains(query)).all()
        
        return True, [user.to_dict() for user in users], None
        
    except Exception as e:
        logging.error(f"Search users service error: {e}")
        return False, 'Internal server error', 500


def _validate_email_format(email):
    """
    Validate email format using regex.
    
    Args:
        email (str): Email to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    if not email:
        return False
    
    # Basic email validation regex
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None