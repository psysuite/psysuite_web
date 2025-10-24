from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.web import bp
from app.models.test import Test
from app.models.experiment import Experiment
from app.utils.decorators import researcher_required
from app import db


@bp.route('/')
@bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard"""
    print("DEBUG: Dashboard route accessed")
    print(f"DEBUG: Current user: {current_user.email if current_user.is_authenticated else 'Anonymous'}")
    
    # Get tests based on user role
    if current_user.is_admin():
        print("DEBUG: User is admin, getting all tests")
        tests = Test.query.all()
    else:
        print("DEBUG: User is not admin, getting assigned tests")
        tests = current_user.get_assigned_tests()
    
    print(f"DEBUG: Found {len(tests)} tests")
    return render_template('main/dashboard.html', tests=tests)


@bp.route('/experiments/<int:test_id>')
@login_required
@researcher_required
def test_experiments(test_id):
    """View experiments for a specific test"""
    test = Test.query.get_or_404(test_id)
    
    # Check access permissions
    if not current_user.has_test_access(test_id):
        flash('Access denied to this test', 'error')
        return redirect(url_for('web.dashboard'))
    
    # Get query parameters for filtering
    page = request.args.get('page', 1, type=int)
    project_filter = request.args.get('project', '')
    per_page = 20
    
    # Build experiments query with project filtering
    experiments_query = Experiment.query.filter_by(test_id=test_id)
    
    # Apply project filter if specified
    if project_filter:
        if project_filter.lower() == 'none':
            # Show experiments with no project
            experiments_query = experiments_query.filter(
                (Experiment.project_name is None) |
                (Experiment.project_name == '') |
                (Experiment.project_name == 'No Project')
            )
        else:
            # Show experiments for specific project
            experiments_query = experiments_query.filter(Experiment.project_name == project_filter)
    
    experiments_query = experiments_query.order_by(Experiment.uploaded_at.desc())
    experiments = experiments_query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get available projects for the filter dropdown
    from app.models.project import Project
    available_projects = Project.get_all_projects()
    
    # Get project statistics for this test
    project_stats = Experiment.query.filter_by(test_id=test_id).with_entities(
        Experiment.project_name,
        db.func.count(Experiment.id).label('count')
    ).group_by(Experiment.project_name).all()
    
    return render_template('main/test_experiments.html', 
                         test=test, 
                         experiments=experiments,
                         available_projects=available_projects,
                         project_stats=project_stats,
                         current_project_filter=project_filter)


@bp.route('/experiment/<int:experiment_id>')
@login_required
@researcher_required
def single_experiment(experiment_id):
    """View single experiment details"""
    experiment = Experiment.query.get_or_404(experiment_id)
    
    # Check access permissions
    if not current_user.has_test_access(experiment.test_id):
        flash('Access denied to this experiment', 'error')
        return redirect(url_for('web.dashboard'))
    
    # Get trial data
    trials = experiment.get_trial_data_as_dict()
    
    return render_template('main/single_experiment.html', 
                         experiment=experiment, 
                         trials=trials)


@bp.route('/api/tests/<int:test_id>/parameters')
@login_required
def get_test_parameters(test_id):
    """Get test parameters for AJAX requests"""
    test = Test.query.get_or_404(test_id)
    
    # Check access permissions
    if not current_user.has_test_access(test_id):
        return jsonify({'error': 'Access denied'}), 403
    
    # Get the basic test data
    test_data = test.to_dict()
    
    # Replace trial_columns with ordered version and include order information
    test_data['trial_columns'] = test.ordered_trial_columns
    test_data['trial_columns_order'] = test.trial_columns_order
    
    return jsonify(test_data)

@bp.route('/debug-test')
def debug_test():
    """Simple route to test PyCharm debugging"""
    print("DEBUG: Debug test route accessed!")
    print("DEBUG: This should appear in PyCharm console")
    
    # Set a breakpoint on the next line
    message = "Breakpoint test - you should see this in console"
    print(f"DEBUG: {message}")
    
    return f"<h1>Debug Test</h1><p>{message}</p>"