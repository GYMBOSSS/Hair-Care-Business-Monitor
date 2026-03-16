from flask import render_template, request, redirect, url_for, flash
from app import db
from app.models.client import Client
from flask import Blueprint

clients_bp = Blueprint('clients', __name__)

@clients_bp.route('/clients')
def index():
    """Список всех клиентов"""
    clients = Client.query.all()
    return render_template('clients/index.html', clients=clients)

@clients_bp.route('/clients/new', methods=['GET','POST'])
def create():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        car_info = request.form.get('car_info')
        
        client = Client(name=name, phone=phone, car_info=car_info)
        db.session.add(client)
        db.session.commit()
        
        flash('Клиент успешно добавлен', 'success')
        return redirect(url_for('clients.index'))
    
    return render_template('clients/form.html')

@clients_bp.route('/clients/<int:id>/edit', methods=['GET','POST'])
def edit(id):
    client = Client.query.get_or_404(id)
    print("Метод edit начал работу")
    if request.method == 'POST':
        print("="*50)
        print("ФОРМА ОТПРАВЛЕНА!")
        print(f"ID клиента: {id}")
        print(f"Данные из формы: {dict(request.form)}")
        print(f"Было в БД: {client.name}, {client.phone}")
        
        client.name = request.form.get('name')
        client.phone = request.form.get('phone')
        client.car_info = request.form.get('car_info')
        
        print(f"Стало в объекте: {client.name}, {client.phone}")
        
        db.session.commit()
        
        check = Client.query.get(id)
        print(f"После коммита в БД: {check.name}, {check.phone}")
        print("="*50)
        
        flash('Клиент обновлён', 'success')
        return redirect(url_for('clients.index'))
    
    return render_template('clients/form.html', client=client)

@clients_bp.route('/clients/<int:id>/delete', methods=['POST'])
def delete(id):
    client = Client.query.get_or_404(id)
    db.session.delete(client)
    db.session.commit()
    flash('Клиент удалён', 'success')
    return redirect(url_for('clients.index'))