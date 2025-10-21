from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.web import bp
from app.models.test import Test
from app.models.experiment import Experiment
from app.utils.decorators import researcher_required


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
    per_page = 20
    
    # Get experiments with pagination
    experiments_query = Experiment.query.filter_by(test_id=test_id).order_by(Experiment.uploaded_at.desc())
    experiments = experiments_query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('main/test_experiments.html', 
                         test=test, 
                         experiments=experiments)


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
    
    return jsonify(test.to_dict())

@bp.route('/debug-test')
def debug_test():
    """Simple route to test PyCharm debugging"""
    print("DEBUG: Debug test route accessed!")
    print("DEBUG: This should appear in PyCharm console")
    
    # Set a breakpoint on the next line
    message = "Breakpoint test - you should see this in console"
    print(f"DEBUG: {message}")
    
    return f"<h1>Debug Test</h1><p>{message}</p>"