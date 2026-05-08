from flask import render_template, request, redirect, url_for, flash, Blueprint
from flask_login import login_required, current_user
from app import db
from app.models.business import Business

bot_bp = Blueprint('bot', __name__)

@bot_bp.route('/business/bot-settings', methods=['GET', 'POST'])
@login_required
def bot_settings():
    # Только владелец бизнеса
    if current_user.role != 'owner':
        flash('Доступ запрещён', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Если нет бизнеса — перенаправляем на создание
    if not current_user.business_id:
        flash('Сначала создайте бизнес', 'warning')
        return redirect(url_for('auth.create_business'))
    
    business = Business.query.get(current_user.business_id)
    
    if request.method == 'POST':
        bot_token = request.form.get('bot_token')
        
        # Сохраняем токен
        business.bot_token = bot_token
        db.session.commit()
        
        flash('Токен бота сохранён!', 'success')
        return redirect(url_for('bot.bot_settings'))
    
    return render_template('business/bot_settings.html', business=business)