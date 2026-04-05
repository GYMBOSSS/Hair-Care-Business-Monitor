from flask import render_template, Blueprint
from flask_login import login_required, current_user
from app import db
from app.models.client import Client
from app.models.service import Service
from app.models.appointment import Appointment
from app.models.user import User
from datetime import datetime, timedelta
from sqlalchemy import func
import requests

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def index():
    # Проверка наличия бизнеса
    if not current_user.business_id:
        if current_user.role == 'owner':
            return render_template('dashboard/no_business_owner.html')
        else:
            return render_template('dashboard/no_business_employee.html')
    
    # Разделяем по ролям
    if current_user.role == 'owner':
        return owner_dashboard()
    else:
        return employee_dashboard()


def owner_dashboard():
    business_id = current_user.business_id
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    
    # Выручка сегодня
    revenue_today = db.session.query(func.sum(Service.price)).join(
        Appointment, Appointment.service_id == Service.id
    ).filter(
        Appointment.business_id == business_id,
        Appointment.status == 'completed',
        func.date(Appointment.appointment_time) == today
    ).scalar() or 0
    
    # Выручка за неделю
    revenue_week = db.session.query(func.sum(Service.price)).join(
        Appointment, Appointment.service_id == Service.id
    ).filter(
        Appointment.business_id == business_id,
        Appointment.status == 'completed',
        Appointment.appointment_time >= week_ago
    ).scalar() or 0
    
    # Количество клиентов
    total_clients = Client.query.filter_by(business_id=business_id).count()
    new_clients_week = Client.query.filter(
        Client.business_id == business_id,
        Client.created_at >= week_ago
    ).count()
    
    # Средний чек
    avg_check = db.session.query(func.avg(Service.price)).join(
        Appointment, Appointment.service_id == Service.id
    ).filter(
        Appointment.business_id == business_id,
        Appointment.status == 'completed'
    ).scalar() or 0
    
    # Топ услуг
    top_services = db.session.query(
        Service.name,
        func.count(Appointment.id).label('total')
    ).join(Appointment).filter(
        Appointment.business_id == business_id
    ).group_by(Service.id).order_by(
        func.count(Appointment.id).desc()
    ).limit(5).all()
    
    # Динамика выручки по дням
    revenue_by_day = []
    for i in range(7):
        day = today - timedelta(days=i)
        revenue = db.session.query(func.sum(Service.price)).join(
            Appointment, Appointment.service_id == Service.id
        ).filter(
            Appointment.business_id == business_id,
            Appointment.status == 'completed',
            func.date(Appointment.appointment_time) == day
        ).scalar() or 0
        revenue_by_day.append({
            'date': day.strftime('%d.%m'),
            'revenue': revenue
        })
    revenue_by_day.reverse()  # чтобы шли по порядку
    
    # Курс доллара
    try:
        usd_rate = requests.get('https://api.exchangerate-api.com/v4/latest/USD').json()['rates']['RUB']
    except:
        usd_rate = 'N/A'
    
    # Последние записи
    recent_appointments = Appointment.query.filter_by(
        business_id=business_id
    ).order_by(
        Appointment.appointment_time.desc()
    ).limit(5).all()
    
    return render_template('dashboard/owner.html',
        revenue_today=revenue_today,
        revenue_week=revenue_week,
        total_clients=total_clients,
        new_clients_week=new_clients_week,
        avg_check=avg_check,
        top_services=top_services,
        revenue_by_day=revenue_by_day,
        usd_rate=usd_rate,
        recent_appointments=recent_appointments
    )


def employee_dashboard():
    business_id = current_user.business_id
    today = datetime.now().date()
    
    # Моя выручка сегодня
    my_revenue_today = db.session.query(func.sum(Service.price)).join(
        Appointment, Appointment.service_id == Service.id
    ).filter(
        Appointment.business_id == business_id,
        Appointment.employee_id == current_user.id,
        Appointment.status == 'completed',
        func.date(Appointment.appointment_time) == today
    ).scalar() or 0
    
    # Мои выполненные услуги сегодня
    my_completed_today = Appointment.query.filter_by(
        business_id=business_id,
        employee_id=current_user.id,
        status='completed'
    ).filter(
        func.date(Appointment.appointment_time) == today
    ).count()
    
    # Активные записи на сегодня (мои)
    my_today_appointments = Appointment.query.filter_by(
        business_id=business_id,
        employee_id=current_user.id,
        status='scheduled'
    ).filter(
        func.date(Appointment.appointment_time) == today
    ).all()
    
    # Записи без сотрудника (можно взять в работу)
    available_appointments = Appointment.query.filter_by(
        business_id=business_id,
        employee_id=None,
        status='scheduled'
    ).filter(
        Appointment.appointment_time >= today
    ).order_by(Appointment.appointment_time).limit(10).all()
    
    # Мои будущие записи
    my_upcoming = Appointment.query.filter_by(
        business_id=business_id,
        employee_id=current_user.id,
        status='scheduled'
    ).filter(
        Appointment.appointment_time > today
    ).order_by(Appointment.appointment_time).limit(10).all()
    
    return render_template('dashboard/employee.html',
        my_revenue_today=my_revenue_today,
        my_completed_today=my_completed_today,
        my_today_appointments=my_today_appointments,
        available_appointments=available_appointments,
        my_upcoming=my_upcoming
    )