# Gebruik een officiële Python runtime als base image
FROM python:3.11-slim

# Zet de working directory in de container
WORKDIR /app

# Voeg de werkdirectory toe aan het PYTHONPATH.
# Dit is cruciaal voor het vinden van de 'src' module.
ENV PYTHONPATH /app

# Kopieer de requirements en installeer ze eerst om gebruik te maken van Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopieer de rest van de applicatiecode
COPY . .

# Definieer de poort die de container zal exposen
EXPOSE 8080

# Start de applicatie met Gunicorn via de correcte app-instantie in app.py
# Dit is de definitieve, correcte regel
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 0 "app:app"
