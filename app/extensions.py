"""Shared Flask extension instances.

Extensions are initialised in the application factory (``app.create_app``)
so that importing this module never creates a circular import.
"""

from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()

login_manager.login_view = "auth.login"
login_manager.login_message = "Please sign in to continue."
login_manager.login_message_category = "warning"
