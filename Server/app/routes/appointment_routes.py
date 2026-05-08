from flask import render_template, request, redirect, url_for, flash, Blueprint, make_response
from flask_login import login_required, current_user
from app import db
from app.models.client import Client
from app.models.service import Service
from app.models.appointment import Appointment
from datetime import datetime

appointments_bp = Blueprint('appointments', __name__)

@appointments_bp.route('/appointments/export')
@login_required
def export():
    if not current_user.business_id:
        flash('Сначала привяжитесь к бизнесу', 'warning')
        return redirect(url_for('dashboard.index'))
    
    appointments = Appointment.query.filter_by(
        business_id=current_user.business_id
    ).order_by(Appointment.appointment_time.desc()).all()
    
    import io
    import csv
    
    si = io.StringIO()
    writer = csv.writer(si, delimiter=';')
    
    # Заголовки
    writer.writerow(['ID', 'Клиент', 'Услуга', 'Дата и время', 'Статус', 'Примечания'])
    
    # Данные
    for app in appointments:
        writer.writerow([
            app.id,
            app.client.name,
            app.service.name,
            app.appointment_time.strftime('%d.%m.%Y %H:%M'),
            app.status,
            app.notes or ''
        ])
    
    response = make_response(si.getvalue().encode('utf-8-sig'))
    response.headers['Content-Disposition'] = 'attachment; filename=appointments.csv'
    response.headers['Content-type'] = 'text/csv; charset=utf-8'
    
    return response

@appointments_bp.route('/appointments')
@login_required
def index():
    if not current_user.business_id:
        flash('Сначала привяжитесь к бизнесу', 'warning')
        return redirect(url_for('dashboard.index'))
    
    appointments = Appointment.query.filter_by(
        business_id=current_user.business_id
    ).order_by(Appointment.appointment_time.desc()).all()
    
    return render_template('appointments/index.html', appointments=appointments)

@appointments_bp.route('/appointments/new', methods=['GET', 'POST'])
@login_required
def create():
    if not current_user.business_id:
        flash('Сначала привяжитесь к бизнесу', 'warning')
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        # ... создание записи (тут business_id уже добавляется)
        pass
    
    # ✅ Фильтруем клиентов и услуги по бизнесу
    clients = Client.query.filter_by(business_id=current_user.business_id).all()
    services = Service.query.filter_by(business_id=current_user.business_id).all()
    
    return render_template('appointments/form.html',
                           clients=clients,
                           services=services)

@appointments_bp.route('/appointment/<int:id>/edit', methods = ['GET', 'POST'])
@login_required
def edit(id):
    if not current_user.business_id:
        flash('Сначала привяжитесь к бизнесу', 'warning')
        return redirect(url_for('dashboard.index'))
    appointment = Appointment.query.get_or_404(id)
    
    if request.method == 'POST':
        appointment.client_id = request.form.get('client_id')
        appointment.service_id = request.form.get('service_id')
        appointment.appointment_time = datetime.fromisoformat(request.form.get('appointment_time'))
        appointment.notes = request.form.get('notes')
        appointment.status = request.form.get('status')
        
        db.session.commit()
        flash('Запись обновлена', 'success')
        return redirect(url_for('appointments.index'))
    
    clients = Client.query.all()
    services = Service.query.all()
    return render_template('/appointments/form.html',
                           appointment = appointment,
                           clients = clients,
                           services = services)

@appointments_bp.route('/appointments/<int:id>/delete', methods = ['POST'])
@login_required
def delete(id):
    if not current_user.business_id:
        flash('Сначала привяжитесь к бизнесу', 'warning')
        return redirect(url_for('dashboard.index'))
    
    appointments = Appointment.query.filter_by(
        business_id=current_user.business_id
    ).order_by(Appointment.appointment_time.desc()).all()
    
    db.session.delete(appointments)
    db.session.commit()
    flash('Запись удалена', 'success')
    return redirect(url_for('appointments.index'))

@appointments_bp.route('/appointments/<int:id>/complete', methods=['POST'])
@login_required
def complete(id):
    if not current_user.business_id:
        flash('Сначала привяжитесь к бизнесу', 'warning')
        return redirect(url_for('dashboard.index'))
    
    appointment = Appointment.query.get_or_404(id)
    appointment.status = 'completed'
    db.session.commit()
    flash('Запись отмечена как выполненная', 'success')
    return redirect(url_for('appointments.index'))

@appointments_bp.route('/appointments/<int:id>/assign', methods=['POST'])
@login_required
def assign(id):
    if not current_user.business_id:
        flash('Сначала привяжитесь к бизнесу', 'warning')
        return redirect(url_for('dashboard.index'))
    
    appointment = Appointment.query.filter_by(
        id=id,
        business_id=current_user.business_id
    ).first_or_404()
    
    appointment.employee_id = current_user.id
    db.session.commit()
    
    flash('Запись взята в работу', 'success')
    return redirect(url_for('dashboard.index'))