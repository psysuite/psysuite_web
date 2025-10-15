from flask import request, jsonify
from datetime import datetime
from app.api import bp
from app.models.test import Test
from app.models.experiment import Experiment
from app.models.dynamic_models import get_trial_model
from app.utils.decorators import validate_json, log_access
from app import db
import logging
import uuid


@bp.route('/upload/experiment', methods=['POST'])
@validate_json(['unique_id', 'test_class_name', 'configuration', 'trials'])
def upload_experiment():
    """Upload experiment data from Android app"""
    try:
        data = request.get_json()
        
        # Extract required fields
        unique_id = data.get('unique_id', '').strip()
        test_class_name = data.get('test_class_name', '').strip()
        configuration = data.get('configuration', {})
        trials = data.get('trials', [])
        
        # Validate required fields
        if not unique_id or not test_class_name:
            return jsonify({'error': 'unique_id and test_class_name are required'}), 400
        
        if not isinstance(configuration, dict):
            return jsonify({'error': 'configuration must be a dictionary'}), 400
        
        if not isinstance(trials, list):
            return jsonify({'error': 'trials must be a list'}), 400
        
        # Check for duplicate experiment
        existing_experiment = Experiment.get_by_unique_id(unique_id)
        if existing_experiment:
            return jsonify({
                'error': 'Experiment with this unique_id already exists',
                'experiment_id': existing_experiment.id
            }), 409
        
        # Find test by class name
        test = Test.get_by_class_name(test_class_name)
        if not test:
            return jsonify({
                'error': f'Test with class name "{test_class_name}" not found'
            }), 404
        
        # Check if test can accept experiments
        if not test.can_accept_experiments():
            return jsonify({
                'error': f'Test "{test.name}" is not accepting new experiments (status: {test.status})'
            }), 400
        
        # Validate configuration structure
        if not _validate_configuration(configuration):
            return jsonify({'error': 'Invalid configuration structure'}), 400
        
        # Extract subject information from configuration
        subject_info = _extract_subject_info(configuration)
        
        # Create experiment record
        experiment = Experiment(
            unique_id=unique_id,
            test_id=test.id,
            subject_label=subject_info.get('label'),
            subject_age=subject_info.get('age'),
            subject_gender=subject_info.get('gender'),
            subject_population=subject_info.get('population'),
            test_type=subject_info.get('type'),
            test_block=subject_info.get('block'),
            completion_status=_determine_completion_status(configuration),
            device_info=subject_info.get('device'),
            app_version=subject_info.get('vercode'),
            stimuli_delays=subject_info.get('stimuliDelays'),
            experiment_date=datetime.utcnow(),
            configuration=configuration
        )
        
        db.session.add(experiment)
        db.session.flush()  # Get experiment ID
        
        # Store trial data
        if trials:
            trial_model = get_trial_model(test.name)
            if not trial_model:
                db.session.rollback()
                return jsonify({
                    'error': f'Trial model not found for test "{test.name}"'
                }), 500
            
            # Validate and store trials
            for i, trial_data in enumerate(trials):
                if not isinstance(trial_data, dict):
                    db.session.rollback()
                    return jsonify({
                        'error': f'Trial {i} must be a dictionary'
                    }), 400
                
                # Create trial record
                trial_record = trial_model(
                    experiment_id=experiment.id,
                    trial_number=trial_data.get('trial_number', i + 1)
                )
                
                # Add trial data fields
                for field_name, field_value in trial_data.items():
                    if field_name not in ['trial_number'] and hasattr(trial_record, field_name):
                        setattr(trial_record, field_name, field_value)
                
                db.session.add(trial_record)
        
        db.session.commit()
        
        # Log the upload
        _log_experiment_upload(experiment, request.remote_addr, request.headers.get('User-Agent'))
        
        return jsonify({
            'message': 'Experiment uploaded successfully',
            'experiment_id': experiment.id,
            'unique_id': experiment.unique_id,
            'trial_count': len(trials)
        }), 201
        
    except Exception as e:
        logging.error(f"Upload experiment error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/upload/validate', methods=['POST'])
@validate_json(['test_class_name', 'configuration'])
def validate_upload():
    """Validate experiment data before upload"""
    try:
        data = request.get_json()
        
        test_class_name = data.get('test_class_name', '').strip()
        configuration = data.get('configuration', {})
        
        # Find test
        test = Test.get_by_class_name(test_class_name)
        if not test:
            return jsonify({
                'valid': False,
                'error': f'Test with class name "{test_class_name}" not found'
            }), 200
        
        # Check test status
        if not test.can_accept_experiments():
            return jsonify({
                'valid': False,
                'error': f'Test "{test.name}" is not accepting new experiments (status: {test.status})'
            }), 200
        
        # Validate configuration
        if not _validate_configuration(configuration):
            return jsonify({
                'valid': False,
                'error': 'Invalid configuration structure'
            }), 200
        
        return jsonify({
            'valid': True,
            'test_name': test.name,
            'test_status': test.status
        }), 200
        
    except Exception as e:
        logging.error(f"Validate upload error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


def _validate_configuration(configuration):
    """Validate experiment configuration structure"""
    try:
        # Check required fields
        required_fields = ['classes', 'label']
        for field in required_fields:
            if field not in configuration:
                return False
        
        # Validate classes field
        classes = configuration.get('classes')
        if not isinstance(classes, list) or not classes:
            return False
        
        # Validate label
        label = configuration.get('label')
        if not isinstance(label, str) or not label.strip():
            return False
        
        return True
        
    except Exception:
        return False


def _extract_subject_info(configuration):
    """Extract subject information from configuration"""
    return {
        'label': configuration.get('label'),
        'age': configuration.get('age'),
        'gender': configuration.get('gender'),
        'population': configuration.get('population'),
        'type': configuration.get('type'),
        'block': configuration.get('block'),
        'device': configuration.get('device'),
        'vercode': configuration.get('vercode'),
        'stimuliDelays': configuration.get('stimuliDelays')
    }


def _determine_completion_status(configuration):
    """Determine completion status from configuration"""
    # This could be enhanced based on specific fields in configuration
    # For now, assume completed if configuration is present
    return 'completed'


def _log_experiment_upload(experiment, ip_address, user_agent):
    """Log experiment upload for audit trail"""
    try:
        from app.models.user import AccessLog
        
        # Create anonymous access log for experiment upload
        access_log = AccessLog(
            user_id=None,  # Anonymous upload from Android
            action='experiment_upload',
            resource=f'experiment:{experiment.unique_id}',
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(access_log)
        db.session.commit()
        
    except Exception as e:
        logging.error(f"Error logging experiment upload: {e}")


@bp.route('/upload/status', methods=['GET'])
def upload_status():
    """Get upload service status"""
    try:
        # Check database connectivity
        db.session.execute('SELECT 1')
        
        # Get some basic stats
        total_experiments = Experiment.query.count()
        total_tests = Test.query.count()
        production_tests = Test.query.filter_by(status='production').count()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'stats': {
                'total_experiments': total_experiments,
                'total_tests': total_tests,
                'production_tests': production_tests
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Upload status error: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': 'Database connection failed'
        }), 500