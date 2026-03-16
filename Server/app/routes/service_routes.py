from flask import render_template, request, redirect, url_for, flash, Blueprint
from app import db
from app.models.service import Service

services_bp = Blueprint('services', __name__)

@services_bp.route('/services')
def index():
    services = Service.query.all()
    return render_template('services/index.html', services=services)

@services_bp.route('/services/new', methods = ['GET', 'POST'])
def create():
    if request.method == 'POST':
        service = Service(
            name = request.form.get('name'),
            price = float(request.form.get('price')),
            duration_minutes = int(request.form.get('duration_minutes'))
        )
        db.session.add(service)
        db.session.commit()
        flash('Услуга добавлена', 'success')
        return redirect(url_for('services.index'))
    
    return render_template('services/form.html')

@services_bp.route('/services/<int:id>/edit', methods = ['GET','POST'])
def edit(id):
    service = Service.query.get_or_404(id)
    
    if request.method == 'POST':
        service.name = request.form.get('name')
        service.price = float(request.form.get('price'))
        service.duration_minutes = int(request.form.get('duration_minutes'))
        
        db.session.commit()
        flash('Услуга обновлена', 'success')
        return redirect(url_for('services.index'))
    
    return render_template('services/form.html', service=service)

@services_bp.route('/services/<int:id>/delete', methods=['POST'])
def delete(id):
    service = Service.query.get_or_404(id)
    db.session.delete(service)
    db.session.commit()
    flash('Услуга удалена', 'success')
    return redirect(url_for('services.index'))