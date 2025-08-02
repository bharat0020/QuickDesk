import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Initialize extensions
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///quickdesk.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# File upload configuration
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size

# Mail configuration (mocked for MVP)
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME", "")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD", "")
app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MAIL_DEFAULT_SENDER", "noreply@quickdesk.com")

# Initialize extensions with app
db.init_app(app)
login_manager.init_app(app)
mail.init_app(app)
csrf.init_app(app)

# Login manager configuration
login_manager.login_view = "login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Create upload directory
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

with app.app_context():
    # Import models to create tables
    import models  # noqa: F401
    db.create_all()
    
    # Create default admin user and categories
    from models import User, Category
    from werkzeug.security import generate_password_hash
    
    # Create default admin if not exists
    admin_user = User.query.filter_by(email="admin@quickdesk.com").first()
    if not admin_user:
        admin_user = User(
            username="admin",
            email="admin@quickdesk.com",
            password_hash=generate_password_hash("admin123"),
            role="admin",
            first_name="System",
            last_name="Administrator"
        )
        db.session.add(admin_user)
    
    # Create default categories if not exists
    default_categories = [
        {"name": "Technical Support", "description": "Technical issues and troubleshooting"},
        {"name": "Account Issues", "description": "Login, password, and account related problems"},
        {"name": "Feature Request", "description": "Suggestions for new features"},
        {"name": "Bug Report", "description": "Report software bugs and issues"},
        {"name": "General Inquiry", "description": "General questions and information"}
    ]
    
    for cat_data in default_categories:
        if not Category.query.filter_by(name=cat_data["name"]).first():
            category = Category(name=cat_data["name"], description=cat_data["description"])
            db.session.add(category)
    
    db.session.commit()
    logging.info("Database initialized with default data")
