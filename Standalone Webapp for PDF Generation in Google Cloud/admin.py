"""
Admin routes
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required

from src.models.database import db
from src.models.system import SystemSetting, WidgetConfiguration, SheetsyncLog, AuditLog
from src.models.organization import Organization
from src.utils.auth import (
    get_current_user, require_permission, require_same_organization,
    format_error_response, format_success_response, paginate_query,
    extract_pagination_params
)

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/settings', methods=['GET'])
@jwt_required()
@require_permission('view_settings')
@require_same_organization
def get_settings(current_organization_id):
    """Get system settings"""
    try:
        settings = SystemSetting.query.filter_by(
            organization_id=current_organization_id
        ).all()
        
        settings_dict = {}
        for setting in settings:
            settings_dict[setting.setting_key] = {
                'value': setting.get_value(),
                'type': setting.setting_type,
                'description': setting.description
            }
        
        return jsonify({'settings': settings_dict}), 200
        
    except Exception as e:
        current_app.logger.error(f"Get settings error: {str(e)}")
        return format_error_response('Instellingen ophalen gefaald', status_code=500)

@admin_bp.route('/settings', methods=['PUT'])
@jwt_required()
@require_permission('manage_settings')
@require_same_organization
def update_settings(current_organization_id):
    """Update system settings"""
    try:
        data = request.get_json()
        
        if not data:
            return format_error_response('Geen data ontvangen')
        
        for key, value in data.items():
            SystemSetting.set_setting(
                organization_id=current_organization_id,
                key=key,
                value=value
            )
        
        db.session.commit()
        
        return format_success_response('Instellingen bijgewerkt')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update settings error: {str(e)}")
        return format_error_response('Instellingen bijwerken gefaald', status_code=500)

@admin_bp.route('/widgets', methods=['GET'])
@jwt_required()
@require_permission('view_settings')
@require_same_organization
def get_widget_configurations(current_organization_id):
    """Get widget configurations"""
    try:
        widgets = WidgetConfiguration.query.filter_by(
            organization_id=current_organization_id
        ).order_by(WidgetConfiguration.sort_order).all()
        
        widgets_data = [widget.to_dict() for widget in widgets]
        
        return jsonify({'widgets': widgets_data}), 200
        
    except Exception as e:
        current_app.logger.error(f"Get widget configurations error: {str(e)}")
        return format_error_response('Widget configuraties ophalen gefaald', status_code=500)

@admin_bp.route('/sync-logs', methods=['GET'])
@jwt_required()
@require_permission('view_settings')
@require_same_organization
def get_sync_logs(current_organization_id):
    """Get Google Sheets sync logs"""
    try:
        page, per_page = extract_pagination_params(request.args)
        
        query = SheetsyncLog.query.filter_by(
            organization_id=current_organization_id
        ).order_by(SheetsyncLog.created_at.desc())
        
        result = paginate_query(query, page, per_page)
        
        return jsonify(result), 200
        
    except Exception as e:
        current_app.logger.error(f"Get sync logs error: {str(e)}")
        return format_error_response('Sync logs ophalen gefaald', status_code=500)

@admin_bp.route('/audit-logs', methods=['GET'])
@jwt_required()
@require_permission('view_settings')
@require_same_organization
def get_audit_logs(current_organization_id):
    """Get audit logs"""
    try:
        page, per_page = extract_pagination_params(request.args)
        
        query = AuditLog.query.filter_by(
            organization_id=current_organization_id
        ).order_by(AuditLog.created_at.desc())
        
        result = paginate_query(query, page, per_page)
        
        return jsonify(result), 200
        
    except Exception as e:
        current_app.logger.error(f"Get audit logs error: {str(e)}")
        return format_error_response('Audit logs ophalen gefaald', status_code=500)

@admin_bp.route('/organization', methods=['GET'])
@jwt_required()
@require_permission('view_settings')
@require_same_organization
def get_organization(current_organization_id):
    """Get organization details"""
    try:
        organization = Organization.query.get(current_organization_id)
        
        if not organization:
            return format_error_response('Organisatie niet gevonden', status_code=404)
        
        return jsonify({'organization': organization.to_dict()}), 200
        
    except Exception as e:
        current_app.logger.error(f"Get organization error: {str(e)}")
        return format_error_response('Organisatie ophalen gefaald', status_code=500)

@admin_bp.route('/organization', methods=['PUT'])
@jwt_required()
@require_permission('manage_settings')
@require_same_organization
def update_organization(current_organization_id):
    """Update organization details"""
    try:
        organization = Organization.query.get(current_organization_id)
        
        if not organization:
            return format_error_response('Organisatie niet gevonden', status_code=404)
        
        data = request.get_json()
        if not data:
            return format_error_response('Geen data ontvangen')
        
        # Update organization fields
        updatable_fields = [
            'name', 'address', 'postal_code', 'city', 'country',
            'phone', 'email', 'website', 'kvk_number', 'btw_number',
            'iban', 'logo_url'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(organization, field, data[field])
        
        db.session.commit()
        
        return format_success_response(
            'Organisatie bijgewerkt',
            {'organization': organization.to_dict()}
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update organization error: {str(e)}")
        return format_error_response('Organisatie bijwerken gefaald', status_code=500)

@admin_bp.route('/sync/trigger', methods=['POST'])
@jwt_required()
@require_permission('manage_settings')
@require_same_organization
def trigger_sync(current_organization_id):
    """Trigger Google Sheets synchronization"""
    try:
        data = request.get_json()
        
        if not data:
            return format_error_response('Geen data ontvangen')
        
        # TODO: Implement Google Sheets sync trigger
        return format_error_response('Google Sheets synchronisatie nog niet geïmplementeerd', status_code=501)
        
    except Exception as e:
        current_app.logger.error(f"Trigger sync error: {str(e)}")
        return format_error_response('Synchronisatie starten gefaald', status_code=500)

