"""
Upload service module containing business logic for experiment upload operations.
This separates the business logic from the API request handling.
"""
from app.models.test import Test
from app.models.experiment import Experiment
from app.models.dynamic_models import get_trial_model
from app import db
from datetime import datetime
import logging
import json


def upload_experiment_service(exp_uid, test_class_name, configuration, trials, device_id, ip_address=None, user_agent=None):
    """
    Upload experiment data with validation and trial storage.
    
    Args:
        exp_uid (str): Unique experiment identifier
        test_class_name (str): Test class name
        configuration (dict): Experiment configuration
        trials (list): List of trial data
        device_id (str): Device identifier
        ip_address (str, optional): Client IP address for logging
        user_agent (str, optional): Client user agent for logging
    
    Returns:
        tuple: (success: bool, result: dict|str, error_code: int|None)
               - If success: (True, experiment_info_dict, None)
               - If error: (False, error_message, http_status_code)
    """
    try:
        # Validate required fields
        if not exp_uid or not exp_uid.strip():
            return False, 'exp_uid is required', 400
        
        if not test_class_name or not test_class_name.strip():
            return False, 'test_class_name is required', 400
        
        if not device_id or not device_id.strip():
            return False, 'device_id is required', 400
        
        exp_uid = exp_uid.strip()
        test_class_name = test_class_name.strip()
        device_id = device_id.strip()
        
        # Validate data types
        if not isinstance(configuration, dict):
            return False, 'configuration must be a dictionary', 400
        
        if not isinstance(trials, list):
            return False, 'trials must be a list', 400
        
        # Check for duplicate experiment
        existing_experiment = Experiment.get_by_exp_uid(exp_uid)
        if existing_experiment:
            return False, f'Experiment with exp_uid "{exp_uid}" already exists', 409
        
        # Find test by class name
        test = Test.get_by_class_name(test_class_name)
        if not test:
            return False, f'Test with class name "{test_class_name}" not found', 404
        
        # Check if test can accept experiments
        if not test.can_accept_experiments():
            return False, f'Test "{test.name}" is not accepting new experiments (status: {test.status})', 400
        
        # Validate configuration structure
        is_valid, error_msg = _validate_configuration(configuration)
        if not is_valid:
            return False, f'Invalid configuration: {error_msg}', 400
        
        # Log experiment upload for debugging
        logging.info(f"Experiment upload - ID: {exp_uid}, Test: {test_class_name}")
        logging.debug(f"Configuration fields: {list(configuration.keys())}")
        
        # Helper function to convert boolean to integer
        def bool_to_int(value):
            if isinstance(value, bool):
                return 1 if value else 0
            return value
        
        # Helper function to convert string to integer for trman_type
        def trman_type_to_int(value):
            if isinstance(value, str):
                # Map common string values to integers
                mapping = {
                    'standard': 0,
                    'adaptive': 1,
                    'fixed': 2
                }
                return mapping.get(value.lower(), 0)
            return value if isinstance(value, int) else 0
        
        # Create experiment record
        experiment = Experiment(
            exp_uid=exp_uid,
            test_id=test.id,
            device_id=device_id,
            
            # Main display fields
            label=configuration.get('label'),
            age=configuration.get('age'),
            gender=configuration.get('gender'),
            population=configuration.get('population'),
            session=configuration.get('session'),
            type=configuration.get('type'),
            date=configuration.get('date'),
            
            # Configuration fields (convert objects to JSON strings and booleans to integers)
            device=json.dumps(configuration.get('device')) if configuration.get('device') else None,
            vercode=configuration.get('vercode'),
            stimuli_delays=json.dumps(configuration.get('stimuliDelays')) if configuration.get('stimuliDelays') else None,
            whitenoise=bool_to_int(configuration.get('whitenoise')),
            trman_type=trman_type_to_int(configuration.get('trman_type')),
            show_result=bool_to_int(configuration.get('showResult')),
            can_repeat=bool_to_int(configuration.get('canRepeat')),
            do_training=bool_to_int(configuration.get('doTraining'))
        )
        
        # Set project information
        project_name = configuration.get('project')
        if project_name:
            experiment.set_project_by_name(project_name)
        
        db.session.add(experiment)
        db.session.flush()  # Get experiment ID
        
        # Store trial data
        trial_count = 0
        if trials:
            trial_model = get_trial_model(test.class_name)  # Use test.class_name for trial table operations
            if not trial_model:
                db.session.rollback()
                return False, f'Trial model not found for test class "{test.class_name}"', 500
            
            # Validate and store trials
            for i, trial_data in enumerate(trials):
                if not isinstance(trial_data, dict):
                    db.session.rollback()
                    return False, f'Trial {i + 1} must be a dictionary', 400
                
                # Create trial record
                trial_record = trial_model(
                    experiment_id=experiment.id,
                    trid=trial_data.get('trid', i + 1)
                )
                
                # Add trial data fields (skip reserved field names)
                reserved_fields = ['id', 'experiment_id', 'trid', 'created_at']
                for field_name, field_value in trial_data.items():
                    if field_name not in reserved_fields and hasattr(trial_record, field_name):
                        setattr(trial_record, field_name, field_value)
                
                db.session.add(trial_record)
                trial_count += 1
        
        db.session.commit()
        
        # Log the upload for audit trail
        _log_experiment_upload(experiment, ip_address, user_agent)
        
        return True, {
            'message': 'Experiment uploaded successfully',
            'experiment_id': experiment.id,
            'exp_uid': experiment.exp_uid,
            'device_id': experiment.device_id,
            'trial_count': trial_count
        }, None
        
    except Exception as e:
        logging.error(f"Upload experiment service error: {e}")
        db.session.rollback()
        return False, 'Internal server error', 500


def validate_upload_service(test_class_name, configuration):
    """
    Validate experiment data before upload.
    
    Args:
        test_class_name (str): Test class name
        configuration (dict): Experiment configuration
    
    Returns:
        tuple: (success: bool, result: dict|str, error_code: int|None)
    """
    try:
        if not test_class_name or not test_class_name.strip():
            return False, 'test_class_name is required', 400
        
        test_class_name = test_class_name.strip()
        
        # Find test
        test = Test.get_by_class_name(test_class_name)
        if not test:
            return False, f'Test with class name "{test_class_name}" not found', 404
        
        # Check test status
        if not test.can_accept_experiments():
            return False, f'Test "{test.name}" is not accepting new experiments (status: {test.status})', 400
        
        # Validate configuration
        is_valid, error_msg = _validate_configuration(configuration)
        if not is_valid:
            return False, f'Invalid configuration: {error_msg}', 400
        
        return True, {
            'valid': True,
            'test_name': test.name,
            'test_status': test.status
        }, None
        
    except Exception as e:
        logging.error(f"Validate upload service error: {e}")
        return False, 'Internal server error', 500


def get_upload_status_service():
    """
    Get upload service status and basic statistics.
    
    Returns:
        tuple: (success: bool, result: dict|str, error_code: int|None)
    """
    try:
        # Check database connectivity
        db.session.execute(db.text('SELECT 1'))
        
        # Get some basic stats
        total_experiments = Experiment.query.count()
        total_tests = Test.query.count()
        production_tests = Test.query.filter_by(status='production').count()
        
        return True, {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'stats': {
                'total_experiments': total_experiments,
                'total_tests': total_tests,
                'production_tests': production_tests
            }
        }, None
        
    except Exception as e:
        logging.error(f"Upload status service error: {e}")
        return False, 'Database connection failed', 500


def _validate_configuration(configuration):
    """
    Validate experiment configuration structure.
    
    Args:
        configuration (dict): Configuration to validate
    
    Returns:
        tuple: (is_valid: bool, error_message: str|None)
    """
    try:
        if not isinstance(configuration, dict):
            return False, 'Configuration must be a dictionary'
        
        # Check required fields
        required_fields = ['type', 'label']
        for field in required_fields:
            if field not in configuration:
                return False, f'Required field "{field}" missing from configuration'
        
        # Validate label
        label = configuration.get('label')
        if not isinstance(label, str) or not label.strip():
            return False, 'Label must be a non-empty string'
        
        # Validate type
        _type = configuration.get('type')
        if not isinstance(_type, int) or _type < 0:
            return False, 'Type must be a non-negative integer'
        
        # Validate optional fields if present
        if 'age' in configuration:
            age = configuration.get('age')
            if age is not None and (not isinstance(age, int) or age < 0 or age > 150):
                return False, 'Age must be an integer between 0 and 150'
        
        if 'gender' in configuration:
            gender = configuration.get('gender')
            if gender is not None and (not isinstance(gender, int) or gender not in [0, 1, 2]):
                return False, 'Gender must be 0 (female), 1 (male), or 2 (other)'
        
        if 'project' in configuration:
            project = configuration.get('project')
            if project is not None and (not isinstance(project, str) or len(project.strip()) > 100):
                return False, 'Project must be a string with maximum 100 characters'
        
        return True, None
        
    except Exception as e:
        logging.error(f"Configuration validation error: {e}")
        return False, f'Configuration validation failed: {str(e)}'


def _log_experiment_upload(experiment, ip_address, user_agent):
    """
    Log experiment upload for audit trail.
    
    Args:
        experiment (Experiment): Uploaded experiment
        ip_address (str): Client IP address
        user_agent (str): Client user agent
    """
    try:
        from app.models.user import AccessLog
        from flask_login import current_user
        
        # Log the experiment upload (anonymous from Android or authenticated user)
        user_id = None
        try:
            user_id = current_user.id if current_user.is_authenticated else None
        except:
            # current_user might not be available in API context
            user_id = None
        access_log = AccessLog(
            user_id=user_id,
            action='experiment_upload',
            resource=f'experiment:{experiment.exp_uid}',
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(access_log)
        db.session.commit()
        
    except Exception as e:
        logging.error(f"Error logging experiment upload: {e}")
        # Don't fail the upload if logging fails