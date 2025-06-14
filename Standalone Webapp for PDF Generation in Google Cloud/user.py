"""
User models
"""
from src.models.database import db, BaseModel
from sqlalchemy.dialects.postgresql import UUID
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token
import enum

class UserRole(enum.Enum):
    ADMIN = 'admin'
    DIRECTOR = 'director'
    SALES = 'sales'
    TECHNICIAN = 'technician'
    ACCOUNTANT = 'accountant'

class User(BaseModel):
    __tablename__ = 'users'
    
    organization_id = db.Column(UUID(as_uuid=True), db.ForeignKey('organizations.id'), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255))
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    phone = db.Column(db.String(50))
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.TECHNICIAN)
    is_active = db.Column(db.Boolean, default=True)
    email_verified = db.Column(db.Boolean, default=False)
    google_id = db.Column(db.String(255), unique=True, index=True)
    last_login = db.Column(db.DateTime(timezone=True))
    
    # Relationships
    user_sessions = db.relationship('UserSession', backref='user', lazy=True, cascade='all, delete-orphan')
    user_preferences = db.relationship('UserPreference', backref='user', uselist=False, cascade='all, delete-orphan')
    created_customers = db.relationship('Customer', foreign_keys='Customer.created_by', backref='creator', lazy=True)
    created_products = db.relationship('Product', foreign_keys='Product.created_by', backref='creator', lazy=True)
    created_orders = db.relationship('Order', foreign_keys='Order.created_by', backref='creator', lazy=True)
    assigned_orders = db.relationship('Order', foreign_keys='Order.assigned_to', backref='assignee', lazy=True)
    created_documents = db.relationship('GeneratedDocument', foreign_keys='GeneratedDocument.created_by', backref='creator', lazy=True)
    created_templates = db.relationship('DocumentTemplate', foreign_keys='DocumentTemplate.created_by', backref='creator', lazy=True)
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def generate_tokens(self):
        """Generate JWT tokens"""
        identity = {
            'user_id': str(self.id),
            'email': self.email,
            'role': self.role.value,
            'organization_id': str(self.organization_id)
        }
        
        access_token = create_access_token(identity=identity)
        refresh_token = create_refresh_token(identity=identity)
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer'
        }
    
    @property
    def full_name(self):
        """Get full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.email
    
    def to_dict(self, exclude=None):
        """Convert to dictionary"""
        exclude = exclude or ['password_hash']
        data = super().to_dict(exclude)
        data['role'] = self.role.value
        data['full_name'] = self.full_name
        return data
    
    def has_permission(self, permission):
        """Check if user has specific permission"""
        role_permissions = {
            UserRole.ADMIN: ['*'],  # All permissions
            UserRole.DIRECTOR: [
                'view_dashboard', 'view_reports', 'manage_users', 'manage_customers',
                'manage_products', 'manage_orders', 'generate_documents', 'view_settings'
            ],
            UserRole.SALES: [
                'view_dashboard', 'manage_customers', 'manage_products', 'manage_orders',
                'generate_documents'
            ],
            UserRole.TECHNICIAN: [
                'view_dashboard', 'view_customers', 'view_products', 'manage_orders',
                'generate_documents'
            ],
            UserRole.ACCOUNTANT: [
                'view_dashboard', 'view_reports', 'view_customers', 'view_products',
                'view_orders', 'generate_documents'
            ]
        }
        
        permissions = role_permissions.get(self.role, [])
        return '*' in permissions or permission in permissions

class UserSession(BaseModel):
    __tablename__ = 'user_sessions'
    
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    token_hash = db.Column(db.String(255), nullable=False, index=True)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    ip_address = db.Column(db.String(45))  # IPv6 compatible
    user_agent = db.Column(db.Text)
    
    def __repr__(self):
        return f'<UserSession {self.user_id}>'

class UserPreference(BaseModel):
    __tablename__ = 'user_preferences'
    
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    dashboard_config = db.Column(db.JSON, default=dict)
    notification_settings = db.Column(db.JSON, default=dict)
    theme = db.Column(db.String(20), default='light')
    language = db.Column(db.String(10), default='nl')
    
    def __repr__(self):
        return f'<UserPreference {self.user_id}>'

