# Gebruik een officiële Python runtime als base image
FROM python:3.11-slim

# Zet de working directory in de container
WORKDIR /app

# Voeg de werkdirectory toe aan het PYTHONPATH.
ENV PYTHONPATH /app

# Kopieer en installeer dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopieer de rest van de applicatiecode
COPY . .

# Definieer de poort die de container zal exposen
EXPOSE 8080

# Start de applicatie met Gunicorn
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 0 "app:app"
