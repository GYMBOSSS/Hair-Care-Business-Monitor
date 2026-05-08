from app import db
from datetime import datetime

class Client(db.Model):
    __tablename__ = 'clients'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), unique=False, nullable=False)
    comment = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    appointments = db.relationship('Appointment', backref='client', lazy=True)
    
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=False)
    
    __table_args___ = (
        db.UniqueConstraint('phone', 'business_id', name = 'unique_phone_per_business')
    )
    
    def __repr__(self):
        return f'<Client> {self.name}'
    