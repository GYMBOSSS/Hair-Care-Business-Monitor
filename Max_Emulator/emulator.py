from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import logging
import requests
from datetime import datetime

app = Flask(__name__)
CORS(app)  
logging.basicConfig(level=logging.INFO)

all_messages = []
message_counter = 0

UI = """
<!DOCTYPE html>
<html>
<head>
    <title>MAX Эмулятор - Отправить сообщение боту</title>
    <style>
        body { font-family: sans-serif; padding: 20px; max-width: 900px; margin: 0 auto; background: #f5f5f5; }
        .container { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        textarea { width: 100%; padding: 10px; margin: 10px 0; font-size: 16px; border: 1px solid #ddd; border-radius: 5px; font-family: monospace; }
        button { padding: 10px 20px; background: #007bff; color: white; border: none; cursor: pointer; font-size: 16px; border-radius: 5px; }
        button:hover { background: #0056b3; }
        button:disabled { background: #ccc; cursor: not-allowed; }
        .log-container { 
            margin-top: 20px; 
            max-height: 500px; 
            overflow-y: auto; 
            background: #1e1e1e; 
            border-radius: 5px; 
            padding: 10px;
            font-family: 'Courier New', monospace;
            font-size: 13px;
        }
        .log { 
            border-bottom: 1px solid #333; 
            padding: 8px; 
            margin: 0;
            color: #d4d4d4;
        }
        .log-time { color: #858585; margin-right: 15px; }
        .log-type { 
            display: inline-block; 
            padding: 2px 8px; 
            border-radius: 3px; 
            margin-right: 10px;
            font-weight: bold;
        }
        .type-sent { background: #007bff; color: white; }
        .type-response { background: #28a745; color: white; }
        .type-error { background: #dc3545; color: white; }
        .type-info { background: #6c757d; color: white; }
        .log-text { color: #d4d4d4; white-space: pre-wrap; }
        .status { 
            margin-top: 10px; 
            padding: 8px; 
            border-radius: 5px; 
            font-size: 12px;
        }
        .status-online { background: #28a745; color: white; }
        .status-offline { background: #dc3545; color: white; }
        h1 { margin-top: 0; color: #333; }
        hr { margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Эмулятор MAX 🤖</h1>
        <p>Отправьте сообщение вашему боту (порт 5001):</p>
        
        <form id="messageForm">
            <textarea id="messageInput" rows="3" placeholder='Например: "Запишите на мойку завтра в 15:00"' required></textarea>
            <br>
            <button type="submit" id="sendBtn">📨 Отправить сообщение боту</button>
        </form>
        
        <div id="status" class="status status-offline">🔄 Проверка подключения...</div>
        
        <hr>
        
        <h3>📝 Лог сообщений:</h3>
        <div id="logContainer" class="log-container">
            <div class="log">
                <span class="log-time">--:--:--</span>
                <span class="log-type type-info">INFO</span>
                <span class="log-text">Ожидание сообщений...</span>
            </div>
        </div>
        
        <div style="margin-top: 15px; font-size: 12px; color: #666;">
            💡 Подсказка: Лог обновляется автоматически каждые 2 секунды
        </div>
    </div>

    <script>
        let lastMessageId = 0;
        
        // Функция для отправки сообщения
        document.getElementById('messageForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const messageInput = document.getElementById('messageInput');
            const sendBtn = document.getElementById('sendBtn');
            const message = messageInput.value.trim();
            
            if (!message) return;
            
            sendBtn.disabled = true;
            sendBtn.textContent = '⏳ Отправка...';
            
            try {
                const response = await fetch('/send', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: message })
                });
                
                if (response.ok) {
                    messageInput.value = '';
                } else {
                    alert('Ошибка при отправке');
                }
            } catch (err) {
                alert('Ошибка: ' + err.message);
            } finally {
                sendBtn.disabled = false;
                sendBtn.textContent = '📨 Отправить сообщение боту';
            }
        });
        
        // Функция для обновления лога
        async function updateLog() {
            try {
                const response = await fetch('/api/messages?after=' + lastMessageId);
                const data = await response.json();
                
                if (data.messages && data.messages.length > 0) {
                    const logContainer = document.getElementById('logContainer');
                    
                    for (const msg of data.messages) {
                        const logDiv = document.createElement('div');
                        logDiv.className = 'log';
                        logDiv.innerHTML = `
                            <span class="log-time">${msg.time}</span>
                            <span class="log-type type-${msg.type}">${msg.typeLabel}</span>
                            <span class="log-text">${escapeHtml(msg.text)}</span>
                        `;
                        logContainer.appendChild(logDiv);
                        lastMessageId = msg.id;
                    }
                    
                    logContainer.scrollTop = logContainer.scrollHeight;
                    
                    // Ограничиваем количество сообщений в DOM (оставляем последние 100)
                    while (logContainer.children.length > 100) {
                        logContainer.removeChild(logContainer.firstChild);
                    }
                }
            } catch (err) {
                console.error('Ошибка обновления лога:', err);
            }
        }
        
        async function checkStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                const statusDiv = document.getElementById('status');
                
                if (data.bot_online) {
                    statusDiv.className = 'status status-online';
                    statusDiv.innerHTML = '✅ Бот на порту 5001: онлайн';
                } else {
                    statusDiv.className = 'status status-offline';
                    statusDiv.innerHTML = '❌ Бот на порту 5001: офлайн (запусти bot.py)';
                }
            } catch (err) {
                console.error('Ошибка проверки статуса:', err);
            }
        }
        
        // Экранирование HTML
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        // Запускаем периодическое обновление
        setInterval(updateLog, 2000);
        setInterval(checkStatus, 5000);
        updateLog();
        checkStatus();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(UI)

@app.route('/send', methods=['POST'])
def send_message():
    global message_counter
    data = request.json
    user_message = data.get('message')
    
    message_counter += 1
    all_messages.append({
        'id': message_counter,
        'time': datetime.now().strftime('%H:%M:%S'),
        'type': 'sent',
        'typeLabel': '📤 ОТПРАВКА',
        'text': user_message
    })
    
    webhook_payload = {
        "message": {
            "chat": {"id": 12345},
            "text": user_message,
            "from": {"first_name": "ТестовыйПользователь"}
        }
    }
    
    try:
        resp = requests.post('http://localhost:5001/webhook/test_bot_token_123', json=webhook_payload, timeout=5)
        
        message_counter += 1
        all_messages.append({
            'id': message_counter,
            'time': datetime.now().strftime('%H:%M:%S'),
            'type': 'info',
            'typeLabel': '✅ СТАТУС',
            'text': f'Бот ответил HTTP {resp.status_code}'
        })
        
    except requests.exceptions.ConnectionError:
        message_counter += 1
        all_messages.append({
            'id': message_counter,
            'time': datetime.now().strftime('%H:%M:%S'),
            'type': 'error',
            'typeLabel': '❌ ОШИБКА',
            'text': 'Не удалось подключиться к боту (порт 5001). Запусти bot.py!'
        })
    except Exception as e:
        message_counter += 1
        all_messages.append({
            'id': message_counter,
            'time': datetime.now().strftime('%H:%M:%S'),
            'type': 'error',
            'typeLabel': '❌ ОШИБКА',
            'text': str(e)
        })
    
    return jsonify({'ok': True})

@app.route('/bot<token>/sendMessage', methods=['POST'])
def bot_send_message(token):
    global message_counter
    data = request.json
    text = data.get('text')
    
    message_counter += 1
    all_messages.append({
        'id': message_counter,
        'time': datetime.now().strftime('%H:%M:%S'),
        'type': 'response',
        'typeLabel': '🤖 ОТВЕТ',
        'text': text
    })
    
    logging.info(f"[ЭМУЛЯТОР MAX] Бот ответил: {text}")
    
    return jsonify({"ok": True, "result": {"message_id": 1, "text": text}})

@app.route('/api/messages')
def get_messages():
    after = request.args.get('after', 0, type=int)
    new_messages = [m for m in all_messages if m['id'] > after]
    return jsonify({'messages': new_messages})

@app.route('/api/status')
def get_status():
    try:
        resp = requests.post(
            'http://localhost:5001/webhook/test_bot_token_123',
            json={"message": {"chat": {"id": 999}, "text": "/start"}},
            timeout=2
        )
        bot_online = resp.status_code == 200
    except requests.exceptions.ConnectionError:
        bot_online = False
    except Exception:
        bot_online = False
    
    return jsonify({'bot_online': bot_online})

if __name__ == '__main__':
    print("=" * 60)
    print("🤖 MAX Эмулятор запущен!")
    print("📱 Открой в браузере: http://127.0.0.1:9000")
    print("=" * 60)
    app.run(port=9000, debug=True)