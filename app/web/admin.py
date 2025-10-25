from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.web import bp
from app.models.test import Test
from app.models.user import User, ProjectAssignment
from app.models.dynamic_models import create_trial_table, drop_trial_table
from app.utils.decorators import admin_required
from app import db
import json


@bp.route('/admin/test/new', methods=['GET', 'POST'])
@login_required
@admin_required
def create_test():
    """Create new test"""
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            class_name = request.form.get('class_name', '').strip()
            description = request.form.get('description', '').strip()
            
            # Parse JSON fields
            trial_columns = {}

            try:
                if request.form.get('trial_columns'):
                    trial_columns = json.loads(request.form.get('trial_columns'))
            except json.JSONDecodeError:
                flash('Invalid JSON format for trial columns', 'error')
                return render_template('admin/test_editor.html')
            
            if not name or not class_name or not trial_columns:
                flash('Name, class name, and trial columns are required', 'error')
                return render_template('admin/test_editor.html')
            
            # Check for duplicates
            if Test.query.filter_by(name=name).first():
                flash('Test name already exists', 'error')
                return render_template('admin/test_editor.html')
            
            if Test.query.filter_by(class_name=class_name).first():
                flash('Test class name already exists', 'error')
                return render_template('admin/test_editor.html')
            
            # Create test
            test = Test(
                name=name,
                class_name=class_name,
                description=description,
                trial_columns=trial_columns
            )
            
            # Validate
            is_valid, error_msg = test.validate_trial_columns()
            if not is_valid:
                flash(f'Invalid trial columns: {error_msg}', 'error')
                return render_template('admin/test_editor.html')
            
            db.session.add(test)
            db.session.commit()
            
            # Create trial table
            if not create_trial_table(test.name, trial_columns):
                db.session.delete(test)
                db.session.commit()
                flash('Failed to create trial table', 'error')
                return render_template('admin/test_editor.html')
            
            flash('Test created successfully', 'success')
            return redirect(url_for('web.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating test: {str(e)}', 'error')
    
    return render_template('admin/test_editor.html')


@bp.route('/admin/test/<int:test_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_test(test_id):
    """Edit existing test"""
    test = Test.query.get_or_404(test_id)
    
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            class_name = request.form.get('class_name', '').strip()
            description = request.form.get('description', '').strip()
            status = request.form.get('status', 'development')
            
            # Validate status
            valid_statuses = ['development', 'production', 'finalized']
            if status not in valid_statuses:
                flash(f'Invalid status. Must be one of: {", ".join(valid_statuses)}', 'error')
                return render_template('admin/test_editor.html', test=test)
            
            # Parse JSON fields
            trial_columns = {}
            
            try:
                if request.form.get('trial_columns'):
                    trial_columns = json.loads(request.form.get('trial_columns'))
            except json.JSONDecodeError:
                flash('Invalid JSON format for trial columns', 'error')
                return render_template('admin/test_editor.html', test=test)
            
            if not name or not class_name or not trial_columns:
                flash('Name, class name, and trial columns are required', 'error')
                return render_template('admin/test_editor.html', test=test)
            
            # Check for duplicates (excluding current test)
            if Test.query.filter(Test.name == name, Test.id != test_id).first():
                flash('Test name already exists', 'error')
                return render_template('admin/test_editor.html', test=test)
            
            if Test.query.filter(Test.class_name == class_name, Test.id != test_id).first():
                flash('Test class name already exists', 'error')
                return render_template('admin/test_editor.html', test=test)
            
            # Update test
            old_trial_columns = test.trial_columns.copy() if test.trial_columns else {}
            
            test.name = name
            test.class_name = class_name
            test.description = description
            test.status = status
            test.trial_columns = trial_columns
            
            # Validate
            is_valid, error_msg = test.validate_trial_columns()
            if not is_valid:
                flash(f'Invalid trial columns: {error_msg}', 'error')
                return render_template('admin/test_editor.html', test=test)
            
            db.session.commit()
            
            # Update trial table if columns changed
            if trial_columns != old_trial_columns:
                from app.models.dynamic_models import update_trial_table
                if not update_trial_table(test.name, old_trial_columns, trial_columns):
                    flash('Warning: Failed to update trial table structure', 'warning')
            
            flash('Test updated successfully', 'success')
            return redirect(url_for('web.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating test: {str(e)}', 'error')
    
    return render_template('admin/test_editor.html', test=test)


@bp.route('/admin/users')
@login_required
@admin_required
def users():
    """User management page"""
    users = User.query.all()
    return render_template('admin/users.html', users=users)


@bp.route('/admin/user/new', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    """Create new user"""
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            role = request.form.get('role', '').lower()
            
            if not email or not password or not role:
                flash('All fields are required', 'error')
                return render_template('admin/user_editor.html')
            
            if '@' not in email or '.' not in email:
                flash('Invalid email format', 'error')
                return render_template('admin/user_editor.html')
            
            if role not in ['admin', 'researcher']:
                flash('Invalid role', 'error')
                return render_template('admin/user_editor.html')
            
            if len(password) < 6:
                flash('Password must be at least 6 characters long', 'error')
                return render_template('admin/user_editor.html')
            
            if User.query.filter_by(email=email).first():
                flash('User with this email already exists', 'error')
                return render_template('admin/user_editor.html')
            
            user = User(email=email, role=role)
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            flash('User created successfully', 'success')
            return redirect(url_for('web.users'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating user: {str(e)}', 'error')
    
    return render_template('admin/user_editor.html')





@bp.route('/admin/user/<int:user_id>/assign-projects', methods=['GET', 'POST'])
@login_required
@admin_required
def assign_projects(user_id):
    """Assign projects to user"""
    from app.models.project import Project
    
    user = User.query.get_or_404(user_id)
    
    if user.is_admin():
        flash('Admin users have access to all projects automatically', 'info')
        return redirect(url_for('web.users'))
    
    if request.method == 'POST':
        try:
            project_ids = request.form.getlist('project_ids')
            project_ids = [int(id) for id in project_ids if id.isdigit()]
            
            # Remove existing assignments
            ProjectAssignment.query.filter_by(user_id=user_id).delete()
            
            # Add new assignments
            for project_id in project_ids:
                if Project.query.get(project_id):  # Verify project exists
                    assignment = ProjectAssignment(user_id=user_id, project_id=project_id)
                    db.session.add(assignment)
            
            db.session.commit()
            flash('Project assignments updated successfully', 'success')
            return redirect(url_for('web.users'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating assignments: {str(e)}', 'error')
    
    # Get current assignments
    current_assignments = [a.project_id for a in user.project_assignments]
    all_projects = Project.query.all()
    
    return render_template('admin/assign_projects.html', 
                         user=user, 
                         all_projects=all_projects, 
                         current_assignments=current_assignments)