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
        subject_label = request.args.get('subject_label')
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
        
        # Build query
        query = Experiment.query
        
        # Filter by test access permissions
        if current_user.is_admin():
            # Admin can see all experiments
            if test_id:
                query = query.filter_by(test_id=test_id)
        else:
            # Researcher can only see experiments from assigned tests
            assigned_test_ids = [test.id for test in current_user.get_assigned_tests()]
            if test_id:
                if test_id not in assigned_test_ids:
                    return jsonify({'error': 'Access denied to this test'}), 403
                query = query.filter_by(test_id=test_id)
            else:
                query = query.filter(Experiment.test_id.in_(assigned_test_ids))
        
        # Apply filters
        if subject_label:
            query = query.filter(Experiment.subject_label.contains(subject_label))
        
        if completion_status:
            query = query.filter_by(completion_status=completion_status)
        
        if date_from_obj:
            query = query.filter(Experiment.uploaded_at >= date_from_obj)
        
        if date_to_obj:
            query = query.filter(Experiment.uploaded_at <= date_to_obj)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination and ordering
        experiments = query.order_by(db.desc(Experiment.uploaded_at)).offset(offset).limit(limit).all()
        
        return jsonify({
            'experiments': [exp.to_dict() for exp in experiments],
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        }), 200
        
    except Exception as e:
        logging.error(f"Get experiments error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/experiments/<int:experiment_id>', methods=['GET'])
@researcher_required
@log_access('view_experiment')
def get_experiment(experiment_id):
    """Get specific experiment details"""
    try:
        experiment = Experiment.query.get_or_404(experiment_id)
        
        # Check access permissions
        if not current_user.has_test_access(experiment.test_id):
            return jsonify({'error': 'Access denied'}), 403
        
        return jsonify(experiment.to_dict(include_trials=True)), 200
        
    except Exception as e:
        logging.error(f"Get experiment error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/experiments/<int:experiment_id>/trials', methods=['GET'])
@researcher_required
@log_access('view_experiment_trials')
def get_experiment_trials(experiment_id):
    """Get trial data for specific experiment"""
    try:
        experiment = Experiment.query.get_or_404(experiment_id)
        
        # Check access permissions
        if not current_user.has_test_access(experiment.test_id):
            return jsonify({'error': 'Access denied'}), 403
        
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
        
        if not experiment_ids:
            return jsonify({'error': 'No experiment IDs provided'}), 400
        
        # Convert to integers
        try:
            experiment_ids = [int(id) for id in experiment_ids]
        except ValueError:
            return jsonify({'error': 'Invalid experiment ID format'}), 400
        
        # Get experiments
        experiments = Experiment.query.filter(Experiment.id.in_(experiment_ids)).all()
        
        if not experiments:
            return jsonify({'error': 'No experiments found'}), 404
        
        # Check access permissions
        for experiment in experiments:
            if not current_user.has_test_access(experiment.test_id):
                return jsonify({'error': f'Access denied to experiment {experiment.id}'}), 403
        
        # Single experiment - return TSV file
        if len(experiments) == 1:
            experiment = experiments[0]
            tsv_content = _generate_experiment_tsv(experiment)
            
            # Create response
            output = io.StringIO()
            output.write(tsv_content)
            output.seek(0)
            
            filename = f"{experiment.test.name}_{experiment.subject_label}_{experiment.unique_id}.tsv"
            
            response = make_response(output.getvalue())
            response.headers['Content-Type'] = 'text/tab-separated-values'
            response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
        
        # Multiple experiments - return ZIP file
        else:
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for experiment in experiments:
                    tsv_content = _generate_experiment_tsv(experiment)
                    filename = f"{experiment.test.name}_{experiment.subject_label}_{experiment.unique_id}.tsv"
                    zip_file.writestr(filename, tsv_content)
            
            zip_buffer.seek(0)
            
            response = make_response(zip_buffer.getvalue())
            response.headers['Content-Type'] = 'application/zip'
            response.headers['Content-Disposition'] = f'attachment; filename="experiments_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip"'
            
            return response
        
    except Exception as e:
        logging.error(f"Download experiments error: {e}")
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
        
        # Experiments by completion status
        experiments_by_status = db.session.query(
            Experiment.completion_status,
            db.func.count(Experiment.id).label('count')
        ).filter(Experiment.test_id.in_(accessible_test_ids)).group_by(Experiment.completion_status).all()
        
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
        output.write(f"# Subject: {experiment.subject_label}\n")
        output.write(f"# Age: {experiment.subject_age}\n")
        output.write(f"# Gender: {experiment.get_gender_display()}\n")
        output.write(f"# Upload Date: {experiment.uploaded_at.isoformat() if experiment.uploaded_at else 'N/A'}\n")
        output.write(f"# Completion Status: {experiment.get_completion_status_display()}\n")
        output.write(f"# Device: {experiment.get_device_display()}\n")
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