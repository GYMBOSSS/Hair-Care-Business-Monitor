from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import logging
import requests
from datetime import datetime

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.WARNING)  # Уровень WARNING, чтобы не плодить INFO

# Хранилище последнего ответа бота (только для текущей сессии)
last_reply = None

UI = """
<!DOCTYPE html>
<html>
<head>
    <title>MAX Эмулятор - Чат с ботом</title>
    <style>
        body { font-family: sans-serif; padding: 20px; max-width: 800px; margin: 0 auto; background: #f5f5f5; }
        .container { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .chat-area { min-height: 400px; max-height: 500px; overflow-y: auto; border: 1px solid #ddd; border-radius: 5px; padding: 10px; background: #fafafa; }
        .message { margin: 10px 0; padding: 8px 12px; border-radius: 10px; max-width: 80%; }
        .user-message { background: #007bff; color: white; text-align: right; margin-left: auto; }
        .bot-message { background: #e9ecef; color: #333; }
        textarea { width: 100%; padding: 10px; margin: 10px 0; font-size: 16px; border: 1px solid #ddd; border-radius: 5px; }
        button { padding: 10px 20px; background: #007bff; color: white; border: none; cursor: pointer; font-size: 16px; border-radius: 5px; }
        button:disabled { background: #ccc; }
        .status { margin-top: 10px; padding: 8px; border-radius: 5px; font-size: 12px; text-align: center; }
        .status-online { background: #28a745; color: white; }
        .status-offline { background: #dc3545; color: white; }
        h1 { margin-top: 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 MAX Эмулятор — Чат с ботом</h1>
        <p>Тестирование чат-бота UniCRM</p>
        
        <div class="chat-area" id="chatArea">
            <div class="message bot-message">
                👋 Привет! Напиши что-нибудь боту...
            </div>
        </div>
        
        <textarea id="messageInput" rows="2" placeholder='Например: "Запишите на мойку завтра в 15:00"'></textarea>
        <button id="sendBtn" onclick="sendMessage()">📨 Отправить</button>
        
        <div id="status" class="status status-offline">🔄 Проверка подключения...</div>
    </div>

    <script>
        let lastReply = null;
        
        function addMessage(text, isUser) {
            const chatArea = document.getElementById('chatArea');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
            messageDiv.textContent = text;
            chatArea.appendChild(messageDiv);
            chatArea.scrollTop = chatArea.scrollHeight;
        }
        
        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const sendBtn = document.getElementById('sendBtn');
            const message = input.value.trim();
            
            if (!message) return;
            
            addMessage(message, true);
            input.value = '';
            sendBtn.disabled = true;
            sendBtn.textContent = '⏳ Отправка...';
            
            try {
                const response = await fetch('/send', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: message })
                });
                
                const data = await response.json();
                
                if (data.reply) {
                    addMessage(data.reply, false);
                } else {
                    addMessage('❌ Ошибка: бот не ответил', false);
                }
            } catch (err) {
                addMessage(`❌ Ошибка: ${err.message}`, false);
            } finally {
                sendBtn.disabled = false;
                sendBtn.textContent = '📨 Отправить';
            }
        }
        
        async function checkStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                const statusDiv = document.getElementById('status');
                
                if (data.bot_online) {
                    statusDiv.className = 'status status-online';
                    statusDiv.innerHTML = '✅ Бот работает';
                } else {
                    statusDiv.className = 'status status-offline';
                    statusDiv.innerHTML = '❌ Бот не запущен';
                }
            } catch (err) {
                console.error('Status check error:', err);
            }
        }
        
        // Ctrl+Enter для отправки
        document.getElementById('messageInput').addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') {
                sendMessage();
            }
        });
        
        setInterval(checkStatus, 5000);
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
    data = request.json
    user_message = data.get('message')
    
    try:
        resp = requests.post('http://localhost:5001/webhook/test_bot_token_123', 
                            json={"message": {"chat": {"id": 12345}, "text": user_message}}, 
                            timeout=10)
        
        if resp.status_code == 200:
            reply = resp.json().get('reply', 'Бот не ответил')
            return jsonify({'ok': True, 'reply': reply})
        else:
            return jsonify({'ok': False, 'error': 'Ошибка бота'}), 500
        
    except requests.exceptions.ConnectionError:
        return jsonify({'ok': False, 'error': 'Бот не запущен'}), 500
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/bot<token>/sendMessage', methods=['POST'])
def bot_send_message(token):
    data = request.json
    text = data.get('text')
    
    # Просто логируем в консоль, но не сохраняем
    print(f"[БОТ] -> {text}")
    
    return jsonify({"ok": True, "result": {"message_id": 1, "text": text}})

@app.route('/api/status')
def get_status():
    try:
        resp = requests.get('http://localhost:5001/', timeout=1)
        bot_online = resp.status_code == 200
    except:
        bot_online = False
    
    return jsonify({'bot_online': bot_online})

if __name__ == '__main__':
    print("=" * 60)
    print("🤖 MAX Эмулятор запущен!")
    print("📱 Открой в браузере: http://127.0.0.1:9000")
    print("=" * 60)
    app.run(port=9000, debug=True, use_reloader=False)