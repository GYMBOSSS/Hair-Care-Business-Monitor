from app import create_app, db
from app.models.client import Client
from app.models.service import Service
from app.models.appointment import Appointment

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)