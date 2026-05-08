from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.business import Business
from app.models.client import Client
from app.models.service import Service
from app.models.appointment import Appointment
from datetime import datetime, timedelta
import logging

api_bp = Blueprint('api', __name__)
logger = logging.getLogger(__name__)


# ============================================================
# 1. API ДЛЯ БОТА (вызывается из bot/bot.py)
# ============================================================

@api_bp.route('/api/bot/services', methods=['GET'])
def get_services():
    """Возвращает список услуг для бизнеса по токену"""
    token = request.args.get('token')
    
    business = Business.query.filter_by(bot_token=token).first()
    if not business:
        return jsonify({'error': 'Unauthorized'}), 401
    
    services = Service.query.filter_by(business_id=business.id).all()
    
    return jsonify({
        'services': [
            {'id': s.id, 'name': s.name, 'price': s.price, 'duration': s.duration_minutes}
            for s in services
        ]
    })


@api_bp.route('/api/bot/check_slot', methods=['POST'])
def check_slot():
    """Проверяет, свободен ли слот для записи"""
    data = request.json
    token = data.get('token')
    service_id = data.get('service_id')
    date_str = data.get('date')
    time_str = data.get('time')
    
    business = Business.query.filter_by(bot_token=token).first()
    if not business:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Парсим дату и время
    try:
        appointment_time = datetime.fromisoformat(f"{date_str}T{time_str}")
    except:
        return jsonify({'error': 'Invalid datetime format'}), 400
    
    # Проверяем, есть ли уже запись на это время
    existing = Appointment.query.filter_by(
        business_id=business.id,
        appointment_time=appointment_time,
        status='scheduled'
    ).first()
    
    if existing:
        return jsonify({'free': False, 'reason': 'slot_taken'})
    
    # Проверяем рабочие часы (можно настроить для каждого бизнеса)
    hour = appointment_time.hour
    if hour < 9 or hour > 20:
        return jsonify({'free': False, 'reason': 'outside_working_hours'})
    
    return jsonify({'free': True})


@api_bp.route('/api/bot/free_slots', methods=['GET'])
def get_free_slots():
    """Возвращает список свободных слотов на указанную дату"""
    token = request.args.get('token')
    service_id = request.args.get('service_id', type=int)
    date_str = request.args.get('date')
    
    business = Business.query.filter_by(bot_token=token).first()
    if not business:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        date = datetime.fromisoformat(date_str).date()
    except:
        return jsonify({'error': 'Invalid date format'}), 400
    
    # Все записи на эту дату
    start_of_day = datetime.combine(date, datetime.min.time())
    end_of_day = datetime.combine(date, datetime.max.time())
    
    booked = Appointment.query.filter(
        Appointment.business_id == business.id,
        Appointment.appointment_time >= start_of_day,
        Appointment.appointment_time <= end_of_day,
        Appointment.status == 'scheduled'
    ).all()
    
    booked_times = [a.appointment_time.time() for a in booked]
    
    # Генерируем слоты (каждый час с 9 до 20)
    all_slots = []
    for hour in range(9, 21):
        slot_time = datetime.now().replace(hour=hour, minute=0, second=0).time()
        if slot_time not in booked_times:
            all_slots.append(slot_time.strftime('%H:%M'))
    
    return jsonify({'slots': all_slots})


@api_bp.route('/api/bot/create_appointment', methods=['POST'])
def create_appointment():
    """Создаёт запись через бота"""
    data = request.json
    token = data.get('token')
    client_name = data.get('client_name')
    client_phone = data.get('client_phone')
    service_id = data.get('service_id')
    appointment_time_str = data.get('appointment_time')
    chat_id = data.get('chat_id')
    
    business = Business.query.filter_by(bot_token=token).first()
    if not business:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Парсим время
    try:
        appointment_time = datetime.fromisoformat(appointment_time_str)
    except:
        return jsonify({'error': 'Invalid datetime format'}), 400
    
    # Проверяем, не занято ли время (повторная проверка)
    existing = Appointment.query.filter_by(
        business_id=business.id,
        appointment_time=appointment_time,
        status='scheduled'
    ).first()
    
    if existing:
        return jsonify({'error': 'Slot already taken'}), 409
    
    # Находим или создаём клиента
    client = Client.query.filter_by(
        phone=client_phone,
        business_id=business.id
    ).first()
    
    if not client:
        client = Client(
            name=client_name,
            phone=client_phone,
            chat_id=str(chat_id) if chat_id else None,
            business_id=business.id
        )
        db.session.add(client)
        db.session.commit()
    
    # Создаём запись
    appointment = Appointment(
        client_id=client.id,
        service_id=service_id,
        appointment_time=appointment_time,
        business_id=business.id,
        status='scheduled'
    )
    db.session.add(appointment)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'appointment_id': appointment.id,
        'message': f'✅ Вы записаны на {appointment_time.strftime("%d.%m.%Y %H:%M")}'
    })


@api_bp.route('/api/bot/my_appointments', methods=['GET'])
def get_my_appointments():
    """Возвращает записи пользователя по chat_id"""
    token = request.args.get('token')
    chat_id = request.args.get('chat_id')
    
    business = Business.query.filter_by(bot_token=token).first()
    if not business:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Находим клиента по chat_id
    client = Client.query.filter_by(
        chat_id=chat_id,
        business_id=business.id
    ).first()
    
    if not client:
        return jsonify({'appointments': []})
    
    appointments = Appointment.query.filter_by(
        client_id=client.id,
        business_id=business.id
    ).filter(
        Appointment.status.in_(['scheduled', 'completed'])
    ).order_by(Appointment.appointment_time.desc()).all()
    
    return jsonify({
        'appointments': [
            {
                'id': a.id,
                'service': a.service.name,
                'price': a.service.price,
                'time': a.appointment_time.isoformat(),
                'status': a.status
            }
            for a in appointments
        ]
    })


@api_bp.route('/api/bot/cancel_appointment', methods=['POST'])
def cancel_appointment():
    """Отменяет запись"""
    data = request.json
    token = data.get('token')
    appointment_id = data.get('appointment_id')
    chat_id = data.get('chat_id')
    
    business = Business.query.filter_by(bot_token=token).first()
    if not business:
        return jsonify({'error': 'Unauthorized'}), 401
    
    appointment = Appointment.query.filter_by(
        id=appointment_id,
        business_id=business.id
    ).first()
    
    if not appointment:
        return jsonify({'error': 'Appointment not found'}), 404
    
    # Проверяем, что запись принадлежит клиенту с этим chat_id
    client = Client.query.get(appointment.client_id)
    if client.chat_id != str(chat_id):
        return jsonify({'error': 'Unauthorized'}), 403
    
    if appointment.status != 'scheduled':
        return jsonify({'error': 'Cannot cancel completed appointment'}), 400
    
    appointment.status = 'cancelled'
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Запись отменена'})


# ============================================================
# 2. API ДЛЯ ВЕБ-ИНТЕРФЕЙСА (управление ботом)
# ============================================================

@api_bp.route('/api/bot/save_token', methods=['POST'])
@login_required
def save_bot_token():
    """Сохраняет токен бота для текущего бизнеса"""
    if current_user.role != 'owner':
        return jsonify({'error': 'Доступ запрещён'}), 403
    
    if not current_user.business_id:
        return jsonify({'error': 'Бизнес не найден'}), 404
    
    data = request.json
    bot_token = data.get('bot_token')
    
    if not bot_token:
        return jsonify({'error': 'Токен не может быть пустым'}), 400
    
    business = Business.query.get(current_user.business_id)
    business.bot_token = bot_token
    db.session.commit()
    
    return jsonify({'success': True})


@api_bp.route('/api/bot/get_token', methods=['GET'])
@login_required
def get_bot_token():
    """Возвращает сохранённый токен бота"""
    if not current_user.business_id:
        return jsonify({'error': 'Бизнес не найден'}), 404
    
    business = Business.query.get(current_user.business_id)
    
    return jsonify({'bot_token': business.bot_token})


@api_bp.route('/api/bot/webhook_url', methods=['GET'])
@login_required
def get_webhook_url():
    """Возвращает webhook URL для настройки бота"""
    if not current_user.business_id:
        return jsonify({'error': 'Бизнес не найден'}), 404
    
    business = Business.query.get(current_user.business_id)
    if not business.bot_token:
        return jsonify({'error': 'Токен не сохранён'}), 404
    
    # Здесь должен быть реальный домен
    from app import app
    base_url = app.config.get('BASE_URL', 'https://ваш-сервер.ru')
    webhook_url = f"{base_url}/webhook/{business.bot_token}"
    
    return jsonify({'webhook_url': webhook_url})


# ============================================================
# 3. ВСПОМОГАТЕЛЬНЫЕ API
# ============================================================

@api_bp.route('/api/business/info', methods=['GET'])
@login_required
def get_business_info():
    """Информация о бизнесе текущего пользователя"""
    if not current_user.business_id:
        return jsonify({'error': 'Бизнес не найден'}), 404
    
    business = Business.query.get(current_user.business_id)
    
    return jsonify({
        'id': business.id,
        'name': business.name,
        'phone': business.phone,
        'address': business.address,
        'has_bot': bool(business.bot_token)
    })