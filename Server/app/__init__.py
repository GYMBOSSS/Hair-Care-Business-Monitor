from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    
    app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    print("Database URI:", app.config['SQLALCHEMY_DATABASE_URI'])
    
    db.init_app(app)
    migrate.init_app(app,db)
    
    from app.models import client, service, appointment
    
    from app.routes import client_routes
    app.register_blueprint(client_routes.clients_bp)
    
    from app.routes import service_routes
    app.register_blueprint(service_routes.services_bp)
    
    from app.routes import appointment_routes
    app.register_blueprint(appointment_routes.appointments_bp)
    
    from app.routes import dashboard_routes
    app.register_blueprint(dashboard_routes.dashboard_bp)
    
    return app