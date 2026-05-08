import asyncio
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Optional

from aiohttp import web, ClientSession

# ============================================================
# КОНФИГУРАЦИЯ
# ============================================================

CRM_URL = "http://localhost:5000"  # URL твоей CRM
BOT_TOKEN = "test_bot_token_123"    # Тестовый токен
PORT = 5001                          # Порт, на котором будет висеть бот

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Хранилище сессий пользователей
sessions = {}


# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (извлечение даты, времени, и т.д.)
# ============================================================

def extract_service_name(text: str, services: list) -> Optional[str]:
    """Извлекает название услуги из текста"""
    text_lower = text.lower()
    
    for service in services:
        if service['name'].lower() in text_lower:
            return service['name']
    
    keywords = {
        'мойка': 'Мойка',
        'стрижка': 'Стрижка',
        'маникюр': 'Маникюр',
        'педикюр': 'Педикюр',
        'чистка': 'Чистка',
    }
    
    for key, name in keywords.items():
        if key in text_lower:
            return name
    
    return None


def extract_date(text: str) -> Optional[datetime]:
    """Извлекает дату из текста"""
    today = datetime.now().date()
    text_lower = text.lower()
    
    if 'сегодня' in text_lower:
        return datetime.now()
    if 'завтра' in text_lower:
        return datetime.now() + timedelta(days=1)
    
    days_map = {
        'понедельник': 0, 'вторник': 1, 'среда': 2, 'четверг': 3,
        'пятница': 4, 'суббота': 5, 'воскресенье': 6
    }
    
    for day_name, day_num in days_map.items():
        if day_name in text_lower:
            days_ahead = day_num - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            return datetime.now() + timedelta(days=days_ahead)
    
    date_pattern = r'(\d{1,2})[\.\s](\d{1,2})'
    match = re.search(date_pattern, text)
    if match:
        day = int(match.group(1))
        month = int(match.group(2))
        try:
            return datetime(today.year, month, day)
        except:
            pass
    
    return None


def extract_time(text: str) -> Optional[datetime]:
    """Извлекает время из текста"""
    now = datetime.now()
    
    time_patterns = [
        (r'(\d{1,2})[:.](\d{2})', lambda h, m: now.replace(hour=h, minute=m, second=0)),
        (r'в (\d{1,2}) часов?', lambda h, _: now.replace(hour=h, minute=0, second=0)),
        (r'в (\d{1,2})', lambda h, _: now.replace(hour=h, minute=0, second=0)),
    ]
    
    for pattern, builder in time_patterns:
        match = re.search(pattern, text)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2)) if len(match.groups()) > 1 else 0
            try:
                return builder(hour, minute)
            except:
                pass
    
    return None


def extract_phone(text: str) -> Optional[str]:
    """Извлекает телефон из текста"""
    phone_pattern = r'(\+?7|8)?[\s\-]?\(?(\d{3})\)?[\s\-]?(\d{3})[\s\-]?(\d{2})[\s\-]?(\d{2})'
    match = re.search(phone_pattern, text)
    
    if match:
        phone = ''.join(filter(str.isdigit, match.group(0)))
        if len(phone) == 11:
            phone = '+' + phone
        elif len(phone) == 10:
            phone = '+7' + phone
        return phone
    return None


def extract_name(text: str, phone: Optional[str] = None) -> Optional[str]:
    """Извлекает имя из текста"""
    if phone:
        name = text.split(phone)[0].strip()
        if name:
            return name
    
    name_pattern = r'^([А-Яа-яЁё]+(?:\s+[А-Яа-яЁё]+){0,2})'
    match = re.search(name_pattern, text)
    if match:
        return match.group(1)
    
    return None


# ============================================================
# КЛАСС ДЛЯ ХРАНЕНИЯ СОСТОЯНИЯ ДИАЛОГА
# ============================================================

class UserSession:
    def __init__(self):
        self.service_id = None
        self.service_name = None
        self.appointment_date = None
        self.appointment_time = None
        self.client_name = None
        self.client_phone = None
        self.waiting_for = None  


# ============================================================
# ОСНОВНАЯ ЛОГИКА ОБРАБОТКИ СООБЩЕНИЙ
# ============================================================

async def send_to_crm(endpoint: str, data: dict, method: str = 'post') -> dict:
    async with ClientSession() as session:
        url = f"{CRM_URL}{endpoint}"
        if method == 'post':
            async with session.post(url, json=data) as resp:
                return await resp.json()
        else:
            async with session.get(url, params=data) as resp:
                return await resp.json()


async def process_message(chat_id: int, text: str) -> str:
    
    if chat_id not in sessions:
        sessions[chat_id] = UserSession()
    session = sessions[chat_id]
    
    business_token = BOT_TOKEN
    text_lower = text.lower().strip()
    
    if text_lower == '/start':
        session.waiting_for = None
        return (
            "👋 Привет! Я бот для записи к вам в сервис.\n\n"
            "Что я умею:\n"
            "📅 Записаться на услугу\n"
            "💰 Узнать стоимость\n"
            "📋 Мои записи\n"
            "❌ Отменить запись\n\n"
            "Например: «Запишите на мойку завтра в 15:00»"
        )
    
    if text_lower == '/help':
        return (
            "📋 Доступные команды:\n\n"
            "/start - Начать заново\n"
            "/help - Эта справка\n\n"
            "А ещё я понимаю фразы:\n"
            "- «Запишите меня на завтра»\n"
            "- «Сколько стоит мойка?»\n"
            "- «Мои записи»\n"
            "- «Отмени запись 123»"
        )
    
    if session.waiting_for == 'name_and_phone':
        phone = extract_phone(text)
        name = extract_name(text, phone)
        
        if name and phone:
            session.client_name = name
            session.client_phone = phone
            session.waiting_for = 'confirmation'
            
            return (
                f"✅ Спасибо, {name}!\n\n"
                f"Проверьте данные:\n"
                f"📋 Услуга: {session.service_name}\n"
                f"📅 Дата: {session.appointment_date.strftime('%d.%m.%Y') if session.appointment_date else 'не указана'}\n"
                f"⏰ Время: {session.appointment_time.strftime('%H:%M') if session.appointment_time else 'не указано'}\n"
                f"👤 Имя: {name}\n"
                f"📞 Телефон: {phone}\n\n"
                f"Всё верно? Напишите «да» или «нет»"
            )
        else:
            return "📝 Напишите, пожалуйста, ваше имя и телефон.\n\nНапример: «Иван Петров, +79991234567»"
    
    if session.waiting_for == 'confirmation':
        if text_lower in ['да', '+', 'yes', 'конечно', 'верно', 'ок']:
            session.waiting_for = None
            
            result = await send_to_crm("/api/bot/create_appointment", {
                'token': business_token,
                'client_name': session.client_name,
                'client_phone': session.client_phone,
                'service_id': session.service_id,
                'appointment_time': session.appointment_time.isoformat() if session.appointment_time else None,
                'chat_id': chat_id
            })
            
            if result.get('success'):
                return result.get('message', '✅ Вы успешно записаны!')
            else:
                return f"❌ Ошибка: {result.get('error', 'Неизвестная ошибка')}"
        else:
            session.waiting_for = None
            return "❌ Запись отменена. Можете начать заново командой /start"
    
    if any(word in text_lower for word in ['запись', 'запишите', 'хочу записаться', 'записать']):
        return await handle_booking_start(business_token, chat_id, text)
    
    if any(word in text_lower for word in ['цена', 'сколько стоит', 'стоимость', 'прайс']):
        return await handle_price(business_token, text)
    
    if any(word in text_lower for word in ['мои записи', 'мои запись', 'что у меня']):
        return await handle_my_appointments(business_token, chat_id)
    
    if any(word in text_lower for word in ['отмени', 'отменить', 'удали']):
        return await handle_cancel(business_token, chat_id, text)
    
    return "🤔 Я вас не понял. Напишите /help для списка команд."


async def handle_booking_start(business_token: str, chat_id: int, text: str) -> str:
    services_data = await send_to_crm("/api/bot/services", {'token': business_token}, method='get')
    services = services_data.get('services', [])
    
    if not services:
        return "❌ Услуги пока не добавлены. Обратитесь к администратору."
    
    service_name = extract_service_name(text, services)
    
    if not service_name:
        services_list = "\n".join([f"• {s['name']} — {s['price']} ₽" for s in services[:5]])
        return f"🔍 Какую услугу вы хотите?\n\nДоступные услуги:\n{services_list}"
    
    service = next((s for s in services if s['name'].lower() == service_name.lower()), None)
    if not service:
        return f"❌ Услуга «{service_name}» не найдена."
    
    # Извлекаем дату и время
    appointment_date = extract_date(text)
    appointment_time = extract_time(text)
    
    if not appointment_date:
        return f"📅 Услуга: {service_name} — {service['price']} ₽\n\nУточните дату записи."
    
    if not appointment_time:
        return f"📅 Услуга: {service_name} — {service['price']} ₽\nДата: {appointment_date.strftime('%d.%m.%Y')}\n\nУточните время записи."
    
    # Проверяем слот
    check_result = await send_to_crm("/api/bot/check_slot", {
        'token': business_token,
        'service_id': service['id'],
        'date': appointment_date.date().isoformat(),
        'time': appointment_time.time().isoformat()
    })
    
    if not check_result.get('free'):
        slots_data = await send_to_crm("/api/bot/free_slots", {
            'token': business_token,
            'service_id': service['id'],
            'date': appointment_date.date().isoformat()
        }, method='get')
        
        free_slots = slots_data.get('slots', [])
        if free_slots:
            slots_str = ", ".join(free_slots[:5])
            return f"⏰ Время {appointment_time.strftime('%H:%M')} уже занято.\n\nСвободные слоты: {slots_str}"
        else:
            return "❌ На этот день нет свободных слотов."
    
    # Сохраняем в сессию
    session = sessions.get(chat_id, UserSession())
    session.service_id = service['id']
    session.service_name = service_name
    session.appointment_date = appointment_date
    session.appointment_time = appointment_time
    session.waiting_for = 'name_and_phone'
    sessions[chat_id] = session
    
    return (
        f"✅ Услуга: {service_name} — {service['price']} ₽\n"
        f"📅 Дата: {appointment_date.strftime('%d.%m.%Y')}\n"
        f"⏰ Время: {appointment_time.strftime('%H:%M')}\n\n"
        f"📝 Теперь укажите ваше имя и телефон для записи.\n"
        f"Например: «Иван Петров, +79991234567»"
    )


async def handle_price(business_token: str, text: str) -> str:
    services_data = await send_to_crm("/api/bot/services", {'token': business_token}, method='get')
    services = services_data.get('services', [])
    
    if not services:
        return "💰 Услуги пока не добавлены."
    
    service_name = extract_service_name(text, services)
    if service_name:
        service = next((s for s in services if s['name'].lower() == service_name.lower()), None)
        if service:
            return f"💰 {service['name']} — {service['price']} ₽"
    
    reply = "💰 Наши услуги:\n\n"
    for s in services:
        reply += f"• {s['name']} — {s['price']} ₽\n"
    return reply


async def handle_my_appointments(business_token: str, chat_id: int) -> str:
    data = await send_to_crm("/api/bot/my_appointments", {
        'token': business_token,
        'chat_id': chat_id
    }, method='get')
    
    appointments = data.get('appointments', [])
    
    if not appointments:
        return "📋 У вас пока нет записей."
    
    reply = "📋 Ваши записи:\n\n"
    for app in appointments:
        dt = datetime.fromisoformat(app['time'])
        status_emoji = "✅" if app['status'] == 'completed' else "⏳"
        reply += f"{status_emoji} {dt.strftime('%d.%m.%Y %H:%M')} — {app['service']} ({app['price']} ₽)\n"
    
    return reply


async def handle_cancel(business_token: str, chat_id: int, text: str) -> str:
    """Отмена записи"""
    data = await send_to_crm("/api/bot/my_appointments", {
        'token': business_token,
        'chat_id': chat_id
    }, method='get')
    
    appointments = data.get('appointments', [])
    active = [a for a in appointments if a['status'] == 'scheduled']
    
    if not active:
        return "📋 У вас нет активных записей для отмены."
    
    id_match = re.search(r'(\d+)', text)
    if id_match:
        appointment_id = int(id_match.group(1))
        cancel_result = await send_to_crm("/api/bot/cancel_appointment", {
            'token': business_token,
            'appointment_id': appointment_id,
            'chat_id': chat_id
        })
        
        if cancel_result.get('success'):
            return "✅ Запись отменена."
        else:
            return "❌ Не удалось отменить запись."
    
    reply = "❌ Какую запись отменить? Напишите её номер:\n\n"
    for app in active:
        dt = datetime.fromisoformat(app['time'])
        reply += f"ID {app['id']}: {dt.strftime('%d.%m.%Y %H:%M')} — {app['service']}\n"
    
    return reply


# ============================================================
# WEBHOOK ОБРАБОТЧИК (принимает сообщения от MAX/эмулятора)
# ============================================================

async def webhook_handler(request):
    try:
        data = await request.json()
        message = data.get('message', {})
        chat_id = message.get('chat', {}).get('id')
        text = message.get('text', '')
        
        if not chat_id or not text:
            return web.Response(text='OK', status=200)
        
        logger.info(f"Получено сообщение от {chat_id}: {text}")
        
        # Обрабатываем сообщение
        reply = await process_message(chat_id, text)
        
        # Отправляем ответ через эмулятор MAX
        async with ClientSession() as session:
            await session.post(f"http://localhost:9000/bot{BOT_TOKEN}/sendMessage", json={
                'chat_id': chat_id,
                'text': reply
            })
        
        return web.Response(text='OK', status=200)
        
    except Exception as e:
        logger.error(f"Ошибка в webhook: {e}")
        return web.Response(text='Error', status=500)


# ============================================================
# ЗАПУСК WEB-СЕРВЕРА БОТА
# ============================================================

app = web.Application()
app.router.add_post('/webhook/{token}', webhook_handler)

if __name__ == '__main__':
    logger.info(f"Бот запущен на порту {PORT}")
    web.run_app(app, port=PORT)