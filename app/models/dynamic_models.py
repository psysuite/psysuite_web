from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime, ForeignKey, Text
from app import db
from app.models.test import Test
import json

# Registry to store dynamically created models
_trial_models = {}


def create_trial_model(test_classname, trial_columns):
    """
    Dynamically create a model for test-specific trial data
    
    Args:
        test_name (str): class_name of the test
        trial_columns (dict): Dictionary of column_name: column_type pairs
    
    Returns:
        SQLAlchemy model class for the trial data
    """

    # Generate safe class and table names
    safe_name = ''.join(c if c.isalnum() else '_' for c in test_classname.lower())
    class_name = ''.join(word.capitalize() for word in safe_name.split('_')) + 'Trial'
    table_name = f"{safe_name}_trials"
    
    # Check if model already exists
    if class_name in _trial_models:
        return _trial_models[class_name]
    
    # Base attributes for the model
    attrs = {
        '__tablename__': table_name,
        '__table_args__': {'extend_existing': True},
        'id': Column(Integer, primary_key=True),
        'experiment_id': Column(Integer, ForeignKey('experiments.id'), nullable=False),
        'trid': Column(Integer, nullable=False),
        'created_at': Column(DateTime, default=datetime.utcnow),
    }
    
    # Add dynamic columns based on test configuration
    for col_name, col_type in trial_columns.items():
        # Sanitize column name
        safe_col_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in col_name.lower())
        
        # Skip reserved column names
        if safe_col_name in ['id', 'experiment_id', 'trid', 'created_at']:
            continue
        
        if col_type == 'integer':
            attrs[safe_col_name] = Column(Integer)
        elif col_type == 'float':
            attrs[safe_col_name] = Column(Float)
        elif col_type == 'string':
            attrs[safe_col_name] = Column(String(255))
        elif col_type == 'boolean':
            attrs[safe_col_name] = Column(Boolean)
        elif col_type == 'datetime':
            attrs[safe_col_name] = Column(DateTime)
        elif col_type == 'text':
            attrs[safe_col_name] = Column(Text)
        elif col_type == 'bigint':
            attrs[safe_col_name] = Column(db.BigInteger)
        else:
            # Default to string for unknown types
            attrs[safe_col_name] = Column(String(255))
    
    # Add methods to the model
    def __repr__(self):
        return f'<{class_name} experiment_id={self.experiment_id} trid={self.trid}>'
    
    def to_dict(self):
        """Convert trial to dictionary for JSON serialization"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result
    
    attrs['__repr__'] = __repr__
    attrs['to_dict'] = to_dict
    
    # Create the model class
    model_class = type(class_name, (db.Model,), attrs)
    
    # Store in registry
    _trial_models[class_name] = model_class
    _trial_models[table_name] = model_class  # Also store by table name for lookup
    
    return model_class


def get_trial_model(test_classname):
    """
    Get the trial model for a specific test
    
    Args:
        test_name (str): Name of the test
    
    Returns:
        SQLAlchemy model class or None if not found
    """
    safe_name = ''.join(c if c.isalnum() else '_' for c in test_classname.lower())
    class_name = ''.join(word.capitalize() for word in safe_name.split('_')) + 'Trial'
    
    return _trial_models.get(class_name)


def get_trial_model_by_table_name(table_name):
    """
    Get the trial model by table name
    
    Args:
        table_name (str): Name of the table
    
    Returns:
        SQLAlchemy model class or None if not found
    """
    return _trial_models.get(table_name)


def create_trial_table(test_classname, trial_columns):
    """
    Create the database table for trial data
    
    Args:
        test_classname (str): class_name of the test
        trial_columns (dict): Dictionary of column_name: column_type pairs
    
    Returns:
        bool: True if table was created successfully
    """
    try:
        model_class = create_trial_model(test_classname, trial_columns)
        
        # Create the table in the database
        model_class.__table__.create(db.engine, checkfirst=True)
        
        return True
    except Exception as e:
        print(f"Error creating trial table for {test_classname}: {e}")
        return False


def drop_trial_table(test_name):
    """
    Drop the database table for trial data
    Args:
        test_name (str): Name of the test
    Returns:
        bool: True if table was dropped successfully
    """
    try:
        model_class = get_trial_model(test_name)
        if model_class:
            # Drop the table from the database
            model_class.__table__.drop(db.engine, checkfirst=True)
            
            # Remove from registry
            safe_name = ''.join(c if c.isalnum() else '_' for c in test_name.lower())
            class_name = ''.join(word.capitalize() for word in safe_name.split('_')) + 'Trial'
            table_name = f"{safe_name}_trials"
            
            _trial_models.pop(class_name, None)
            _trial_models.pop(table_name, None)
        
        return True
    except Exception as e:
        print(f"Error dropping trial table for {test_name}: {e}")
        return False


def update_trial_table(test_name, old_columns, new_columns):
    """
    Update the trial table structure when test configuration changes
    Args:
        test_name (str): Name of the test
        old_columns (dict): Previous column configuration
        new_columns (dict): New column configuration
    Returns:
        bool: True if table was updated successfully
    """
    try:
        # For simplicity, we'll recreate the table
        # In production, you might want to use ALTER TABLE statements
        
        # Get existing data
        model_class = get_trial_model(test_name)
        existing_data = []
        
        if model_class:
            existing_data = model_class.query.all()
            existing_data = [trial.to_dict() for trial in existing_data]
        
        # Drop old table
        drop_trial_table(test_name)
        
        # Create new table
        create_trial_table(test_name, new_columns)
        
        # Restore data (only columns that still exist)
        if existing_data:
            new_model_class = get_trial_model(test_name)
            new_column_names = [col.name for col in new_model_class.__table__.columns]
            
            for trial_data in existing_data:
                # Filter data to only include columns that exist in new schema
                filtered_data = {k: v for k, v in trial_data.items() if k in new_column_names}
                
                new_trial = new_model_class(**filtered_data)
                db.session.add(new_trial)
            
            db.session.commit()
        
        return True
    except Exception as e:
        print(f"Error updating trial table for {test_name}: {e}")
        db.session.rollback()
        return False


def initialize_existing_tests():
    """
    Initialize trial models for existing tests in the database
    This should be called when the application starts
    """
    try:
        tests = Test.query.all()
        initialized_count = 0
        
        for test in tests:
            if test.trial_columns:
                try:
                    # Handle both dict and string formats
                    if isinstance(test.trial_columns, str):
                        trial_columns = json.loads(test.trial_columns)
                    else:
                        trial_columns = test.trial_columns
                    
                    if isinstance(trial_columns, dict):
                        create_trial_table(test.class_name, trial_columns)
                        initialized_count += 1
                    else:
                        print(f"Error creating trial table for {test.class_name}: trial_columns is not a dict")
                except Exception as e:
                    print(f"Error creating trial table for {test.class_name}: {e}")
        
        print(f"Initialized {initialized_count} trial models")
    except Exception as e:
        print(f"Error initializing existing tests: {e}")


def get_all_trial_models():
    """
    Get all registered trial models
    
    Returns:
        dict: Dictionary of model_name: model_class pairs
    """
    return _trial_models.copy()


def clear_trial_models():
    """
    Clear all registered trial models (useful for testing)
    """
    global _trial_models
    _trial_models = {}