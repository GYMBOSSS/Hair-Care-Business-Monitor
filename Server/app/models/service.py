from app import db

class Service(db.Model):
    __tablename__ = 'services'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    
    appointments = db.relationship('Appointment', backref='service', lazy=True)
    
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=False)
    
    def __repr__(self):
        return f'<Service {self.name}>'