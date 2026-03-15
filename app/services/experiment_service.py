"""
Experiment service module containing business logic for experiment operations.
This separates the business logic from the API request handling.
"""
from app.models.experiment import Experiment
from app.models.test import Test
from app.models.dynamic_models import get_trial_model
from app import db
from datetime import datetime
import logging
import io
import csv
import zipfile
import tempfile
import os


def get_experiments_service(test_id=None, device_id=None, label=None,
                          completion_status=None, date_from=None, date_to=None, 
                          limit=50, offset=0, user_permissions=None):
    """
    Get experiments with filtering and pagination.
    
    Args:
        test_id (int, optional): Filter by test ID
        device_id (str, optional): Filter by device ID
        label (str, optional): Filter by subject label
        completion_status (str, optional): Filter by completion status
        date_from (datetime, optional): Filter experiments from this date
        date_to (datetime, optional): Filter experiments to this date
        limit (int): Maximum number of results (default: 50)
        offset (int): Number of results to skip (default: 0)
        user_permissions (dict, optional): User permission context
    
    Returns:
        tuple: (success: bool, result: dict|str, error_code: int|None)
               - If success: (True, {'experiments': [...], 'total': int}, None)
               - If error: (False, error_message, http_status_code)
    """
    try:
        # Build query
        query = Experiment.query
        
        # Apply filters
        if test_id:
            query = query.filter(Experiment.test_id == test_id)
        
        if device_id:
            query = query.filter(Experiment.device_id.ilike(f'%{device_id}%'))
        
        if label:
            query = query.filter(Experiment.label.ilike(f'%{label}%'))
        
        # Note: completion_status filtering not implemented as Experiment model doesn't have completed field
        # This could be implemented based on trial data or other criteria if needed
        
        if date_from:
            query = query.filter(Experiment.created_at >= date_from)
        
        if date_to:
            query = query.filter(Experiment.created_at <= date_to)
        
        # Apply user permissions if provided
        if user_permissions and not user_permissions.get('is_admin', False):
            # For researchers, filter by accessible projects
            accessible_project_names = user_permissions.get('accessible_project_names', [])
            if accessible_project_names:
                query = query.filter(Experiment.project_name.in_(accessible_project_names))
            else:
                # No accessible projects, return empty result
                return True, {'experiments': [], 'total': 0}, None
        
        # Get total count before pagination
        total = query.count()
        
        # Apply pagination
        experiments = query.offset(offset).limit(limit).all()
        
        # Convert to dict format
        experiments_data = []
        for exp in experiments:
            exp_dict = exp.to_dict()
            # Add test name for convenience
            if exp.test:
                exp_dict['test_name'] = exp.test.name
            experiments_data.append(exp_dict)
        
        return True, {
            'experiments': experiments_data,
            'total': total,
            'limit': limit,
            'offset': offset
        }, None
        
    except Exception as e:
        logging.error(f"Get experiments service error: {e}")
        return False, 'Internal server error', 500


def delete_test_experiments(test_id):
    exps = Experiment.query.filter(Experiment.test_id == test_id).all()
    for exp in exps:
        delete_experiment_service(exp.id)
    return True


def get_experiment_by_id_service(experiment_id, user_permissions=None):
    """
    Get a specific experiment by ID.
    
    Args:
        experiment_id (int): Experiment ID
        user_permissions (dict, optional): User permission context
    
    Returns:
        tuple: (success: bool, result: Experiment|str, error_code: int|None)
    """
    try:
        experiment = Experiment.query.get(experiment_id)
        if not experiment:
            return False, 'Experiment not found', 404
        
        # Check user permissions
        if user_permissions and not user_permissions.get('is_admin', False):
            accessible_project_names = user_permissions.get('accessible_project_names', [])
            if not experiment.project_name or experiment.project_name not in accessible_project_names:
                return False, 'Access denied', 403
        
        return True, experiment, None
        
    except Exception as e:
        logging.error(f"Get experiment by ID service error: {e}")
        return False, 'Internal server error', 500


def delete_experiment_service(experiment_id, user_permissions=None):
    """
    Delete an experiment and its trial data.
    
    Args:
        experiment_id (int): Experiment ID
        user_permissions (dict, optional): User permission context
    
    Returns:
        tuple: (success: bool, message: str, error_code: int|None)
    """
    try:
        experiment = Experiment.query.get(experiment_id)
        if not experiment:
            return False, 'Experiment not found', 404
        
        # Check user permissions
        if user_permissions and not user_permissions.get('is_admin', False):
            accessible_project_names = user_permissions.get('accessible_project_names', [])
            if not experiment.project_name or experiment.project_name not in accessible_project_names:
                return False, 'Access denied', 403
        
        # Get trial model to delete trial data
        test = experiment.test
        if test and test.class_name:
            trial_model = get_trial_model(test.class_name)
            if trial_model:
                # Delete all trials for this experiment
                trial_model.query.filter_by(experiment_id=experiment_id).delete()
        
        # Delete the experiment
        db.session.delete(experiment)
        db.session.commit()
        
        return True, 'Experiment deleted successfully', None
        
    except Exception as e:
        logging.error(f"Delete experiment service error: {e}")
        db.session.rollback()
        return False, 'Internal server error', 500


def delete_experiments_service(experiment_ids, user_permissions=None):
    """
    Delete multiple experiments and their trial data.
    
    Args:
        experiment_ids (list): List of experiment IDs to delete
        user_permissions (dict, optional): User permission context
    
    Returns:
        tuple: (success: bool, result: dict|str, error_code: int|None)
               - If success: (True, {'deleted': count, 'failed': count}, None)
               - If error: (False, error_message, http_status_code)
    """
    try:
        if not experiment_ids:
            return False, 'No experiment IDs provided', 400
        
        # Convert to integers
        try:
            experiment_ids = [int(id) for id in experiment_ids]
        except ValueError:
            return False, 'Invalid experiment ID format', 400
        
        # Only admins can delete experiments
        if user_permissions and not user_permissions.get('is_admin', False):
            return False, 'Admin access required to delete experiments', 403
        
        # Get experiments
        experiments = Experiment.query.filter(Experiment.id.in_(experiment_ids)).all()
        
        if not experiments:
            return False, 'No experiments found', 404
        
        deleted_count = 0
        failed_count = 0
        
        for experiment in experiments:
            try:
                # Get trial model to delete trial data
                test = experiment.test
                if test and test.class_name:
                    trial_model = get_trial_model(test.class_name)
                    if trial_model:
                        # Delete all trials for this experiment
                        trial_model.query.filter_by(experiment_id=experiment.id).delete()
                
                # Delete the experiment
                db.session.delete(experiment)
                deleted_count += 1
            except Exception as e:
                logging.error(f"Error deleting experiment {experiment.id}: {e}")
                failed_count += 1
        
        db.session.commit()
        
        return True, {'deleted': deleted_count, 'failed': failed_count}, None
        
    except Exception as e:
        logging.error(f"Delete experiments service error: {e}")
        db.session.rollback()
        return False, 'Internal server error', 500


def export_experiment_data_service(experiment_ids, format='csv', user_permissions=None):
    """
    Export experiment data in various formats.
    
    Args:
        experiment_ids (list): List of experiment IDs to export
        format (str): Export format ('csv', 'json')
        user_permissions (dict, optional): User permission context
    
    Returns:
        tuple: (success: bool, result: bytes|str, error_code: int|None)
               - If success: (True, file_data_bytes, None)
               - If error: (False, error_message, http_status_code)
    """
    try:
        if not experiment_ids:
            return False, 'No experiments specified for export', 400
        
        # Get experiments
        experiments = Experiment.query.filter(Experiment.id.in_(experiment_ids)).all()
        
        if not experiments:
            return False, 'No experiments found', 404
        
        # Check user permissions for all experiments
        if user_permissions and not user_permissions.get('is_admin', False):
            accessible_project_names = user_permissions.get('accessible_project_names', [])
            for exp in experiments:
                if not exp.project_name or exp.project_name not in accessible_project_names:
                    return False, 'Access denied to one or more experiments', 403
        
        if format == 'csv':
            return _export_experiments_csv(experiments)
        elif format == 'json':
            return _export_experiments_json(experiments)
        else:
            return False, 'Unsupported export format', 400
        
    except Exception as e:
        logging.error(f"Export experiment data service error: {e}")
        return False, 'Internal server error', 500


def _export_experiments_csv(experiments):
    """
    Export experiments to CSV format.
    
    Args:
        experiments (list): List of Experiment objects
    
    Returns:
        tuple: (success: bool, result: bytes, error_code: int|None)
    """
    try:
        # Create a temporary file for the ZIP
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        
        with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for experiment in experiments:
                # Export experiment metadata
                exp_csv = io.StringIO()
                exp_writer = csv.writer(exp_csv)
                
                # Write experiment metadata
                exp_writer.writerow(['Experiment Metadata'])
                exp_writer.writerow(['ID', experiment.id])
                exp_writer.writerow(['Unique ID', experiment.exp_uid])
                exp_writer.writerow(['Test', experiment.test.name if experiment.test else 'Unknown'])
                exp_writer.writerow(['Device ID', experiment.device_id])
                exp_writer.writerow(['Subject Label', experiment.label])
                exp_writer.writerow(['Age', experiment.age])
                exp_writer.writerow(['Gender', experiment.gender])
                exp_writer.writerow(['Population', experiment.population])
                exp_writer.writerow(['Type', experiment.type])
                exp_writer.writerow(['Date', experiment.date])
                exp_writer.writerow(['Uploaded At', experiment.uploaded_at])

                exp_writer.writerow([])
                
                # Export trial data if available
                if experiment.test and experiment.test.class_name:
                    trial_model = get_trial_model(experiment.test.class_name)
                    if trial_model:
                        trials = trial_model.query.filter_by(experiment_id=experiment.id).all()
                        
                        if trials:
                            exp_writer.writerow(['Trial Data'])
                            
                            # Get column names from the first trial
                            if trials:
                                columns = [col.name for col in trial_model.__table__.columns]
                                exp_writer.writerow(columns)
                                
                                for trial in trials:
                                    row = [getattr(trial, col) for col in columns]
                                    exp_writer.writerow(row)
                
                # Add to ZIP
                filename = f'experiment_{experiment.id}_{experiment.exp_uid}.csv'
                zipf.writestr(filename, exp_csv.getvalue())
        
        # Read the ZIP file data
        with open(temp_zip.name, 'rb') as f:
            zip_data = f.read()
        
        # Clean up temporary file
        os.unlink(temp_zip.name)
        
        return True, zip_data, None
        
    except Exception as e:
        logging.error(f"CSV export error: {e}")
        return False, 'Failed to export CSV data', 500


def _export_experiments_json(experiments):
    """
    Export experiments to JSON format.
    
    Args:
        experiments (list): List of Experiment objects
    
    Returns:
        tuple: (success: bool, result: bytes, error_code: int|None)
    """
    try:
        import json
        
        export_data = []
        
        for experiment in experiments:
            exp_data = experiment.to_dict()
            
            # Add trial data if available
            if experiment.test and experiment.test.class_name:
                trial_model = get_trial_model(experiment.test.class_name)
                if trial_model:
                    trials = trial_model.query.filter_by(experiment_id=experiment.id).all()
                    exp_data['trials'] = []
                    
                    for trial in trials:
                        trial_dict = {}
                        for col in trial_model.__table__.columns:
                            trial_dict[col.name] = getattr(trial, col.name)
                        exp_data['trials'].append(trial_dict)
            
            export_data.append(exp_data)
        
        json_data = json.dumps(export_data, indent=2, default=str)
        return True, json_data.encode('utf-8'), None
        
    except Exception as e:
        logging.error(f"JSON export error: {e}")
        return False, 'Failed to export JSON data', 500