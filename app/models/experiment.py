from datetime import datetime
from app import db


class Experiment(db.Model):
    __tablename__ = 'experiments'
    
    id = db.Column(db.Integer, primary_key=True)
    exp_uid = db.Column(db.String(100), unique=True, nullable=False, index=True)  # From Android app
    test_id = db.Column(db.Integer, db.ForeignKey('tests.id'), nullable=False)
    device_id = db.Column(db.String(50), index=True)
    
    # Project relationship
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True, index=True)
    project_name = db.Column(db.String(100), index=True)  # Denormalized for performance
    
    # Subject information (main display fields)
    label = db.Column(db.String(50))
    age = db.Column(db.Integer)
    gender = db.Column(db.Integer)  # 0=female, 1=male, 2=other
    population = db.Column(db.Integer)
    session = db.Column(db.Integer)
    type = db.Column(db.Integer)
    date = db.Column(db.String(50))  # Date as string from Android

    # Test configuration info (single_experiment page)
    device = db.Column(db.Text)  # Device info as JSON string
    vercode = db.Column(db.Integer)
    stimuli_delays = db.Column(db.Text)  # StimuliDelays as JSON string
    whitenoise = db.Column(db.Integer)
    trman_type = db.Column(db.Integer)
    show_result = db.Column(db.Integer)
    can_repeat = db.Column(db.Integer)
    do_training = db.Column(db.Integer)
    
    # Metadata
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    project = db.relationship('Project', backref='experiments', lazy=True)
    
    def __repr__(self):
        return f'<Experiment {self.exp_uid}>'
    
    def get_subject_display_name(self):
        """Get a display-friendly subject identifier"""
        if self.label:
            return f"{self.label} (Age: {self.age or 'N/A'})"
        return f"Subject {self.id}"
    
    def get_gender_display(self):
        """Get human-readable gender"""
        gender_map = {0: 'Male', 1: 'Female', 2: 'Other'}
        return gender_map.get(self.gender, 'Unknown')
    
    def get_device_display(self):
        """Get device information for display"""
        if not self.device:
            return 'Unknown Device'
        
        try:
            import json
            device_info = json.loads(self.device)
            manufacturer = device_info.get('manufacturer', '')
            model = device_info.get('model', '')
            os_version = device_info.get('os', '')
            
            parts = []
            if manufacturer:
                parts.append(manufacturer.title())
            if model:
                parts.append(model)
            if os_version:
                parts.append(f"Android {os_version}")
            
            return ' '.join(parts) if parts else 'Unknown Device'
        except:
            return 'Unknown Device'
    
    @property
    def subject_label(self):
        """Get subject label, handling None values"""
        return self.label if self.label is not None else 'N/A'
    
    @property
    def subject_age(self):
        """Get subject age, handling None values"""
        return self.age if self.age is not None else 'N/A'
    
    def get_population_display(self):
        """Get population information for display"""
        return self.population if self.population is not None else 'N/A'
    
    def get_session_display(self):
        """Get session information for display"""
        return self.session if self.session is not None else 'N/A'
    
    def get_experiment_date_display(self):
        """Get experiment date for display"""
        return self.date if self.date else 'N/A'
    
    def get_device_id_display(self):
        """Get device ID for display"""
        return self.device_id if self.device_id else 'Not registered'
    
    def get_project_display(self):
        """Get project name for display"""
        if self.project_name:
            return self.project_name
        elif self.project:
            return self.project.name
        else:
            return 'No Project'
    
    def get_project_name(self):
        """Get project name, handling None values"""
        return self.project_name if self.project_name else 'No Project'
    
    def get_trial_count(self):
        """Get number of trials for this experiment"""
        from app.models.dynamic_models import get_trial_model
        
        trial_model = get_trial_model(self.test.class_name)
        if trial_model:
            return trial_model.query.filter_by(experiment_id=self.id).count()
        return 0
    
    def get_trials(self):
        """Get all trials for this experiment"""
        from app.models.dynamic_models import get_trial_model
        
        trial_model = get_trial_model(self.test.class_name)
        if trial_model:
            return trial_model.query.filter_by(experiment_id=self.id).order_by('trid').all()
        return []
    
    def get_trial_data_as_dict(self):
        """Get trial data as list of dictionaries for export"""
        trials = self.get_trials()
        if not trials:
            return []
        
        # Get column names from the trial model
        trial_data = []
        for trial in trials:
            trial_dict = {}
            for column in trial.__table__.columns:
                if column.name not in ['id', 'experiment_id']:
                    value = getattr(trial, column.name)
                    trial_dict[column.name] = value
            trial_data.append(trial_dict)
        
        return trial_data
    
    def validate_configuration(self):
        """Validate experiment configuration data"""
        if not self.configuration:
            return False, "Configuration data is required"
        
        if not isinstance(self.configuration, dict):
            return False, "Configuration must be a dictionary"
        
        # Check for required fields
        required_fields = ['classes', 'label']
        for field in required_fields:
            if field not in self.configuration:
                return False, f"Required field '{field}' missing from configuration"
        
        return True, "Valid"
    
    def to_dict(self, include_trials=False):
        """Convert experiment to dictionary for JSON serialization"""
        result = {
            'id': self.id,
            'exp_uid': self.exp_uid,
            'test_id': self.test_id,
            'test_name': self.test.name if self.test else None,
            'label': self.label,
            'age': self.age,
            'subject_label': self.subject_label,
            'subject_age': self.subject_age,
            'gender': self.gender,
            'gender_display': self.get_gender_display(),
            'population': self.population,
            'population_display': self.get_population_display(),
            'session': self.session,
            'session_display': self.get_session_display(),
            'type': self.type,
            'date': self.date,
            'experiment_date_display': self.get_experiment_date_display(),
            'device': self.device,
            'device_display': self.get_device_display(),
            'device_id': self.device_id,
            'device_id_display': self.get_device_id_display(),
            'project_id': self.project_id,
            'project_name': self.project_name,
            'project_display': self.get_project_display(),
            'vercode': self.vercode,
            'stimuli_delays': self.stimuli_delays,
            'whitenoise': self.whitenoise,
            'trman_type': self.trman_type,
            'show_result': self.show_result,
            'can_repeat': self.can_repeat,
            'do_training': self.do_training,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'trial_count': self.get_trial_count()
        }
        
        if include_trials:
            result['trials'] = self.get_trial_data_as_dict()
        
        return result
    
    @staticmethod
    def get_by_exp_uid(exp_uid):
        """Get experiment by unique ID"""
        return Experiment.query.filter_by(exp_uid=exp_uid).first()
    
    @staticmethod
    def get_experiments_for_test(test_id, limit=None):
        """Get experiments for a specific test"""
        query = Experiment.query.filter_by(test_id=test_id).order_by(db.desc(Experiment.uploaded_at))
        if limit:
            query = query.limit(limit)
        return query.all()
    
    @staticmethod
    def get_recent_experiments(limit=50):
        """Get recent experiments across all tests"""
        return Experiment.query.order_by(db.desc(Experiment.uploaded_at)).limit(limit).all()
    
    @staticmethod
    def search_experiments(test_id=None, subject_label=None, project_id=None, completion_status=None, date_from=None, date_to=None):
        """Search experiments with various filters"""
        query = Experiment.query
        
        if test_id:
            query = query.filter_by(test_id=test_id)
        
        if subject_label:
            query = query.filter(Experiment.label.contains(subject_label))
        
        if project_id:
            query = query.filter_by(project_id=project_id)
        
        if date_from:
            query = query.filter(Experiment.uploaded_at >= date_from)
        
        if date_to:
            query = query.filter(Experiment.uploaded_at <= date_to)
        
        return query.order_by(db.desc(Experiment.uploaded_at)).all()
    
    def get_completion_status_display(self):
        """Get completion status display for templates"""
        trial_count = self.get_trial_count()
        if trial_count == 0:
            return "No trials"
        else:
            return f"{trial_count} trials"
    
    def set_project(self, project):
        """Set project for this experiment"""
        if project:
            self.project_id = project.id
            self.project_name = project.name
        else:
            self.project_id = None
            self.project_name = None
    
    def set_project_by_name(self, project_name):
        """Set project by name, creating project reference if it exists"""
        from app.models.project import Project
        
        if not project_name or project_name.lower() in ['no project', 'n.a.', '']:
            self.project_id = None
            self.project_name = 'No Project'
            return
        
        # Try to find existing project
        project = Project.get_project_by_name(project_name)
        if project:
            self.project_id = project.id
            self.project_name = project.name
        else:
            # Store the name even if project doesn't exist in database
            self.project_id = None
            self.project_name = project_name
    
    @staticmethod
    def get_experiments_by_project(project_id, limit=None):
        """Get experiments for a specific project"""
        query = Experiment.query.filter_by(project_id=project_id).order_by(db.desc(Experiment.uploaded_at))
        if limit:
            query = query.limit(limit)
        return query.all()
    
    @staticmethod
    def get_project_statistics():
        """Get statistics about experiments by project"""
        from sqlalchemy import func
        from app.models.project import Project
        
        # Get counts by project_name (including those without project_id)
        stats = db.session.query(
            Experiment.project_name,
            func.count(Experiment.id).label('count')
        ).group_by(Experiment.project_name).order_by(
            func.count(Experiment.id).desc()
        ).all()
        
        return [(name or 'No Project', count) for name, count in stats]