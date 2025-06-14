"""
User management routes
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from sqlalchemy import or_

from src.models.database import db
from src.models.user import User, UserRole, UserPreference
from src.utils.auth import (
    get_current_user, require_permission, require_same_organization,
    format_error_response, format_success_response, paginate_query,
    extract_pagination_params, extract_search_params, audit_log
)
from src.utils.validators import validate_email, validate_password, validate_phone

users_bp = Blueprint('users', __name__)

@users_bp.route('', methods=['GET'])
@jwt_required()
@require_permission('manage_users')
@require_same_organization
def get_users(current_organization_id):
    """Get all users in organization"""
    try:
        page, per_page = extract_pagination_params(request.args)
        search, sort_by, sort_order = extract_search_params(request.args)
        role_filter = request.args.get('role')
        active_filter = request.args.get('active')
        
        # Build query
        query = User.query.filter_by(organization_id=current_organization_id)
        
        # Apply search filter
        if search:
            query = query.filter(
                or_(
                    User.first_name.ilike(f'%{search}%'),
                    User.last_name.ilike(f'%{search}%'),
                    User.email.ilike(f'%{search}%')
                )
            )
        
        # Apply role filter
        if role_filter:
            try:
                role_enum = UserRole(role_filter)
                query = query.filter_by(role=role_enum)
            except ValueError:
                pass
        
        # Apply active filter
        if active_filter is not None:
            is_active = active_filter.lower() in ['true', '1', 'yes']
            query = query.filter_by(is_active=is_active)
        
        # Apply sorting
        if hasattr(User, sort_by):
            if sort_order == 'asc':
                query = query.order_by(getattr(User, sort_by).asc())
            else:
                query = query.order_by(getattr(User, sort_by).desc())
        
        # Paginate results
        result = paginate_query(query, page, per_page)
        
        return jsonify(result), 200
        
    except Exception as e:
        current_app.logger.error(f"Get users error: {str(e)}")
        return format_error_response('Gebruikers ophalen gefaald', status_code=500)

@users_bp.route('/<user_id>', methods=['GET'])
@jwt_required()
@require_permission('manage_users')
@require_same_organization
def get_user(user_id, current_organization_id):
    """Get specific user"""
    try:
        user = User.query.filter_by(
            id=user_id, 
            organization_id=current_organization_id
        ).first()
        
        if not user:
            return format_error_response('Gebruiker niet gevonden', status_code=404)
        
        user_data = user.to_dict()
        user_data['organization'] = user.organization.to_dict()
        
        if user.user_preferences:
            user_data['preferences'] = user.user_preferences.to_dict()
        
        return jsonify({'user': user_data}), 200
        
    except Exception as e:
        current_app.logger.error(f"Get user error: {str(e)}")
        return format_error_response('Gebruiker ophalen gefaald', status_code=500)

@users_bp.route('', methods=['POST'])
@jwt_required()
@require_permission('manage_users')
@require_same_organization
@audit_log('users', 'INSERT')
def create_user(current_organization_id):
    """Create new user"""
    try:
        data = request.get_json()
        
        if not data:
            return format_error_response('Geen data ontvangen')
        
        # Validate required fields
        email = data.get('email', '').strip().lower()
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        role = data.get('role', 'technician')
        
        if not email:
            return format_error_response('Email is vereist')
        
        if not validate_email(email):
            return format_error_response('Ongeldig email adres')
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            return format_error_response('Email adres is al in gebruik')
        
        # Validate role
        try:
            role_enum = UserRole(role)
        except ValueError:
            return format_error_response('Ongeldige rol')
        
        # Validate phone if provided
        phone = data.get('phone', '').strip()
        if phone and not validate_phone(phone):
            return format_error_response('Ongeldig telefoonnummer')
        
        # Create user
        user = User(
            organization_id=current_organization_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role=role_enum,
            is_active=data.get('is_active', True),
            email_verified=data.get('email_verified', False)
        )
        
        # Set password if provided
        password = data.get('password')
        if password:
            if not validate_password(password):
                return format_error_response('Wachtwoord moet minimaal 8 karakters lang zijn')
            user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        return format_success_response(
            'Gebruiker succesvol aangemaakt',
            {'user': user.to_dict()},
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Create user error: {str(e)}")
        return format_error_response('Gebruiker aanmaken gefaald', status_code=500)

@users_bp.route('/<user_id>', methods=['PUT'])
@jwt_required()
@require_permission('manage_users')
@require_same_organization
@audit_log('users', 'UPDATE')
def update_user(user_id, current_organization_id):
    """Update user"""
    try:
        user = User.query.filter_by(
            id=user_id,
            organization_id=current_organization_id
        ).first()
        
        if not user:
            return format_error_response('Gebruiker niet gevonden', status_code=404)
        
        data = request.get_json()
        if not data:
            return format_error_response('Geen data ontvangen')
        
        # Store old values for audit
        old_values = user.to_dict()
        
        # Update fields
        if 'first_name' in data:
            user.first_name = data['first_name'].strip()
        
        if 'last_name' in data:
            user.last_name = data['last_name'].strip()
        
        if 'phone' in data:
            phone = data['phone'].strip()
            if phone and not validate_phone(phone):
                return format_error_response('Ongeldig telefoonnummer')
            user.phone = phone
        
        if 'role' in data:
            try:
                role_enum = UserRole(data['role'])
                user.role = role_enum
            except ValueError:
                return format_error_response('Ongeldige rol')
        
        if 'is_active' in data:
            user.is_active = bool(data['is_active'])
        
        if 'email_verified' in data:
            user.email_verified = bool(data['email_verified'])
        
        # Update password if provided
        if 'password' in data and data['password']:
            if not validate_password(data['password']):
                return format_error_response('Wachtwoord moet minimaal 8 karakters lang zijn')
            user.set_password(data['password'])
        
        db.session.commit()
        
        return format_success_response(
            'Gebruiker succesvol bijgewerkt',
            {'user': user.to_dict()}
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update user error: {str(e)}")
        return format_error_response('Gebruiker bijwerken gefaald', status_code=500)

@users_bp.route('/<user_id>', methods=['DELETE'])
@jwt_required()
@require_permission('manage_users')
@require_same_organization
@audit_log('users', 'DELETE')
def delete_user(user_id, current_organization_id):
    """Delete user (soft delete by deactivating)"""
    try:
        current_user = get_current_user()
        
        # Prevent self-deletion
        if str(current_user.id) == str(user_id):
            return format_error_response('Je kunt je eigen account niet verwijderen')
        
        user = User.query.filter_by(
            id=user_id,
            organization_id=current_organization_id
        ).first()
        
        if not user:
            return format_error_response('Gebruiker niet gevonden', status_code=404)
        
        # Soft delete by deactivating
        user.is_active = False
        db.session.commit()
        
        return format_success_response('Gebruiker succesvol gedeactiveerd')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Delete user error: {str(e)}")
        return format_error_response('Gebruiker verwijderen gefaald', status_code=500)

@users_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile"""
    try:
        user = get_current_user()
        
        if not user:
            return format_error_response('Gebruiker niet gevonden', status_code=404)
        
        user_data = user.to_dict()
        user_data['organization'] = user.organization.to_dict()
        
        if user.user_preferences:
            user_data['preferences'] = user.user_preferences.to_dict()
        
        return jsonify({'user': user_data}), 200
        
    except Exception as e:
        current_app.logger.error(f"Get profile error: {str(e)}")
        return format_error_response('Profiel ophalen gefaald', status_code=500)

@users_bp.route('/profile', methods=['PUT'])
@jwt_required()
@audit_log('users', 'UPDATE')
def update_profile():
    """Update current user profile"""
    try:
        user = get_current_user()
        
        if not user:
            return format_error_response('Gebruiker niet gevonden', status_code=404)
        
        data = request.get_json()
        if not data:
            return format_error_response('Geen data ontvangen')
        
        # Update allowed fields
        if 'first_name' in data:
            user.first_name = data['first_name'].strip()
        
        if 'last_name' in data:
            user.last_name = data['last_name'].strip()
        
        if 'phone' in data:
            phone = data['phone'].strip()
            if phone and not validate_phone(phone):
                return format_error_response('Ongeldig telefoonnummer')
            user.phone = phone
        
        db.session.commit()
        
        return format_success_response(
            'Profiel succesvol bijgewerkt',
            {'user': user.to_dict()}
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update profile error: {str(e)}")
        return format_error_response('Profiel bijwerken gefaald', status_code=500)

@users_bp.route('/preferences', methods=['GET'])
@jwt_required()
def get_preferences():
    """Get user preferences"""
    try:
        user = get_current_user()
        
        if not user:
            return format_error_response('Gebruiker niet gevonden', status_code=404)
        
        if not user.user_preferences:
            # Create default preferences
            preferences = UserPreference(user_id=user.id)
            db.session.add(preferences)
            db.session.commit()
        else:
            preferences = user.user_preferences
        
        return jsonify({'preferences': preferences.to_dict()}), 200
        
    except Exception as e:
        current_app.logger.error(f"Get preferences error: {str(e)}")
        return format_error_response('Voorkeuren ophalen gefaald', status_code=500)

@users_bp.route('/preferences', methods=['PUT'])
@jwt_required()
def update_preferences():
    """Update user preferences"""
    try:
        user = get_current_user()
        
        if not user:
            return format_error_response('Gebruiker niet gevonden', status_code=404)
        
        data = request.get_json()
        if not data:
            return format_error_response('Geen data ontvangen')
        
        # Get or create preferences
        if not user.user_preferences:
            preferences = UserPreference(user_id=user.id)
            db.session.add(preferences)
        else:
            preferences = user.user_preferences
        
        # Update preferences
        if 'dashboard_config' in data:
            preferences.dashboard_config = data['dashboard_config']
        
        if 'notification_settings' in data:
            preferences.notification_settings = data['notification_settings']
        
        if 'theme' in data:
            preferences.theme = data['theme']
        
        if 'language' in data:
            preferences.language = data['language']
        
        db.session.commit()
        
        return format_success_response(
            'Voorkeuren succesvol bijgewerkt',
            {'preferences': preferences.to_dict()}
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update preferences error: {str(e)}")
        return format_error_response('Voorkeuren bijwerken gefaald', status_code=500)

