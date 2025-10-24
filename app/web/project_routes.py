from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, session
from flask_login import login_required, current_user
from app.models.project import Project
from app.models.experiment import Experiment
from app import db
import logging

logger = logging.getLogger(__name__)

project_bp = Blueprint('projects', __name__, url_prefix='/admin/projects')


def admin_required(f):
    """Decorator to require admin access"""
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        
        if not current_user.is_admin:
            flash('Admin access required.', 'error')
            return redirect(url_for('web.dashboard'))
        
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function


@project_bp.route('/')
@login_required
@admin_required
def manage_projects():
    """Display project management page"""
    try:
        # First, let's try to get projects without counts to see if basic query works
        projects = Project.get_all_projects()
        logger.info(f"Found {len(projects)} projects")
        
        # Now try to get projects with counts
        projects_with_counts = Project.get_projects_with_counts()
        logger.info(f"Successfully got projects with counts: {len(projects_with_counts)}")
        
        return render_template('admin/projects.html', 
                             projects_with_counts=projects_with_counts)
    except Exception as e:
        logger.error(f"Error loading projects: {e}", exc_info=True)
        
        # Try to render the page with empty projects list as fallback
        try:
            return render_template('admin/projects.html', 
                                 projects_with_counts=[])
        except Exception as template_error:
            logger.error(f"Error rendering template: {template_error}", exc_info=True)
            flash('Error loading projects page', 'error')
            return redirect(url_for('web.dashboard'))


@project_bp.route('/create', methods=['POST'])
@login_required
@admin_required
def create_project():
    """Create a new project"""
    logger.info(f"Create project route accessed by {current_user.email}")
    logger.info(f"Form data: {request.form}")
    
    try:
        project_name = request.form.get('name', '').strip()
        logger.info(f"Project name from form: '{project_name}'")
        
        if not project_name:
            logger.warning("Project name is empty")
            flash('Project name is required', 'error')
            return redirect(url_for('projects.manage_projects'))
        
        logger.info(f"Attempting to create project: '{project_name}'")
        project, error = Project.create_project(
            name=project_name,
            created_by=current_user.email
        )
        
        if project:
            flash(f'Project "{project.name}" created successfully', 'success')
            logger.info(f"Project created successfully: {project.name} by {current_user.email}")
        else:
            flash(f'Error creating project: {error}', 'error')
            logger.warning(f"Failed to create project '{project_name}': {error}")
        
    except Exception as e:
        logger.error(f"Error creating project: {e}", exc_info=True)
        flash('Error creating project', 'error')
    
    return redirect(url_for('projects.manage_projects'))


@project_bp.route('/<int:project_id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_project(project_id):
    """Edit an existing project"""
    try:
        project = Project.get_project_by_id(project_id)
        if not project:
            flash('Project not found', 'error')
            return redirect(url_for('projects.manage_projects'))
        
        new_name = request.form.get('name', '').strip()
        
        if not new_name:
            flash('Project name is required', 'error')
            return redirect(url_for('projects.manage_projects'))
        
        success, message = project.update_name(new_name)
        
        if success:
            flash(message, 'success')
            logger.info(f"Project updated: {project.name} by {current_user.email}")
        else:
            flash(f'Error updating project: {message}', 'error')
            logger.warning(f"Failed to update project {project_id}: {message}")
        
    except Exception as e:
        logger.error(f"Error updating project {project_id}: {e}")
        flash('Error updating project', 'error')
    
    return redirect(url_for('projects.manage_projects'))


@project_bp.route('/<int:project_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_project(project_id):
    """Delete a project"""
    try:
        project = Project.get_project_by_id(project_id)
        if not project:
            flash('Project not found', 'error')
            return redirect(url_for('projects.manage_projects'))
        
        project_name = project.name
        success, message = project.delete()
        
        if success:
            flash(message, 'success')
            logger.info(f"Project deleted: {project_name} by {current_user.email}")
        else:
            flash(f'Error deleting project: {message}', 'error')
            logger.warning(f"Failed to delete project {project_id}: {message}")
        
    except Exception as e:
        logger.error(f"Error deleting project {project_id}: {e}")
        flash('Error deleting project', 'error')
    
    return redirect(url_for('projects.manage_projects'))


@project_bp.route('/api/list')
@login_required
def api_list_projects():
    """API endpoint to list all projects (for dropdowns, etc.)"""
    try:
        projects = Project.get_all_projects()
        return jsonify({
            'success': True,
            'projects': [{'id': p.id, 'name': p.name} for p in projects]
        })
    except Exception as e:
        logger.error(f"Error listing projects via API: {e}")
        return jsonify({
            'success': False,
            'error': 'Error loading projects'
        }), 500


@project_bp.route('/<int:project_id>/experiments')
@login_required
@admin_required
def project_experiments(project_id):
    """View experiments for a specific project"""
    try:
        project = Project.get_project_by_id(project_id)
        if not project:
            flash('Project not found', 'error')
            return redirect(url_for('projects.manage_projects'))
        
        experiments = Experiment.get_experiments_by_project(project.name)
        
        return render_template('admin/project_experiments.html',
                             project=project,
                             experiments=experiments)
    except Exception as e:
        logger.error(f"Error loading experiments for project {project_id}: {e}")
        flash('Error loading project experiments', 'error')
        return redirect(url_for('projects.manage_projects'))


@project_bp.route('/statistics')
@login_required
@admin_required
def project_statistics():
    """View project statistics"""
    try:
        stats = Experiment.get_project_statistics()
        total_experiments = sum(count for _, count in stats)
        
        return render_template('admin/project_statistics.html',
                             stats=stats,
                             total_experiments=total_experiments)
    except Exception as e:
        logger.error(f"Error loading project statistics: {e}")
        flash('Error loading project statistics', 'error')
        return redirect(url_for('projects.manage_projects'))


# Error handlers for the blueprint
@project_bp.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@project_bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500