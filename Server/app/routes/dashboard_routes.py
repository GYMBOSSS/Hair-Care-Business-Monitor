from flask import render_template, Blueprint
from app import db
from app.models.client import Client
from app.models.service import Service
from app.models.appointment import Appointment
from datetime import datetime, timedelta
from sqlalchemy import func

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
def index():
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    total_clients = Client.query.count()
    total_services = Service.query.count()
    
    today_appointments = Appointment.query.filter(
        func.date(Appointment.appointment_time) == today
    ).count()
    
    completed_today = Appointment.query.filter(
        Appointment.status == 'completed',
        func.date(Appointment.appointment_time) == today
    ).count()
    
    revenue_today = db.session.query(func.sum(Service.price)).join(
        Appointment, Appointment.service_id == Service.id
    ).filter(
        Appointment.status == 'completed',
        func.date(Appointment.appointment_time) == today
    ).scalar() or 0
    
    revenue_week = db.session.query(func.sum(Service.price)).join(
        Appointment, Appointment.service_id == Service.id
    ).filter(
        Appointment.status == 'completed',
        Appointment.appointment_time >= week_ago
    ).scalar() or 0
    
    top_services = db.session.query(
        Service.name,
        func.count(Appointment.id).label('total')
    ).join(Appointment).group_by(Service.id).order_by(
        func.count(Appointment.id).desc()
    ).limit(5).all()
    
    recent_appointments = Appointment.query.order_by(
        Appointment.appointment_time.desc()
    ).limit(5).all()
    
    return render_template(
        'dashboard/index.html',
        total_clients=total_clients,
        total_services=total_services,
        today_appointments=today_appointments,
        completed_today=completed_today,
        revenue_today=revenue_today,
        revenue_week=revenue_week,
        top_services=top_services,
        recent_appointments=recent_appointments
    )