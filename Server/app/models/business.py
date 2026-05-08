from app import db
from datetime import datetime

class Business(db.Model):
    __tablename__ = 'businesses'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    users = db.relationship('User', backref='business', lazy=True)
    clients = db.relationship('Client', backref='business', lazy=True)
    services = db.relationship('Service', backref='business', lazy=True)
    appointments = db.relationship('Appointment', backref='business', lazy=True)
    
    bot_token = db.Column(db.String(200), unique = True, nullable = True)
    
    def __repr__(self):
        return f'<Buisness {self.name}>'