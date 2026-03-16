from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    print("Database URI:", app.config['SQLALCHEMY_DATABASE_URI'])
    
    db.init_app(app)
    migrate.init_app(app,db)
    
    login_manager.init_app(app)
    login_manager.login = 'auth.login'
    login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице'
    
    from app.models import client, service, appointment, business, user, invite
    
    from app.routes import client_routes
    app.register_blueprint(client_routes.clients_bp)
    
    from app.routes import service_routes
    app.register_blueprint(service_routes.services_bp)
    
    from app.routes import appointment_routes
    app.register_blueprint(appointment_routes.appointments_bp)
    
    from app.routes import dashboard_routes
    app.register_blueprint(dashboard_routes.dashboard_bp)
    
    from app.routes import auth_routes
    app.register_blueprint(auth_routes.auth_bp)
    
    return app

@login_manager.user_loader
def load_user(user_id):
    from app.models.user import User
    return User.query.get(int(user_id))