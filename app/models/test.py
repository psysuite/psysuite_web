from datetime import datetime
from app import db
import json


class Test(db.Model):
    __tablename__ = 'tests'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    class_name = db.Column(db.String(20), nullable=False, unique=True, index=True)  # e.g., "TestBIS"
    description = db.Column(db.Text)
    status = db.Column(db.Enum('development', 'production', 'finalized', name='test_status'), 
                      default='development', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # JSON fields for flexible configuration
    _trial_columns = db.Column('trial_columns', db.JSON)       # Trial result column definitions
    
    @property
    def trial_columns(self):
        """Get trial columns as dict, handling both string and dict formats"""
        if self._trial_columns is None:
            return {}
        
        if isinstance(self._trial_columns, str):
            try:
                return json.loads(self._trial_columns)
            except (json.JSONDecodeError, TypeError):
                return {}
        
        return self._trial_columns if isinstance(self._trial_columns, dict) else {}
    
    @trial_columns.setter
    def trial_columns(self, value):
        """Set trial columns, ensuring it's stored properly"""
        if value is None:
            self._trial_columns = None
        elif isinstance(value, dict):
            self._trial_columns = value
        elif isinstance(value, str):
            try:
                self._trial_columns = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                self._trial_columns = {}
        else:
            self._trial_columns = {}
    
    # Relationships
    experiments = db.relationship('Experiment', backref='test', lazy='dynamic', cascade='all, delete-orphan')
    assignments = db.relationship('TestAssignment', backref='test', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Test {self.name}>'
    
    def get_trial_table_name(self):
        """Get the name of the dynamic trial table for this test"""
        # Convert test name to lowercase and replace spaces/special chars with underscores
        safe_name = ''.join(c if c.isalnum() else '_' for c in self.class_name.lower())
        return f"{safe_name}_trials"
    
    def get_trial_model_class_name(self):
        """Get the class name for the dynamic trial model"""
        # Convert test name to PascalCase
        words = ''.join(c if c.isalnum() else ' ' for c in self.name).split()
        return ''.join(word.capitalize() for word in words) + 'Trial'
    
    def can_accept_experiments(self):
        """Check if test can accept new experiments"""
        return self.status in ['development', 'production']
    
    def is_finalized(self):
        """Check if test is finalized (no more experiments accepted)"""
        return self.status == 'finalized'
    
    def get_experiment_count(self):
        """Get total number of experiments for this test"""
        return self.experiments.count()
    
    def get_recent_experiments(self, limit=10):
        """Get recent experiments for this test"""
        return self.experiments.order_by(db.desc('uploaded_at')).limit(limit).all()
    
    def validate_trial_columns(self):
        """Validate trial columns configuration"""
        if not self.trial_columns:
            return False, "Trial columns must be defined"
        
        if not isinstance(self.trial_columns, dict):
            return False, "Trial columns must be a dictionary"
        
        valid_types = ['integer', 'float', 'string', 'bigint', 'boolean', 'datetime']
        for column_name, column_type in self.trial_columns.items():
            if not isinstance(column_name, str) or not column_name.strip():
                return False, f"Invalid column name: {column_name}"
            
            if column_type not in valid_types:
                return False, f"Invalid column type '{column_type}' for column '{column_name}'. Valid types: {valid_types}"
        
        return True, "Valid"
    
    def to_dict(self, include_experiments=False):
        """Convert test to dictionary for JSON serialization"""
        result = {
            'id': self.id,
            'name': self.name,
            'class_name': self.class_name,
            'description': self.description,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,

            'trial_columns': self.trial_columns,
            'experiment_count': self.get_experiment_count()
        }
        
        if include_experiments:
            result['experiments'] = [exp.to_dict() for exp in self.experiments.all()]
        
        return result
    
    @staticmethod
    def get_by_class_name(class_name):
        """Get test by its class name"""
        return Test.query.filter_by(class_name=class_name).first()
    
    @staticmethod
    def get_production_tests():
        """Get all tests in production status"""
        return Test.query.filter_by(status='production').all()
    
    @staticmethod
    def search_tests(query):
        """Search tests by name or description"""
        return Test.query.filter(
            db.or_(
                Test.name.contains(query),
                Test.description.contains(query)
            )
        ).all()