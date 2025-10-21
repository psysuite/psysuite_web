from datetime import datetime
from app import db


class Experiment(db.Model):
    __tablename__ = 'experiments'
    
    id = db.Column(db.Integer, primary_key=True)
    unique_id = db.Column(db.String(100), unique=True, nullable=False, index=True)  # From Android app
    test_id = db.Column(db.Integer, db.ForeignKey('tests.id'), nullable=False)
    device_id = db.Column(db.String(50), index=True)
    
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
    
    def __repr__(self):
        return f'<Experiment {self.unique_id}>'
    
    def get_subject_display_name(self):
        """Get a display-friendly subject identifier"""
        if self.label:
            return f"{self.label} (Age: {self.age or 'N/A'})"
        return f"Subject {self.id}"
    
    def get_gender_display(self):
        """Get human-readable gender"""
        gender_map = {0: 'Female', 1: 'Male', 2: 'Other'}
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
            return trial_model.query.filter_by(experiment_id=self.id).order_by('trial_number').all()
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
            'unique_id': self.unique_id,
            'test_id': self.test_id,
            'test_name': self.test.name if self.test else None,
            'label': self.label,
            'age': self.age,
            'gender': self.gender,
            'gender_display': self.get_gender_display(),
            'population': self.population,
            'session': self.session,
            'type': self.type,
            'date': self.date,
            'device': self.device,
            'device_display': self.get_device_display(),
            'device_id': self.device_id,
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
    def get_by_unique_id(unique_id):
        """Get experiment by unique ID"""
        return Experiment.query.filter_by(unique_id=unique_id).first()
    
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
    def search_experiments(test_id=None, subject_label=None, completion_status=None, date_from=None, date_to=None):
        """Search experiments with various filters"""
        query = Experiment.query
        
        if test_id:
            query = query.filter_by(test_id=test_id)
        
        if subject_label:
            query = query.filter(Experiment.label.contains(subject_label))
        

        
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