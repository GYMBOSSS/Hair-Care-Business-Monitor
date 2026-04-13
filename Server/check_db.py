from app import create_app, db
from app.models.client import Client
from app.models.user import User
from app.models.business import Business

app = create_app()
with app.app_context():
    print("Клиенты:", Client.query.all())
    print("Пользователи:", User.query.all())
    print("Бизнесы:", Business.query.all())