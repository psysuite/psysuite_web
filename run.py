import os
from app import create_app, db
from app.models.user import User
from app.models.test import Test
from app.models.experiment import Experiment
from app.models.project import Project

app = create_app(os.getenv('FLASK_CONFIG') or 'default')


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Test': Test, 'Experiment': Experiment, 'Project': Project}


if __name__ == '__main__':
    # Get configuration from environment
    config_name = os.getenv('FLASK_CONFIG', 'default')
    debug_mode = config_name == 'development'
    
    # Disable reloader when debugging to allow PyCharm breakpoints
    app.run(debug=debug_mode, host='0.0.0.0', port=5000, use_reloader=False)