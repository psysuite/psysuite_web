from datetime import datetime
from app import db


class Project(db.Model):
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    created_by = db.Column(db.String(50))  # Admin username who created the project
    
    def __repr__(self):
        return f'<Project {self.name}>'
    
    def to_dict(self):
        """Convert project to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by
        }
    
    @staticmethod
    def get_all_projects():
        """Get all projects ordered by name"""
        return Project.query.order_by(Project.name).all()
    
    @staticmethod
    def get_project_by_name(name):
        """Get project by name"""
        return Project.query.filter_by(name=name).first()
    
    @staticmethod
    def get_project_by_id(project_id):
        """Get project by ID"""
        return Project.query.get(project_id)
    
    @staticmethod
    def create_project(name, created_by=None):
        """Create a new project"""
        # Check if project already exists
        existing = Project.get_project_by_name(name)
        if existing:
            return None, "Project with this name already exists"
        
        # Validate name
        if not name or not name.strip():
            return None, "Project name cannot be empty"
        
        if len(name.strip()) > 100:
            return None, "Project name cannot exceed 100 characters"
        
        try:
            project = Project(
                name=name.strip(),
                created_by=created_by
            )
            db.session.add(project)
            db.session.commit()
            return project, None
        except Exception as e:
            db.session.rollback()
            return None, f"Error creating project: {str(e)}"
    
    def update_name(self, new_name):
        """Update project name"""
        if not new_name or not new_name.strip():
            return False, "Project name cannot be empty"
        
        if len(new_name.strip()) > 100:
            return False, "Project name cannot exceed 100 characters"
        
        # Check if another project with this name exists
        existing = Project.query.filter(
            Project.name == new_name.strip(),
            Project.id != self.id
        ).first()
        
        if existing:
            return False, "Another project with this name already exists"
        
        try:
            old_name = self.name
            self.name = new_name.strip()
            db.session.commit()
            
            # Update denormalized project_name in experiments table
            from app.models.experiment import Experiment
            experiments = Experiment.query.filter_by(project_id=self.id).all()
            for exp in experiments:
                exp.project_name = self.name
            db.session.commit()
            
            return True, f"Project renamed from '{old_name}' to '{self.name}'"
        except Exception as e:
            db.session.rollback()
            return False, f"Error updating project: {str(e)}"
    
    def delete(self):
        """Delete project"""
        try:
            # Check if there are experiments using this project
            from app.models.experiment import Experiment
            experiment_count = Experiment.query.filter_by(project_id=self.id).count()
            
            if experiment_count > 0:
                # Don't delete, but set project_id to None in experiments
                experiments = Experiment.query.filter_by(project_id=self.id).all()
                for exp in experiments:
                    exp.project_id = None
                    exp.project_name = "Deleted Project"
                
                db.session.delete(self)
                db.session.commit()
                return True, f"Project deleted. {experiment_count} experiments were updated to 'Deleted Project'"
            else:
                db.session.delete(self)
                db.session.commit()
                return True, "Project deleted successfully"
                
        except Exception as e:
            db.session.rollback()
            return False, f"Error deleting project: {str(e)}"
    
    def get_experiment_count(self):
        """Get number of experiments using this project"""
        from app.models.experiment import Experiment
        return Experiment.query.filter_by(project_id=self.id).count()
    
    @staticmethod
    def get_projects_with_counts():
        """Get all projects with their experiment counts"""
        try:
            from app.models.experiment import Experiment
            from sqlalchemy import func
            
            projects_with_counts = db.session.query(
                Project,
                func.count(Experiment.id).label('experiment_count')
            ).outerjoin(
                Experiment, Project.id == Experiment.project_id
            ).group_by(Project.id).order_by(Project.name).all()
            
            return [(project, count) for project, count in projects_with_counts]
        except Exception as e:
            # Fallback: return projects with zero counts if join fails
            projects = Project.get_all_projects()
            return [(project, 0) for project in projects]