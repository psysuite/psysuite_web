"""
Test service module containing business logic for test operations.
This separates the business logic from the API request handling.
"""
from app.models.test import Test
from app.models.dynamic_models import create_trial_table, drop_trial_table
from app import db
import logging
from app.services.experiment_service import delete_test_experiments


def create_test_service(name, class_name, description='', trial_columns=None, status='development'):
    """
    Create a new test with validation and trial table creation.
    
    Args:
        name (str): Test name
        class_name (str): Test class name
        description (str): Test description
        trial_columns (dict): Trial columns configuration
        status (str): Test status (development, production, finalized)
    
    Returns:
        tuple: (success: bool, result: Test|str, error_code: int|None)
               - If success: (True, Test instance, None)
               - If error: (False, error_message, http_status_code)
    """
    try:
        # Validate required fields
        if not name or not name.strip():
            return False, 'Test name is required', 400
        
        if not class_name or not class_name.strip():
            return False, 'Test class_name is required', 400
        
        name = name.strip()
        class_name = class_name.strip()
        
        # Check if test name already exists
        existing_test = Test.query.filter_by(name=name).first()
        if existing_test:
            return False, 'Test name already exists', 400
        
        # Check if class name already exists
        existing_class = Test.query.filter_by(class_name=class_name).first()
        if existing_class:
            return False, 'Test class name already exists', 400
        
        # Set default trial columns if not provided
        if trial_columns is None:
            trial_columns = {
                'trid': 'integer',
                'label': 'string'
            }
        
        # Create test instance
        test = Test(
            name=name,
            class_name=class_name,
            description=description,
            status=status,
            trial_columns=trial_columns
        )
        
        # Validate trial columns
        is_valid, error_msg = test.validate_trial_columns()
        if not is_valid:
            return False, f'Invalid trial columns: {error_msg}', 400
        

        
        # Save test to database
        db.session.add(test)
        db.session.commit()
        
        # Create trial table
        if not create_trial_table(test.class_name, trial_columns):
            # Rollback test creation if table creation fails
            db.session.delete(test)
            db.session.commit()
            return False, 'Failed to create trial table', 500
        
        return True, test, None
        
    except Exception as e:
        logging.error(f"Create test service error: {e}")
        db.session.rollback()
        return False, 'Internal server error', 500


def delete_test_service(test_id, delete_all = False)-> tuple:
    """
    Delete a test and its associated trial table.
    Args:
        delete_all:
        test_id (int): Test ID
    Returns:
        tuple: (success: bool, message: str, error_code: int|None)
    """
    try:
        test = Test.query.get(test_id)
        if not test:
            return False, 'Test not found', 404

        # Check if test has experiments
        if test.get_experiment_count() > 0:
            if delete_all:
                res = delete_test_experiments(test_id)
            else:
                return False, 'Cannot delete test with existing experiments. Please delete experiments first.', 400

        test_class_name = test.class_name

        # Delete the test
        db.session.delete(test)
        db.session.commit()

        # Drop trial table
        drop_trial_table(test_class_name)

        return True, 'Test deleted successfully', None

    except Exception as e:
        logging.error(f"Delete test service error: {e}")
        db.session.rollback()
        return False, 'Internal server error', 500


def get_test_by_id(test_id):
    """
    Get a test by ID.
    Args:
        test_id (int): Test ID
    Returns:
        Test|None: Test instance or None if not found
    """
    return Test.query.get(test_id)


def get_test_by_name(name):
    """
    Get a test by name.
    Args:
        name (str): Test name
    Returns:
        Test|None: Test instance or None if not found
    """
    return Test.query.filter_by(name=name).first()


def get_test_by_class_name(class_name):
    """
    Get a test by class name.
    Args:
        class_name (str): Test class name
    Returns:
        Test|None: Test instance or None if not found
    """
    return Test.query.filter_by(class_name=class_name).first()


def get_all_tests():
    """
    Get all tests.
    Returns:
        list: List of Test instances
    """
    return Test.query.all()

