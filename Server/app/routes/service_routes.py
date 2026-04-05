from flask import render_template, request, redirect, url_for, flash, Blueprint, make_response
from flask_login import login_required, current_user
from app import db
from app.models.service import Service
import csv

services_bp = Blueprint('services', __name__)

@services_bp.route('/services/export')
@login_required
def export():
    if not current_user.business_id:
        flash('Сначала привяжитесь к бизнесу', 'warning')
        return redirect(url_for('dashboard.index'))
    
    services = Service.query.filter_by(business_id=current_user.business_id).all()
    
    output = []
    output.append(['ID', 'Название', 'Цена', 'Длительность (мин)'])
    
    for service in services:
        output.append([
            service.id,
            service.name,
            service.price,
            service.duration_minutes
        ])
    
    import io
    import csv
    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerows(output)
    
    response = make_response(si.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=services.csv'
    response.headers['Content-type'] = 'text/csv; charset=utf-8'
    
    return response

@services_bp.route('/services')
@login_required
def index():
    if not current_user.business_id:
        flash('Сначала привяжитесь к бизнесу', 'warning')
        return redirect(url_for('dashboard.index'))
    
    services = Service.query.filter_by(business_id=current_user.business_id).all()
    return render_template('services/index.html', services=services)

@services_bp.route('/services/new', methods=['GET', 'POST'])
@login_required
def create():
    if not current_user.business_id:
        flash('Сначала привяжитесь к бизнесу', 'warning')
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        service = Service(
            name=request.form.get('name'),
            price=float(request.form.get('price')),
            duration_minutes=int(request.form.get('duration_minutes')),
            business_id=current_user.business_id
        )
        db.session.add(service)
        db.session.commit()
        flash('Услуга добавлена', 'success')
        return redirect(url_for('services.index'))
    
    return render_template('services/form.html')

@services_bp.route('/services/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    if not current_user.business_id:
        flash('Сначала привяжитесь к бизнесу', 'warning')
        return redirect(url_for('dashboard.index'))
    
    service = Service.query.filter_by(
        id=id, 
        business_id=current_user.business_id
    ).first_or_404()
    
    if request.method == 'POST':
        service.name = request.form.get('name')
        service.price = float(request.form.get('price'))
        service.duration_minutes = int(request.form.get('duration_minutes'))
        
        db.session.commit()
        flash('Услуга обновлена', 'success')
        return redirect(url_for('services.index'))
    
    return render_template('services/form.html', service=service)

@services_bp.route('/services/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    if not current_user.business_id:
        flash('Сначала привяжитесь к бизнесу', 'warning')
        return redirect(url_for('dashboard.index'))
    
    service = Service.query.filter_by(
        id=id, 
        business_id=current_user.business_id
    ).first_or_404()
    
    db.session.delete(service)
    db.session.commit()
    flash('Услуга удалена', 'success')
    return redirect(url_for('services.index'))