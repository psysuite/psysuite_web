from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('admin', 'researcher', name='user_roles'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    access_logs = db.relationship('AccessLog', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """Check if user is admin"""
        return self.role == 'admin'
    
    def is_researcher(self):
        """Check if user is researcher"""
        return self.role == 'researcher'
    
    def get_all_tests(self):
        """Get all tests (access control is now project-based)"""
        from app.models.test import Test
        return Test.query.all()
    
    def get_accessible_project_names(self):
        """Get list of project names this user can access"""
        if self.is_admin():
            from app.models.project import Project
            return [p.name for p in Project.query.all()]
        else:
            # Return only projects assigned to this researcher
            return [assignment.project.name for assignment in self.project_assignments]
    
    def can_access_experiment(self, experiment):
        """Check if user can access a specific experiment based on project assignment"""
        if self.is_admin():
            return True
        
        if not experiment.project_name or experiment.project_name in ['No Project', '', None]:
            # Experiments without projects are only visible to admins
            return False
        
        accessible_project_names = self.get_accessible_project_names()
        return experiment.project_name in accessible_project_names
    
    def to_dict(self):
        """Convert user to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }






class ProjectAssignment(db.Model):
    __tablename__ = 'project_assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='project_assignments')
    project = db.relationship('Project', backref='user_assignments')
    
    # Unique constraint to prevent duplicate assignments
    __table_args__ = (db.UniqueConstraint('user_id', 'project_id', name='unique_user_project'),)
    
    def __repr__(self):
        return f'<ProjectAssignment {self.user.email} -> {self.project.name}>'


class AccessLog(db.Model):
    __tablename__ = 'access_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)  # login, logout, view_test, download_data, etc.
    resource = db.Column(db.String(200))  # test_id, experiment_id, etc.
    ip_address = db.Column(db.String(45))  # IPv4 or IPv6
    user_agent = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<AccessLog {self.user.email} {self.action} {self.timestamp}>'
    
    def to_dict(self):
        """Convert access log to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_email': self.user.email,
            'action': self.action,
            'resource': self.resource,
            'ip_address': self.ip_address,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }