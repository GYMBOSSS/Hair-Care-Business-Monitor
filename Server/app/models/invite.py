from app import db
from datetime import datetime

class Invite(db.Model):
    __tablename__ = 'invites'
    
    id = db.Column(db.Integer, primary_key=True)
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    responded_at = db.Column(db.DateTime, nullable=True)
    
    # Связи
    business = db.relationship('Business', backref='invites')
    
    def __repr__(self):
        return f'<Invite {self.user_id} -> {self.business_id}>'