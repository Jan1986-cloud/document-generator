"""
Authentication and authorization utilities
"""
from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from src.models.user import User, UserRole
from src.models.system import AuditLog
from typing import Optional, List

def get_current_user() -> Optional[User]:
    """Get current authenticated user"""
    try:
        verify_jwt_in_request()
        current_user_data = get_jwt_identity()
        
        if not current_user_data or not isinstance(current_user_data, dict):
            return None
        
        user_id = current_user_data.get('user_id')
        if not user_id:
            return None
        
        user = User.query.get(user_id)
        return user if user and user.is_active else None
        
    except Exception:
        return None

def require_permission(permission: str):
    """Decorator to require specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            
            if not user:
                return jsonify({'message': 'Authenticatie vereist'}), 401
            
            if not user.has_permission(permission):
                return jsonify({'message': 'Onvoldoende rechten'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_role(roles: List[UserRole]):
    """Decorator to require specific role(s)"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            
            if not user:
                return jsonify({'message': 'Authenticatie vereist'}), 401
            
            if user.role not in roles:
                return jsonify({'message': 'Onvoldoende rechten'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_same_organization(f):
    """Decorator to ensure user can only access data from their organization"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        
        if not user:
            return jsonify({'message': 'Authenticatie vereist'}), 401
        
        # Add organization_id to kwargs for use in the route
        kwargs['current_organization_id'] = user.organization_id
        
        return f(*args, **kwargs)
    return decorated_function

def log_user_action(table_name: str, record_id: str, action: str, 
                   old_values: dict = None, new_values: dict = None):
    """Log user action for audit trail"""
    try:
        user = get_current_user()
        
        if user:
            AuditLog.log_action(
                table_name=table_name,
                record_id=record_id,
                action=action,
                old_values=old_values,
                new_values=new_values,
                user_id=user.id,
                organization_id=user.organization_id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
    except Exception as e:
        # Don't fail the main operation if logging fails
        print(f"Audit logging failed: {e}")

def audit_log(table_name: str, action: str):
    """Decorator to automatically log actions"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Execute the function first
            result = f(*args, **kwargs)
            
            # Try to extract record ID from result or kwargs
            record_id = None
            if isinstance(result, tuple) and len(result) >= 2:
                response_data = result[0]
                if hasattr(response_data, 'get_json'):
                    json_data = response_data.get_json()
                    if json_data and isinstance(json_data, dict):
                        record_id = json_data.get('id')
            
            # Log the action
            log_user_action(table_name, record_id, action)
            
            return result
        return decorated_function
    return decorator

def check_organization_access(user: User, organization_id: str) -> bool:
    """Check if user has access to specific organization"""
    if not user or not user.is_active:
        return False
    
    # Admin users can access any organization (for super admin functionality)
    if user.role == UserRole.ADMIN and user.organization.name == 'System':
        return True
    
    # Regular users can only access their own organization
    return str(user.organization_id) == str(organization_id)

def check_resource_access(user: User, resource_organization_id: str) -> bool:
    """Check if user has access to a specific resource"""
    return check_organization_access(user, resource_organization_id)

def get_user_dashboard_config(user: User) -> dict:
    """Get dashboard configuration for user based on role"""
    base_config = {
        'theme': 'light',
        'language': 'nl',
        'widgets': []
    }
    
    # Role-based widget configuration
    role_widgets = {
        UserRole.ADMIN: [
            'user_stats', 'system_health', 'recent_activity', 'organization_overview',
            'customer_stats', 'product_stats', 'order_stats', 'document_stats'
        ],
        UserRole.DIRECTOR: [
            'organization_overview', 'customer_stats', 'product_stats', 'order_stats',
            'document_stats', 'revenue_chart', 'recent_orders'
        ],
        UserRole.SALES: [
            'customer_stats', 'order_stats', 'recent_orders', 'my_customers',
            'product_catalog', 'sales_targets'
        ],
        UserRole.TECHNICIAN: [
            'my_orders', 'recent_orders', 'customer_info', 'product_catalog',
            'work_schedule'
        ],
        UserRole.ACCOUNTANT: [
            'financial_overview', 'invoice_stats', 'payment_status', 'revenue_chart',
            'recent_documents'
        ]
    }
    
    base_config['widgets'] = role_widgets.get(user.role, [])
    
    # Merge with user preferences if available
    if user.user_preferences and user.user_preferences.dashboard_config:
        base_config.update(user.user_preferences.dashboard_config)
    
    return base_config

def format_error_response(message: str, details: dict = None, status_code: int = 400):
    """Format standardized error response"""
    response = {'message': message}
    
    if details:
        response['details'] = details
    
    return jsonify(response), status_code

def format_success_response(message: str, data: dict = None, status_code: int = 200):
    """Format standardized success response"""
    response = {'message': message}
    
    if data:
        response.update(data)
    
    return jsonify(response), status_code

def paginate_query(query, page: int = 1, per_page: int = 20, max_per_page: int = 100):
    """Paginate SQLAlchemy query"""
    # Validate pagination parameters
    page = max(1, page)
    per_page = min(max_per_page, max(1, per_page))
    
    # Execute pagination
    paginated = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    return {
        'items': [item.to_dict() for item in paginated.items],
        'pagination': {
            'page': paginated.page,
            'per_page': paginated.per_page,
            'total': paginated.total,
            'pages': paginated.pages,
            'has_prev': paginated.has_prev,
            'has_next': paginated.has_next,
            'prev_num': paginated.prev_num,
            'next_num': paginated.next_num
        }
    }

def extract_pagination_params(request_args):
    """Extract pagination parameters from request"""
    try:
        page = int(request_args.get('page', 1))
        per_page = int(request_args.get('per_page', 20))
        return page, per_page
    except (ValueError, TypeError):
        return 1, 20

def extract_search_params(request_args):
    """Extract search parameters from request"""
    search = request_args.get('search', '').strip()
    sort_by = request_args.get('sort_by', 'created_at')
    sort_order = request_args.get('sort_order', 'desc').lower()
    
    if sort_order not in ['asc', 'desc']:
        sort_order = 'desc'
    
    return search, sort_by, sort_order

