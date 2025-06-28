import os
import sys
from datetime import timedelta

from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import database and models
from models.database import db
from models.organization import Organization
from models.user import User
from models.customer import Customer, CustomerAddress, CustomerContact
from models.product import Product, ProductCategory, ProductAttachment
from models.order import Order, OrderItem
from models.document import DocumentTemplate, GeneratedDocument
from models.system import SystemSetting, WidgetConfiguration, SheetsyncLog, AuditLog

# Import routes
from routes.auth import auth_bp
from routes.users import users_bp
from routes.customers import customers_bp
from routes.products import products_bp
from routes.orders import orders_bp
from routes.documents import documents_bp
from routes.dashboard import dashboard_bp
from routes.admin import admin_bp

def create_app(config_name='production'):
    """Application factory pattern - Railway optimized"""
    app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'railway-secret-key-change-in-production')
    
    # Database configuration - Railway provides DATABASE_URL automatically
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        # Handle postgres:// vs postgresql:// URL schemes
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        # Fallback to SQLite for local development
        app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 20,
        'pool_size': 5,
        'max_overflow': 10
    }
    
    # JWT Configuration
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', app.config['SECRET_KEY'])
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
    
    # Railway-specific configuration
    app.config['PORT'] = int(os.getenv('PORT', 8080))
    app.config['RAILWAY_ENVIRONMENT'] = os.getenv('RAILWAY_ENVIRONMENT', 'production')
    app.config['RAILWAY_PROJECT_ID'] = os.getenv('RAILWAY_PROJECT_ID')
    app.config['RAILWAY_SERVICE_ID'] = os.getenv('RAILWAY_SERVICE_ID')
    
    # Application Configuration
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', '/tmp/uploads')
    
    # Email Configuration (optional)
    app.config['SMTP_SERVER'] = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    app.config['SMTP_PORT'] = int(os.getenv('SMTP_PORT', '587'))
    app.config['SMTP_USERNAME'] = os.getenv('SMTP_USERNAME')
    app.config['SMTP_PASSWORD'] = os.getenv('SMTP_PASSWORD')
    app.config['FROM_EMAIL'] = os.getenv('FROM_EMAIL')
    
    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    jwt = JWTManager(app)
    
    # Enable CORS for all routes
    CORS(app, origins="*", supports_credentials=True)
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(customers_bp, url_prefix='/api/customers')
    app.register_blueprint(products_bp, url_prefix='/api/products')
    app.register_blueprint(orders_bp, url_prefix='/api/orders')
    app.register_blueprint(documents_bp, url_prefix='/api/documents')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    
    # Health check endpoint for Railway
    @app.route('/health')
    def health_check():
        """Health check endpoint for Railway load balancers"""
        try:
            # Test database connection
            db.session.execute('SELECT 1')
            return jsonify({
                'status': 'healthy',
                'database': 'connected',
                'version': '1.0.0',
                'environment': app.config.get('RAILWAY_ENVIRONMENT', 'unknown'),
                'service': app.config.get('RAILWAY_SERVICE_ID', 'unknown')
            }), 200
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'database': 'disconnected',
                'error': str(e),
                'environment': app.config.get('RAILWAY_ENVIRONMENT', 'unknown')
            }), 503
    
    # API info endpoint
    @app.route('/api')
    def api_info():
        """API information endpoint"""
        return jsonify({
            'name': 'Document Generator API',
            'version': '1.0.0',
            'description': 'REST API voor Document Generatie App - Railway Deployment',
            'environment': app.config.get('RAILWAY_ENVIRONMENT', 'unknown'),
            'endpoints': {
                'auth': '/api/auth',
                'users': '/api/users',
                'customers': '/api/customers',
                'products': '/api/products',
                'orders': '/api/orders',
                'documents': '/api/documents',
                'dashboard': '/api/dashboard',
                'admin': '/api/admin'
            }
        })
    
    # Railway-specific info endpoint
    @app.route('/railway')
    def railway_info():
        """Railway deployment information"""
        return jsonify({
            'platform': 'Railway',
            'project_id': app.config.get('RAILWAY_PROJECT_ID'),
            'service_id': app.config.get('RAILWAY_SERVICE_ID'),
            'environment': app.config.get('RAILWAY_ENVIRONMENT'),
            'port': app.config.get('PORT'),
            'database_connected': True if os.getenv('DATABASE_URL') else False
        })
    
    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'message': 'Token is verlopen'}), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'message': 'Ongeldig token'}), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({'message': 'Autorisatie token vereist'}), 401
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'message': 'Endpoint niet gevonden'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'message': 'Interne server fout'}), 500
    
    @app.errorhandler(413)
    def too_large(error):
        return jsonify({'message': 'Bestand te groot'}), 413
    
    # Frontend serving (for production)
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        """Serve frontend files"""
        static_folder_path = app.static_folder
        if static_folder_path is None:
            return jsonify({'message': 'Frontend niet geconfigureerd'}), 404

        if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
            return send_from_directory(static_folder_path, path)
        else:
            index_path = os.path.join(static_folder_path, 'index.html')
            if os.path.exists(index_path):
                return send_from_directory(static_folder_path, 'index.html')
            else:
                return jsonify({'message': 'Frontend niet gevonden'}), 404
    
    # Create database tables
    with app.app_context():
        try:
            db.create_all()
            print("✅ Database tabellen aangemaakt")
        except Exception as e:
            print(f"❌ Fout bij aanmaken database tabellen: {e}")
    
    return app

# Create app instance
app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    print(f"🚂 Starting Document Generator API on Railway")
    print(f"🔧 Port: {port}")
    print(f"🔧 Debug mode: {debug}")
    print(f"🗄️  Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print(f"🌍 Environment: {app.config.get('RAILWAY_ENVIRONMENT', 'unknown')}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)

