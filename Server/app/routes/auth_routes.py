from flask import render_template, redirect, url_for, flash, request, Blueprint
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from datetime import datetime
from app.models.user import User
from app.models.business import Business
from app.models.invite import Invite
from werkzeug.security import generate_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Вход выполнен успешно', 'success')
            return redirect(url_for('dashboard.index'))
        else:
            flash('Неверное имя пользователя или пароль', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'employee')
        
        if User.query.filter_by(username=username).first():
            flash('Имя пользователя уже занято', 'danger')
            return redirect(url_for('auth.register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email уже зарегистрирован', 'danger')
            return redirect(url_for('auth.register'))
        
        user = User(
            username=username,
            email=email,
            role=role
        )
        user.set_password(password)
        
        if role == 'owner':
            db.session.add(user)
            db.session.commit()
    
            login_user(user)
            
            flash('Регистрация успешна! Теперь создайте свой бизнес', 'success')
            return redirect(url_for('auth.create_business'))
        else:  # employee
            db.session.add(user)
            db.session.commit()
            
            login_user(user)
            
            flash('Регистрация успешна! Теперь выберите бизнес для вступления', 'success')
            return redirect(url_for('auth.join_business'))
        
    return render_template('auth/register.html')

import re

def validate_phone(phone):
    digits = re.sub(r'\D', '', phone)
    if len(digits) not in [10, 11]:
        return False, "Номер телефона должен содержать 10 или 11 цифр"
    if len(digits) == 11 and digits[0] not in ['7', '8']:
        return False, "Номер должен начинаться с 7 или 8"
    return True, None

@auth_bp.route('/create-business', methods=['GET', 'POST'])
@login_required
def create_business():
    if current_user.role != 'owner':
        flash('Только владелец может создать бизнес', 'danger')
        return redirect(url_for('dashboard.index'))
    
    if current_user.business_id:
        flash('Вы уже привязаны к бизнесу', 'info')
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        address = request.form.get('address')
        phone = request.form.get('phone')
        description = request.form.get('description')
        
        # Валидация телефона
        is_valid, error_msg = validate_phone(phone)
        if not is_valid:
            flash(error_msg, 'danger')
            return render_template('auth/create_business.html')
        
        business = Business(
            name=name,
            address=address,
            phone=phone,
            description=description
        )
        
        db.session.add(business)
        db.session.flush()
        
        current_user.business_id = business.id
        db.session.commit()
        
        flash('Бизнес успешно создан!', 'success')
        return redirect(url_for('dashboard.index'))
    
    return render_template('auth/create_business.html')

@auth_bp.route('/join-business', methods=['GET', 'POST'])
@login_required
def join_business():
    if current_user.role != 'employee':
        flash('Эта страница только для сотрудников', 'danger')
        return redirect(url_for('dashboard.index'))
    
    if current_user.business_id:
        flash('Вы уже привязаны к бизнесу', 'info')
        return redirect(url_for('dashboard.index'))
    
    existing_invite = Invite.query.filter_by(
        user_id=current_user.id,
        status='pending'
    ).first()
    
    if existing_invite:
        flash('У вас уже есть активная заявка', 'info')
        return redirect(url_for('auth.my_invites'))
    
    if request.method == 'POST':
        business_id = request.form.get('business_id')
        
        if not business_id:
            flash('Выберите бизнес', 'danger')
            return redirect(url_for('auth.join_business'))
        
        invite = Invite(
            user_id=current_user.id,
            business_id=business_id,
            status='pending'
        )
        
        db.session.add(invite)
        db.session.commit()
        
        flash('Заявка отправлена! Ожидайте подтверждения владельца', 'success')
        return redirect(url_for('auth.my_invites'))
    
    businesses = Business.query.all()
    return render_template('auth/join_business.html', businesses=businesses)

@auth_bp.route('/my-invites')
@login_required
def my_invites():
    # Мои заявки (для сотрудников)
    invites = Invite.query.filter_by(user_id=current_user.id).order_by(Invite.created_at.desc()).all()
    return render_template('auth/my_invites.html', invites=invites)

@auth_bp.route('/invites')
@login_required
def invites():
    # Только владельцы видят заявки
    if current_user.role != 'owner' or not current_user.business_id:
        flash('Доступ запрещён', 'danger')
        return redirect(url_for('dashboard.index'))
    
    pending_invites = Invite.query.filter_by(
        business_id=current_user.business_id,
        status='pending'
    ).all()
    
    return render_template('auth/invites.html', invites=pending_invites)

@auth_bp.route('/invite/<int:invite_id>/<action>', methods=['POST'])
@login_required
def handle_invite(invite_id, action):
    if current_user.role != 'owner' or not current_user.business_id:
        flash('Доступ запрещён', 'danger')
        return redirect(url_for('dashboard.index'))
    
    invite = Invite.query.get_or_404(invite_id)
    
    # Проверяем, что заявка относится к бизнесу владельца
    if invite.business_id != current_user.business_id:
        flash('Чужая заявка', 'danger')
        return redirect(url_for('auth.invites'))
    
    if action == 'accept':
        invite.status = 'accepted'
        invite.responded_at = datetime.utcnow()
        
        # Привязываем пользователя к бизнесу
        user = User.query.get(invite.user_id)
        user.business_id = current_user.business_id
        
        flash(f'Пользователь {user.username} принят в бизнес', 'success')
    
    elif action == 'reject':
        invite.status = 'rejected'
        invite.responded_at = datetime.utcnow()
        flash('Заявка отклонена', 'info')
    
    db.session.commit()
    return redirect(url_for('auth.invites'))

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('auth.login'))

def validate_phone(phone):
    if not phone:
        return True, None  # пустое поле — ок (необязательно)
    
    # Убираем все нецифровые символы
    digits = re.sub(r'\D', '', phone)
    
    # Проверяем длину (10 или 11 цифр)
    if len(digits) not in [10, 11]:
        return False, "Номер телефона должен содержать 10 или 11 цифр"
    
    # Проверяем, что начинается с 7 или 8 (для российских номеров)
    if len(digits) == 11 and digits[0] not in ['7', '8']:
        return False, "Номер должен начинаться с 7 или 8"
    
    return True, None