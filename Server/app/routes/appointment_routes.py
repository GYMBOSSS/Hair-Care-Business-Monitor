from flask import render_template, request, redirect, url_for, flash, Blueprint
from app import db
from app.models.client import Client
from app.models.service import Service
from app.models.appointment import Appointment
from datetime import datetime

appointments_bp = Blueprint('appointments', __name__)

@appointments_bp.route('/appointments')
def index():
    appointments = Appointment.query.order_by(Appointment.appointment_time.desc()).all()
    return render_template('appointments/index.html', appointments=appointments)

@appointments_bp.route('/appointments/new', methods = ['GET', 'POST'])
def create():
    if request.method == 'POST':
        client_id = request.form.get('client_id')
        service_id = request.form.get('service_id')
        appointment_time_str = request.form.get('appointment_time')
        notes = request.form.get('notes')
        
        appointment_time = datetime.fromisoformat(appointment_time_str)
        
        appointment = Appointment(
            client_id = client_id,
            service_id = service_id,
            appointment_time = appointment_time,
            notes = notes,
            status = 'scheduled'
        )
        
        db.session.add(appointment)
        db.session.commit()
        
        flash('Запись создана', 'success')
        return redirect(url_for('appointments.index'))
    
    clients = Client.query.all()
    services = Service.query.all()
    
    return render_template('appointments/form.html',
                           clients = clients,
                           services = services)

@appointments_bp.route('/appointment/<int:id>/edit', methods = ['GET', 'POST'])
def edit(id):
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
def delete(id):
    appointment = Appointment.query.get_or_404(id)
    db.session.delete(appointment)
    db.session.commit()
    flash('Запись удалена', 'success')
    return redirect(url_for('appointments.index'))

@appointments_bp.route('/appointments/<int:id>/complete', methods=['POST'])
def complete(id):
    """Отметить запись как выполненную"""
    appointment = Appointment.query.get_or_404(id)
    appointment.status = 'completed'
    db.session.commit()
    flash('Запись отмечена как выполненная', 'success')
    return redirect(url_for('appointments.index'))