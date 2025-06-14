"""
Dashboard routes
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from sqlalchemy import func
from datetime import datetime, timedelta

from src.models.database import db
from src.models.customer import Customer
from src.models.product import Product
from src.models.order import Order, OrderStatus
from src.models.document import GeneratedDocument
from src.models.user import User
from src.utils.auth import (
    get_current_user, require_permission, require_same_organization,
    format_error_response, format_success_response
)

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/stats', methods=['GET'])
@jwt_required()
@require_permission('view_dashboard')
@require_same_organization
def get_dashboard_stats(current_organization_id):
    """Get dashboard statistics"""
    try:
        current_user = get_current_user()
        
        # Basic counts
        customer_count = Customer.query.filter_by(
            organization_id=current_organization_id,
            is_active=True
        ).count()
        
        product_count = Product.query.filter_by(
            organization_id=current_organization_id,
            is_active=True
        ).count()
        
        order_count = Order.query.filter_by(
            organization_id=current_organization_id
        ).count()
        
        document_count = GeneratedDocument.query.filter_by(
            organization_id=current_organization_id
        ).count()
        
        # Recent orders
        recent_orders = Order.query.filter_by(
            organization_id=current_organization_id
        ).order_by(Order.created_at.desc()).limit(5).all()
        
        # Order status distribution
        order_status_stats = db.session.query(
            Order.status,
            func.count(Order.id).label('count')
        ).filter_by(
            organization_id=current_organization_id
        ).group_by(Order.status).all()
        
        # Monthly revenue (last 12 months)
        twelve_months_ago = datetime.now() - timedelta(days=365)
        monthly_revenue = db.session.query(
            func.date_trunc('month', Order.order_date).label('month'),
            func.sum(Order.total_incl_btw).label('revenue')
        ).filter(
            Order.organization_id == current_organization_id,
            Order.order_date >= twelve_months_ago.date()
        ).group_by(
            func.date_trunc('month', Order.order_date)
        ).order_by('month').all()
        
        # User-specific stats based on role
        user_stats = {}
        if current_user.role.value in ['sales', 'technician']:
            # My orders
            my_orders = Order.query.filter_by(
                organization_id=current_organization_id,
                assigned_to=current_user.id
            ).count()
            user_stats['my_orders'] = my_orders
            
            # My recent orders
            my_recent_orders = Order.query.filter_by(
                organization_id=current_organization_id,
                assigned_to=current_user.id
            ).order_by(Order.created_at.desc()).limit(5).all()
            user_stats['my_recent_orders'] = [order.to_dict() for order in my_recent_orders]
        
        stats = {
            'overview': {
                'customers': customer_count,
                'products': product_count,
                'orders': order_count,
                'documents': document_count
            },
            'recent_orders': [order.to_dict() for order in recent_orders],
            'order_status_distribution': [
                {'status': status.value, 'count': count} 
                for status, count in order_status_stats
            ],
            'monthly_revenue': [
                {
                    'month': month.strftime('%Y-%m') if month else None,
                    'revenue': float(revenue) if revenue else 0
                }
                for month, revenue in monthly_revenue
            ],
            'user_stats': user_stats
        }
        
        return jsonify({'stats': stats}), 200
        
    except Exception as e:
        current_app.logger.error(f"Get dashboard stats error: {str(e)}")
        return format_error_response('Dashboard statistieken ophalen gefaald', status_code=500)

@dashboard_bp.route('/widgets', methods=['GET'])
@jwt_required()
@require_permission('view_dashboard')
@require_same_organization
def get_dashboard_widgets(current_organization_id):
    """Get dashboard widget configuration"""
    try:
        current_user = get_current_user()
        
        # Get widget configuration based on user role
        from src.utils.auth import get_user_dashboard_config
        dashboard_config = get_user_dashboard_config(current_user)
        
        return jsonify({'widgets': dashboard_config}), 200
        
    except Exception as e:
        current_app.logger.error(f"Get dashboard widgets error: {str(e)}")
        return format_error_response('Dashboard widgets ophalen gefaald', status_code=500)

@dashboard_bp.route('/widgets', methods=['PUT'])
@jwt_required()
@require_permission('view_dashboard')
def update_dashboard_widgets():
    """Update user dashboard widget configuration"""
    try:
        current_user = get_current_user()
        data = request.get_json()
        
        if not data:
            return format_error_response('Geen data ontvangen')
        
        # Update user preferences
        if not current_user.user_preferences:
            from src.models.user import UserPreference
            preferences = UserPreference(user_id=current_user.id)
            db.session.add(preferences)
        else:
            preferences = current_user.user_preferences
        
        # Update dashboard config
        if 'widgets' in data:
            if not preferences.dashboard_config:
                preferences.dashboard_config = {}
            preferences.dashboard_config['widgets'] = data['widgets']
        
        if 'layout' in data:
            if not preferences.dashboard_config:
                preferences.dashboard_config = {}
            preferences.dashboard_config['layout'] = data['layout']
        
        db.session.commit()
        
        return format_success_response('Dashboard configuratie bijgewerkt')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update dashboard widgets error: {str(e)}")
        return format_error_response('Dashboard configuratie bijwerken gefaald', status_code=500)

@dashboard_bp.route('/activity', methods=['GET'])
@jwt_required()
@require_permission('view_dashboard')
@require_same_organization
def get_recent_activity(current_organization_id):
    """Get recent activity feed"""
    try:
        # Get recent audit log entries
        from src.models.system import AuditLog
        
        recent_activity = AuditLog.query.filter_by(
            organization_id=current_organization_id
        ).order_by(AuditLog.created_at.desc()).limit(20).all()
        
        activity_data = [activity.to_dict() for activity in recent_activity]
        
        return jsonify({'activity': activity_data}), 200
        
    except Exception as e:
        current_app.logger.error(f"Get recent activity error: {str(e)}")
        return format_error_response('Recente activiteit ophalen gefaald', status_code=500)

