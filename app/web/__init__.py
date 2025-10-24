from flask import Blueprint

bp = Blueprint('web', __name__)

from app.web import auth, main, admin
from app.web.project_routes import project_bp