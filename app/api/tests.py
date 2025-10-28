from flask import request, jsonify
from flask_login import current_user
from app.api import bp
from app.models.test import Test
from app.models.dynamic_models import create_trial_table, drop_trial_table, update_trial_table
from app.services.test_service import create_test_service, delete_test_service
from app.utils.decorators import admin_required, researcher_required, log_access, validate_json
from app.utils.api_auth import require_api_key
from app import db
import logging


@bp.route('/tests', methods=['GET'])
@researcher_required
@log_access('view_tests')
def get_tests():
    """Get all tests (filtered by user permissions)"""
    try:
        if current_user.is_admin():
            tests = Test.query.all()
        else:
            # Get only tests assigned to this researcher and in production
            tests = current_user.get_assigned_tests()
        
        return jsonify({
            'tests': [test.to_dict() for test in tests]
        }), 200
        
    except Exception as e:
        logging.error(f"Get tests error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/tests/<int:test_id>', methods=['GET'])
@researcher_required
@log_access('view_test')
def get_test(test_id):
    """Get specific test details"""
    try:
        test = Test.query.get_or_404(test_id)
        
        # Admin users can access all tests, researchers can access all tests too
        # (access control is now at the experiment level based on projects)
        if not current_user.is_admin() and not current_user.is_researcher():
            return jsonify({'error': 'Access denied'}), 403
        
        return jsonify(test.to_dict(include_experiments=True)), 200
        
    except Exception as e:
        logging.error(f"Get test error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/tests', methods=['POST'])
@admin_required
@validate_json(['name', 'class_name', 'trial_columns'])
@log_access('create_test')
def create_test():
    """Create a new test"""
    try:
        data = request.get_json()
        
        # Extract data from request
        name = data.get('name', '').strip()
        class_name = data.get('class_name', '').strip()
        description = data.get('description', '')
        trial_columns = data.get('trial_columns', {})
        status = data.get('status', 'development')
        
        # Use service to create test
        success, result, error_code = create_test_service(
            name=name,
            class_name=class_name,
            description=description,
            trial_columns=trial_columns,
            status=status
        )
        
        if not success:
            return jsonify({'error': result}), error_code
        
        return jsonify({
            'message': 'Test created successfully',
            'test': result.to_dict()
        }), 201
        
    except Exception as e:
        logging.error(f"Create test API error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/tests/<int:test_id>', methods=['PUT'])
@admin_required
@validate_json()
@log_access('update_test')
def update_test(test_id):
    """Update an existing test"""
    try:
        test = Test.query.get_or_404(test_id)
        data = request.get_json()
        
        # Store old trial columns for table update
        old_trial_columns = test.trial_columns.copy() if test.trial_columns else {}
        
        # Update fields
        if 'name' in data:
            new_name = data['name'].strip()
            if new_name != test.name:
                # Check if new name already exists
                existing_test = Test.query.filter_by(name=new_name).first()
                if existing_test:
                    return jsonify({'error': 'Test name already exists'}), 400
                test.name = new_name
        
        if 'class_name' in data:
            new_class_name = data['class_name'].strip()
            if new_class_name != test.class_name:
                # Check if new class name already exists
                existing_class = Test.query.filter_by(class_name=new_class_name).first()
                if existing_class:
                    return jsonify({'error': 'Test class name already exists'}), 400
                test.class_name = new_class_name
        
        if 'description' in data:
            test.description = data['description']
        
        if 'default_parameters' in data:
            test.default_parameters = data['default_parameters']
        
        if 'trial_columns' in data:
            test.trial_columns = data['trial_columns']
        
        # Validate updated data
        is_valid, error_msg = test.validate_trial_columns()
        if not is_valid:
            return jsonify({'error': error_msg}), 400

        db.session.commit()
        
        # Update trial table if columns changed
        if 'trial_columns' in data and data['trial_columns'] != old_trial_columns:
            if not update_trial_table(test.name, old_trial_columns, test.trial_columns):
                return jsonify({'error': 'Failed to update trial table'}), 500
        
        return jsonify({
            'message': 'Test updated successfully',
            'test': test.to_dict()
        }), 200
        
    except Exception as e:
        logging.error(f"Update test error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/tests/<int:test_id>', methods=['DELETE'])
@admin_required
@log_access('delete_test')
def delete_test(test_id):
    """Delete a test"""
    try:
        Test.query.get_or_404(test_id)
        res = delete_test_service(test_id, True)

        if res:
            return jsonify({'message': 'Test deleted successfully'}), 200
        else:
            return jsonify({
                'error': 'Cannot delete test with existing experiments. Please delete experiments first.'
            }), 400

        # Check if test has experiments
        if test.get_experiment_count() > 0:
            return jsonify({
                'error': 'Cannot delete test with existing experiments. Please delete experiments first.'
            }), 400
        
        test_name = test.name
        
        # Delete the test
        db.session.delete(test)
        db.session.commit()
        
        # Drop trial table
        drop_trial_table(test_name)
        

        
    except Exception as e:
        logging.error(f"Delete test error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/tests/<int:test_id>/status', methods=['PUT'])
@admin_required
@validate_json(['status'])
@log_access('update_test_status')
def update_test_status(test_id):
    """Update test status"""
    try:
        test = Test.query.get_or_404(test_id)
        data = request.get_json()
        
        new_status = data.get('status')
        valid_statuses = ['development', 'production', 'finalized']
        
        if new_status not in valid_statuses:
            return jsonify({
                'error': f'Invalid status. Valid options: {valid_statuses}'
            }), 400
        
        # Validate status transitions
        if test.status == 'finalized' and new_status != 'finalized':
            return jsonify({
                'error': 'Cannot change status of finalized test'
            }), 400
        
        test.status = new_status
        db.session.commit()
        
        return jsonify({
            'message': 'Test status updated successfully',
            'test': test.to_dict()
        }), 200
        
    except Exception as e:
        logging.error(f"Update test status error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/tests/search', methods=['GET'])
@researcher_required
@log_access('search_tests')
def search_tests():
    """Search tests by name or description"""
    try:
        query = request.args.get('q', '').strip()
        
        if not query:
            return jsonify({'tests': []}), 200
        
        # Search tests
        tests = Test.search_tests(query)
        
        # Filter by user permissions
        if not current_user.is_admin():
            user_test_ids = [test.id for test in current_user.get_assigned_tests()]
            tests = [test for test in tests if test.id in user_test_ids]
        
        return jsonify({
            'tests': [test.to_dict() for test in tests]
        }), 200
        
    except Exception as e:
        logging.error(f"Search tests error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/tests/public', methods=['GET'])
@require_api_key
def get_public_tests():
    """Get available tests for PsySuite Android app (requires API key)"""
    try:
        # Only return tests in production status
        tests = Test.query.filter_by(status='production').all()
        
        # Return simplified test data for Android app
        test_data = []
        for test in tests:
            test_data.append({
                'id': test.id,
                'name': test.name,
                'class_name': test.class_name,
                'description': test.description,
                'default_parameters': test.default_parameters,
                'trial_columns': test.trial_columns,
                'status': test.status,
                'created_at': test.created_at.isoformat() if test.created_at else None
            })
        
        return jsonify({
            'tests': test_data,
            'count': len(test_data)
        }), 200
        
    except Exception as e:
        logging.error(f"Get public tests error: {e}")
        return jsonify({'error': 'Internal server error'}), 500