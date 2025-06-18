from src.main import create_app

app = create_app()

if __name__ == '__main__':
    # Gebruik Gunicorn of een andere WSGI server in productie
    # Deze run is alleen voor lokaal debuggen
    app.run(host='0.0.0.0', port=8080)
