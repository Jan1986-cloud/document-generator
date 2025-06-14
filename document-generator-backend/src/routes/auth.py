"""
Authentication routes
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required, 
    get_jwt_identity, get_jwt
)
from werkzeug.security import check_password_hash
from datetime import datetime, timezone
import uuid

from src.models.database import db
from src.models.user import User, UserSession
from src.models.organization import Organization
from src.utils.validators import validate_email, validate_password
from src.utils.auth import get_current_user, require_permission

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login with email and password"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'message': 'Geen data ontvangen'}), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'message': 'Email en wachtwoord zijn vereist'}), 400
        
        if not validate_email(email):
            return jsonify({'message': 'Ongeldig email adres'}), 400
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            return jsonify({'message': 'Ongeldige inloggegevens'}), 401
        
        if not user.is_active:
            return jsonify({'message': 'Account is gedeactiveerd'}), 401
        
        # Update last login
        user.last_login = datetime.now(timezone.utc)
        
        # Generate tokens
        tokens = user.generate_tokens()
        
        # Create session record
        session = UserSession(
            user_id=user.id,
            token_hash=get_jwt()['jti'] if get_jwt() else str(uuid.uuid4()),
            expires_at=datetime.now(timezone.utc).replace(hour=23, minute=59, second=59),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(session)
        db.session.commit()
        
        return jsonify({
            'message': 'Succesvol ingelogd',
            'user': user.to_dict(),
            'tokens': tokens
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Login error: {str(e)}")
        return jsonify({'message': 'Inloggen gefaald'}), 500

@auth_bp.route('/register', methods=['POST'])
def register():
    """User registration"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'message': 'Geen data ontvangen'}), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        organization_name = data.get('organization_name', '').strip()
        
        # Validation
        if not email or not password:
            return jsonify({'message': 'Email en wachtwoord zijn vereist'}), 400
        
        if not validate_email(email):
            return jsonify({'message': 'Ongeldig email adres'}), 400
        
        if not validate_password(password):
            return jsonify({'message': 'Wachtwoord moet minimaal 8 karakters lang zijn'}), 400
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            return jsonify({'message': 'Email adres is al in gebruik'}), 409
        
        # Create or find organization
        if organization_name:
            organization = Organization.query.filter_by(name=organization_name).first()
            if not organization:
                organization = Organization(name=organization_name)
                db.session.add(organization)
                db.session.flush()  # Get ID without committing
        else:
            # Default organization for demo
            organization = Organization.query.first()
            if not organization:
                organization = Organization(name='Demo Bedrijf')
                db.session.add(organization)
                db.session.flush()
        
        # Create user
        user = User(
            organization_id=organization.id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role='admin' if not organization.users else 'technician',  # First user is admin
            is_active=True,
            email_verified=False
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'Account succesvol aangemaakt',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Registration error: {str(e)}")
        return jsonify({'message': 'Registratie gefaald'}), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    try:
        current_user_data = get_jwt_identity()
        user = User.query.get(current_user_data['user_id'])
        
        if not user or not user.is_active:
            return jsonify({'message': 'Gebruiker niet gevonden of gedeactiveerd'}), 401
        
        # Generate new access token
        tokens = user.generate_tokens()
        
        return jsonify({
            'message': 'Token vernieuwd',
            'tokens': tokens
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Token refresh error: {str(e)}")
        return jsonify({'message': 'Token vernieuwen gefaald'}), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """User logout"""
    try:
        jti = get_jwt()['jti']
        
        # Remove session
        session = UserSession.query.filter_by(token_hash=jti).first()
        if session:
            db.session.delete(session)
            db.session.commit()
        
        return jsonify({'message': 'Succesvol uitgelogd'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Logout error: {str(e)}")
        return jsonify({'message': 'Uitloggen gefaald'}), 500

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user_info():
    """Get current user information"""
    try:
        user = get_current_user()
        
        if not user:
            return jsonify({'message': 'Gebruiker niet gevonden'}), 404
        
        return jsonify({
            'user': user.to_dict(),
            'organization': user.organization.to_dict(),
            'permissions': get_user_permissions(user)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get current user error: {str(e)}")
        return jsonify({'message': 'Gebruiker ophalen gefaald'}), 500

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password"""
    try:
        user = get_current_user()
        data = request.get_json()
        
        if not data:
            return jsonify({'message': 'Geen data ontvangen'}), 400
        
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        
        if not current_password or not new_password:
            return jsonify({'message': 'Huidig en nieuw wachtwoord zijn vereist'}), 400
        
        if not user.check_password(current_password):
            return jsonify({'message': 'Huidig wachtwoord is onjuist'}), 400
        
        if not validate_password(new_password):
            return jsonify({'message': 'Nieuw wachtwoord moet minimaal 8 karakters lang zijn'}), 400
        
        user.set_password(new_password)
        db.session.commit()
        
        return jsonify({'message': 'Wachtwoord succesvol gewijzigd'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Change password error: {str(e)}")
        return jsonify({'message': 'Wachtwoord wijzigen gefaald'}), 500

@auth_bp.route('/google/login', methods=['POST'])
def google_login():
    """Google OAuth login"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'message': 'Geen data ontvangen'}), 400
        
        google_token = data.get('token')
        
        if not google_token:
            return jsonify({'message': 'Google token is vereist'}), 400
        
        # Verify Google token (implement Google OAuth verification)
        # This is a placeholder - implement actual Google token verification
        google_user_info = verify_google_token(google_token)
        
        if not google_user_info:
            return jsonify({'message': 'Ongeldig Google token'}), 401
        
        email = google_user_info.get('email')
        google_id = google_user_info.get('sub')
        first_name = google_user_info.get('given_name', '')
        last_name = google_user_info.get('family_name', '')
        
        # Find or create user
        user = User.query.filter_by(email=email).first()
        
        if not user:
            # Create new user
            organization = Organization.query.first()  # Default organization
            if not organization:
                organization = Organization(name='Demo Bedrijf')
                db.session.add(organization)
                db.session.flush()
            
            user = User(
                organization_id=organization.id,
                email=email,
                first_name=first_name,
                last_name=last_name,
                google_id=google_id,
                is_active=True,
                email_verified=True
            )
            db.session.add(user)
        else:
            # Update Google ID if not set
            if not user.google_id:
                user.google_id = google_id
        
        user.last_login = datetime.now(timezone.utc)
        db.session.commit()
        
        # Generate tokens
        tokens = user.generate_tokens()
        
        return jsonify({
            'message': 'Succesvol ingelogd met Google',
            'user': user.to_dict(),
            'tokens': tokens
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Google login error: {str(e)}")
        return jsonify({'message': 'Google login gefaald'}), 500

def verify_google_token(token):
    """Verify Google OAuth token"""
    # Placeholder for Google token verification
    # Implement actual Google OAuth token verification here
    return None

def get_user_permissions(user):
    """Get user permissions based on role"""
    role_permissions = {
        'admin': ['*'],
        'director': [
            'view_dashboard', 'view_reports', 'manage_users', 'manage_customers',
            'manage_products', 'manage_orders', 'generate_documents', 'view_settings'
        ],
        'sales': [
            'view_dashboard', 'manage_customers', 'manage_products', 'manage_orders',
            'generate_documents'
        ],
        'technician': [
            'view_dashboard', 'view_customers', 'view_products', 'manage_orders',
            'generate_documents'
        ],
        'accountant': [
            'view_dashboard', 'view_reports', 'view_customers', 'view_products',
            'view_orders', 'generate_documents'
        ]
    }
    
    return role_permissions.get(user.role.value, [])

