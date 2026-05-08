from flask import render_template, request, redirect, url_for, flash, Blueprint, make_response
from app import db
from app.models.client import Client
from flask_login import login_required, current_user
import csv
import re

clients_bp = Blueprint('clients', __name__)

@clients_bp.route('/clients/export')
def export():
    if not current_user.business_id:
        flash('Сначала привяжитесь к бизнесу', 'warning')
        return redirect(url_for('dashboard.index'))

    clients = Client.query.filter_by(business_id=current_user.business_id).all()
    
    output = []
    output.append(['ID', 'Имя', 'Телефон', 'Комментарий', 'Дата регистрации'])
    
    for client in clients:
        output.append([
            client.id,
            client.name,
            client.phone,
            client.comment or '',
            client.created_at.strftime('%d.%m.%Y')
        ])
    
    import io
    si = io.StringIO()
    writer = csv.writer(si, delimiter=';')
    writer.writerows(output)
    
    response = make_response(si.getvalue().encode('utf-8-sig'))
    response.headers['Content-Disposition'] = 'attachment; filename=clients.csv'
    response.headers['Content-type'] = 'text/csv; charset=utf-8'
    
    return response
    
@clients_bp.route('/clients')
@login_required
def index():
    if not current_user.business_id:
        flash('Сначала привяжитесь к бизнесу', 'warning')
        return redirect(url_for('dashboard.index'))
    
    clients = Client.query.filter_by(business_id=current_user.business_id).all()
    return render_template('clients/index.html', clients=clients)

@clients_bp.route('/clients/new', methods=['GET','POST'])
@login_required
def create():
    if not current_user.business_id:
        flash('Сначала привяжитесь к бизнесу', 'warning')
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        comment = request.form.get('comment')
        
        # Валидация телефона
        is_valid, error_msg = validate_phone(phone)
        if not is_valid:
            flash(error_msg, 'danger')
            return render_template('clients/form.html', name=name, phone=phone, comment=comment)
        
        # Проверка на дубликат в рамках бизнеса
        existing = Client.query.filter_by(
            phone=phone,
            business_id=current_user.business_id
        ).first()
        
        if existing:
            flash(f'Клиент с номером {phone} уже существует в вашем бизнесе', 'danger')
            return render_template('clients/form.html', name=name, phone=phone, comment=comment)
        
        client = Client(
            name=name,
            phone=phone,
            comment=comment,
            business_id=current_user.business_id
        )
        db.session.add(client)
        db.session.commit()
        
        flash('Клиент успешно добавлен', 'success')
        return redirect(url_for('clients.index'))
    
    return render_template('clients/form.html')

@clients_bp.route('/clients/<int:id>/edit', methods=['GET','POST'])
@login_required
def edit(id):
    if not current_user.business_id:
        flash('Сначала привяжитесь к бизнесу', 'warning')
        return redirect(url_for('dashboard.index'))
    
    client = Client.query.filter_by(
        id=id, 
        business_id=current_user.business_id
    ).first_or_404()
    
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        comment = request.form.get('comment')
        
        # Валидация телефона
        is_valid, error_msg = validate_phone(phone)
        if not is_valid:
            flash(error_msg, 'danger')
            return render_template('clients/form.html', client=client)
        
        # Проверка на дубликат (исключая текущего клиента)
        existing = Client.query.filter(
            Client.phone == phone,
            Client.business_id == current_user.business_id,
            Client.id != id
        ).first()
        
        if existing:
            flash(f'Клиент с номером {phone} уже существует в вашем бизнесе', 'danger')
            return render_template('clients/form.html', client=client)
        
        client.name = name
        client.phone = phone
        client.comment = comment
        
        db.session.commit()
        flash('Клиент обновлен', 'success')
        return redirect(url_for('clients.index'))
    
    return render_template('clients/form.html', client=client)

@clients_bp.route('/clients/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    if not current_user.business_id:
        flash('Сначала привяжитесь к бизнесу', 'warning')
        return redirect(url_for('dashboard.index'))
    
    client = Client.query.filter_by(
        id=id,
        business_id=current_user.business_id
    ).first_or_404()
    
    db.session.delete(client)
    db.session.commit()
    flash('Клиент удалён', 'success')
    return redirect(url_for('clients.index'))

def validate_phone(phone):
    # Убираем все нецифровые символы
    digits = re.sub(r'\D', '', phone)
    
    # Проверяем длину (10 или 11 цифр)
    if len(digits) not in [10, 11]:
        return False, "Номер должен содержать 10 или 11 цифр"
    
    # Проверяем, что начинается с 7, 8 или +7
    if len(digits) == 11 and digits[0] not in ['7', '8']:
        return False, "Номер должен начинаться с 7 или 8"
    
    return True, None