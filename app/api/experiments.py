from flask import request, jsonify, send_file, make_response
from flask_login import current_user
from datetime import datetime
import io
import csv
import zipfile
import tempfile
import os
from app.api import bp
from app.models.experiment import Experiment
from app.services.experiment_service import get_experiments_service

from app.models.test import Test
from app.utils.decorators import researcher_required, test_access_required, log_access
from app import db
import logging


@bp.route('/experiments', methods=['GET'])
@researcher_required
@log_access('view_experiments')
def get_experiments():
    """Get experiments (filtered by user permissions)"""
    try:
        # Get query parameters
        test_id = request.args.get('test_id', type=int)
        device_id = request.args.get('device_id')
        label = request.args.get('label')
        completion_status = request.args.get('completion_status')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Parse dates
        date_from_obj = None
        date_to_obj = None
        if date_from:
            try:
                date_from_obj = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid date_from format'}), 400
        
        if date_to:
            try:
                date_to_obj = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid date_to format'}), 400
        
        # Prepare user permissions context
        user_permissions = {
            'is_admin': current_user.is_admin(),
            'assigned_test_ids': [assignment.test_id for assignment in current_user.test_assignments] if not current_user.is_admin() else []
        }
        
        # Use service to get experiments
        success, result, error_code = get_experiments_service(
            test_id=test_id,
            device_id=device_id,
            label=label,
            completion_status=completion_status,
            date_from=date_from_obj,
            date_to=date_to_obj,
            limit=limit,
            offset=offset,
            user_permissions=user_permissions
        )
        
        if not success:
            return jsonify({'error': result}), error_code
        
        return jsonify(result), 200

    except Exception as e:
        logging.error(f"Get experiments error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/experiments/<int:experiment_id>', methods=['GET'])
@researcher_required
@log_access('view_experiment')
def get_experiment(experiment_id):
    """Get specific experiment details"""
    try:
        # Prepare user permissions context
        user_permissions = {
            'is_admin': current_user.is_admin(),
            'assigned_test_ids': [assignment.test_id for assignment in current_user.test_assignments] if not current_user.is_admin() else []
        }
        
        # Use service to get experiment
        from app.services.experiment_service import get_experiment_by_id_service
        success, result, error_code = get_experiment_by_id_service(
            experiment_id=experiment_id,
            user_permissions=user_permissions
        )
        
        if not success:
            return jsonify({'error': result}), error_code
        
        return jsonify(result.to_dict(include_trials=True)), 200
        
    except Exception as e:
        logging.error(f"Get experiment error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/experiments/<int:experiment_id>/trials', methods=['GET'])
@researcher_required
@log_access('view_experiment_trials')
def get_experiment_trials(experiment_id):
    """Get trial data for specific experiment"""
    try:
        # Prepare user permissions context
        user_permissions = {
            'is_admin': current_user.is_admin(),
            'assigned_test_ids': [assignment.test_id for assignment in current_user.test_assignments] if not current_user.is_admin() else []
        }
        
        # Use service to get experiment (includes permission check)
        from app.services.experiment_service import get_experiment_by_id_service
        success, result, error_code = get_experiment_by_id_service(
            experiment_id=experiment_id,
            user_permissions=user_permissions
        )
        
        if not success:
            return jsonify({'error': result}), error_code
        
        experiment = result
        trials = experiment.get_trial_data_as_dict()
        
        return jsonify({
            'experiment_id': experiment_id,
            'trial_count': len(trials),
            'trials': trials
        }), 200
        
    except Exception as e:
        logging.error(f"Get experiment trials error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/experiments/download', methods=['GET'])
@researcher_required
@log_access('download_experiments')
def download_experiments():
    """Download selected experiments as files"""
    try:
        # Get experiment IDs from query parameters
        experiment_ids = request.args.getlist('experiment_ids')
        format_type = request.args.get('format', 'csv')  # csv or json
        
        if not experiment_ids:
            return jsonify({'error': 'No experiment IDs provided'}), 400
        
        # Convert to integers
        try:
            experiment_ids = [int(id) for id in experiment_ids]
        except ValueError:
            return jsonify({'error': 'Invalid experiment ID format'}), 400
        
        # Prepare user permissions context
        user_permissions = {
            'is_admin': current_user.is_admin(),
            'assigned_test_ids': [assignment.test_id for assignment in current_user.test_assignments] if not current_user.is_admin() else []
        }
        
        # Use service to export experiment data
        from app.services.experiment_service import export_experiment_data_service
        success, result, error_code = export_experiment_data_service(
            experiment_ids=experiment_ids,
            format=format_type,
            user_permissions=user_permissions
        )
        
        if not success:
            return jsonify({'error': result}), error_code
        
        # Create response based on format
        if format_type == 'csv':
            response = make_response(result)
            response.headers['Content-Type'] = 'application/zip'
            response.headers['Content-Disposition'] = f'attachment; filename="experiments_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip"'
        else:  # json
            response = make_response(result)
            response.headers['Content-Type'] = 'application/json'
            response.headers['Content-Disposition'] = f'attachment; filename="experiments_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json"'
        
        return response
        
    except Exception as e:
        logging.error(f"Download experiments error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/experiments/<int:experiment_id>', methods=['DELETE'])
@researcher_required
@log_access('delete_experiment')
def delete_experiment(experiment_id):
    """Delete an experiment"""
    try:
        # Prepare user permissions context
        user_permissions = {
            'is_admin': current_user.is_admin(),
            'assigned_test_ids': [assignment.test_id for assignment in current_user.test_assignments] if not current_user.is_admin() else []
        }
        
        # Use service to delete experiment
        from app.services.experiment_service import delete_experiment_service
        success, message, error_code = delete_experiment_service(
            experiment_id=experiment_id,
            user_permissions=user_permissions
        )
        
        if not success:
            return jsonify({'error': message}), error_code
        
        return jsonify({'message': message}), 200
        
    except Exception as e:
        logging.error(f"Delete experiment error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/experiments/stats', methods=['GET'])
@researcher_required
@log_access('view_experiment_stats')
def get_experiment_stats():
    """Get experiment statistics"""
    try:
        # Get accessible test IDs
        if current_user.is_admin():
            accessible_test_ids = [test.id for test in Test.query.all()]
        else:
            accessible_test_ids = [test.id for test in current_user.get_assigned_tests()]
        
        if not accessible_test_ids:
            return jsonify({
                'total_experiments': 0,
                'experiments_by_test': [],
                'experiments_by_status': [],
                'recent_experiments': []
            }), 200
        
        # Total experiments
        total_experiments = Experiment.query.filter(Experiment.test_id.in_(accessible_test_ids)).count()
        
        # Experiments by test
        experiments_by_test = db.session.query(
            Test.name,
            db.func.count(Experiment.id).label('count')
        ).join(Experiment).filter(Test.id.in_(accessible_test_ids)).group_by(Test.name).all()
        
        # Experiments by test status (since completion_status doesn't exist)
        experiments_by_status = db.session.query(
            Test.status,
            db.func.count(Experiment.id).label('count')
        ).join(Experiment).filter(Test.id.in_(accessible_test_ids)).group_by(Test.status).all()
        
        # Recent experiments
        recent_experiments = Experiment.query.filter(
            Experiment.test_id.in_(accessible_test_ids)
        ).order_by(db.desc(Experiment.uploaded_at)).limit(10).all()
        
        return jsonify({
            'total_experiments': total_experiments,
            'experiments_by_test': [{'test_name': name, 'count': count} for name, count in experiments_by_test],
            'experiments_by_status': [{'status': status or 'unknown', 'count': count} for status, count in experiments_by_status],
            'recent_experiments': [exp.to_dict() for exp in recent_experiments]
        }), 200
        
    except Exception as e:
        logging.error(f"Get experiment stats error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


def _generate_experiment_tsv(experiment):
    """Generate TSV content for an experiment"""
    try:
        # Get trial data
        trials = experiment.get_trial_data_as_dict()
        
        if not trials:
            return f"# No trial data for experiment {experiment.unique_id}\n"
        
        # Create TSV content
        output = io.StringIO()
        
        # Write header with experiment info
        output.write(f"# Experiment: {experiment.unique_id}\n")
        output.write(f"# Test: {experiment.test.name}\n")
        output.write(f"# Subject: {experiment.label}\n")
        output.write(f"# Age: {experiment.age}\n")
        output.write(f"# Gender: {experiment.get_gender_display()}\n")
        output.write(f"# Upload Date: {experiment.uploaded_at.isoformat() if experiment.uploaded_at else 'N/A'}\n")
        output.write(f"# Completion Status: {experiment.get_completion_status_display()}\n")
        output.write(f"# Device: {experiment.get_device_display()}\n")
        output.write(f"# Device ID: {experiment.device_id or 'Not registered'}\n")
        output.write("\n")
        
        # Write trial data as TSV
        if trials:
            # Get column names (excluding internal fields)
            columns = [col for col in trials[0].keys() if col not in ['id', 'experiment_id', 'created_at']]
            
            # Write TSV header
            writer = csv.DictWriter(output, fieldnames=columns, delimiter='\t')
            writer.writeheader()
            
            # Write trial data
            for trial in trials:
                # Filter out internal fields
                filtered_trial = {k: v for k, v in trial.items() if k in columns}
                writer.writerow(filtered_trial)
        
        return output.getvalue()
        
    except Exception as e:
        logging.error(f"Generate experiment TSV error: {e}")
        return f"# Error generating TSV for experiment {experiment.unique_id}: {str(e)}\n"