# Gebruik een officiële Python runtime als base image
FROM python:3.11-slim

# Installeer Gunicorn en andere benodigdheden
RUN pip install gunicorn

# Zet de working directory in de container
WORKDIR /app

# Voeg de werkdirectory toe aan het PYTHONPATH zodat Python modules in deze map
# kan vinden wanneer de applicatie start.
ENV PYTHONPATH /app

# Kopieer de requirements en installeer ze
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopieer de rest van de applicatiecode
COPY . .

# Definieer de poort die de container zal exposen
EXPOSE 8080

# Start de applicatie met Gunicorn via de app factory
# Dit leest de $PORT variabele die Cloud Run aanlevert
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 0 "src.main:create_app()"

