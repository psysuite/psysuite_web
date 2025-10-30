from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import config

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()


def create_app(config_name='default', skip_db_init=False):
    app = Flask(__name__)
    
    # Handle both config name strings and direct config dictionaries
    if isinstance(config_name, dict):
        # Direct config dictionary (for testing)
        app.config.update(config_name)
    else:
        # Config name string
        app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
    # Initialize mail
    from app.utils.email import init_mail
    init_mail(app)
    
    # Configure login manager
    login_manager.login_view = 'web.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Register blueprints
    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    from app.web import bp as web_bp
    app.register_blueprint(web_bp)
    
    from app.web.project_routes import project_bp
    app.register_blueprint(project_bp)
    
    # Initialize database and create default admin user (unless skipped)
    if not skip_db_init:
        with app.app_context():
            from app.models.user import User
            from app.models.test import Test
            from app.models.experiment import Experiment
            from app.models.project import Project
            from app.models.dynamic_models import initialize_existing_tests
            
            # Skip automatic table creation and admin user creation
            # These will be handled by init_db.py script
            pass
            
            # Initialize existing trial models (with error handling for fresh databases)
            try:
                initialize_existing_tests()
            except Exception as e:
                # This is expected on fresh databases where tables don't exist yet
                print(f"Note: Could not initialize existing tests (expected on fresh database): {e}")
                pass
    
    return app


@login_manager.user_loader
def load_user(user_id):
    from app.models.user import User
    return User.query.get(int(user_id))