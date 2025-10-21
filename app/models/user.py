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
    test_assignments = db.relationship('TestAssignment', backref='user', lazy='dynamic', cascade='all, delete-orphan')
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
    
    def get_assigned_tests(self):
        """Get list of tests assigned to this user"""
        if self.is_admin():
            from app.models.test import Test
            return Test.query.all()
        else:
            return [assignment.test for assignment in self.test_assignments if assignment.test.status == 'production']
    
    def has_test_access(self, test_id):
        """Check if user has access to specific test"""
        if self.is_admin():
            return True
        
        return self.test_assignments.filter_by(test_id=test_id).first() is not None
    
    def to_dict(self):
        """Convert user to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }


class TestAssignment(db.Model):
    __tablename__ = 'test_assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    test_id = db.Column(db.Integer, db.ForeignKey('tests.id'), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint to prevent duplicate assignments
    __table_args__ = (db.UniqueConstraint('user_id', 'test_id', name='unique_user_test'),)
    
    def __repr__(self):
        return f'<TestAssignment user_id={self.user_id} test_id={self.test_id}>'


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