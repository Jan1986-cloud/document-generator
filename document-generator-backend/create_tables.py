import os
from src.main import create_app
from src.models.database import db

# Maak een app-instantie aan met de 'testing' configuratie
app = create_app('testing')

# Werk binnen de applicatie-context
with app.app_context():
    print("Dropping all tables...")
    db.drop_all()  # Optioneel: begin met een schone lei
    print("Creating all tables...")
    db.create_all()
    print("Tables created successfully.")