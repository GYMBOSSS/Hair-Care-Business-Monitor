from flask import render_template, request, redirect, url_for, flash, Blueprint, make_response
from app import db
from app.models.client import Client
from flask_login import login_required, current_user
import csv

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
    
    clients = Client.query.all()
    return render_template('clients/index.html', clients=clients)

#хуй

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
        business_id = current_user.business_id
        
        client = Client(name=name, phone=phone, comment=comment, business_id=business_id)
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
        client.name = request.form.get('name')
        client.phone = request.form.get('phone')
        client.comment = request.form.get('comment')
        
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