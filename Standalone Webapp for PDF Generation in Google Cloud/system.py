"""
System models
"""
from src.models.database import db, BaseModel
from sqlalchemy.dialects.postgresql import UUID
from src.models.user import UserRole

class SystemSetting(BaseModel):
    __tablename__ = 'system_settings'
    
    organization_id = db.Column(UUID(as_uuid=True), db.ForeignKey('organizations.id'), nullable=False)
    setting_key = db.Column(db.String(100), nullable=False)
    setting_value = db.Column(db.Text)
    setting_type = db.Column(db.String(50), default='string')
    description = db.Column(db.Text)
    
    __table_args__ = (
        db.UniqueConstraint('organization_id', 'setting_key', name='uq_org_setting_key'),
    )
    
    def __repr__(self):
        return f'<SystemSetting {self.setting_key}>'
    
    def get_value(self):
        """Get typed value"""
        if not self.setting_value:
            return None
        
        if self.setting_type == 'integer':
            return int(self.setting_value)
        elif self.setting_type == 'decimal':
            from decimal import Decimal
            return Decimal(self.setting_value)
        elif self.setting_type == 'boolean':
            return self.setting_value.lower() in ('true', '1', 'yes')
        elif self.setting_type == 'json':
            import json
            return json.loads(self.setting_value)
        else:
            return self.setting_value
    
    def set_value(self, value):
        """Set typed value"""
        if self.setting_type == 'json':
            import json
            self.setting_value = json.dumps(value)
        else:
            self.setting_value = str(value)
    
    @classmethod
    def get_setting(cls, organization_id, key, default=None):
        """Get setting value"""
        setting = cls.query.filter_by(organization_id=organization_id, setting_key=key).first()
        return setting.get_value() if setting else default
    
    @classmethod
    def set_setting(cls, organization_id, key, value, setting_type='string', description=None):
        """Set setting value"""
        setting = cls.query.filter_by(organization_id=organization_id, setting_key=key).first()
        if not setting:
            setting = cls(
                organization_id=organization_id,
                setting_key=key,
                setting_type=setting_type,
                description=description
            )
            db.session.add(setting)
        
        setting.set_value(value)
        if description:
            setting.description = description
        
        return setting

class WidgetConfiguration(BaseModel):
    __tablename__ = 'widget_configurations'
    
    organization_id = db.Column(UUID(as_uuid=True), db.ForeignKey('organizations.id'), nullable=False)
    widget_name = db.Column(db.String(100), nullable=False)
    widget_config = db.Column(db.JSON, default=dict)
    roles = db.Column(db.Text, default='[]')  # JSON array for SQLite compatibility
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<WidgetConfiguration {self.widget_name}>'
    
    def is_visible_for_role(self, role):
        """Check if widget is visible for given role"""
        if not self.is_active:
            return False
        if not self.roles:
            return True
        return role in self.roles
    
    def to_dict(self, exclude=None):
        """Convert to dictionary"""
        data = super().to_dict(exclude)
        data['roles'] = [role.value for role in self.roles] if self.roles else []
        return data

class SheetsyncLog(BaseModel):
    __tablename__ = 'sheets_sync_log'
    
    organization_id = db.Column(UUID(as_uuid=True), db.ForeignKey('organizations.id'), nullable=False)
    sheet_id = db.Column(db.String(255), nullable=False)
    sheet_name = db.Column(db.String(255))
    sync_type = db.Column(db.String(50), nullable=False)  # import, export
    sync_status = db.Column(db.String(50), nullable=False)  # success, error, in_progress
    records_processed = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text)
    started_at = db.Column(db.DateTime(timezone=True), default=lambda: db.func.now())
    completed_at = db.Column(db.DateTime(timezone=True))
    
    def __repr__(self):
        return f'<SheetsyncLog {self.sheet_name} {self.sync_type}>'
    
    def to_dict(self, exclude=None):
        """Convert to dictionary"""
        data = super().to_dict(exclude)
        if self.started_at and self.completed_at:
            duration = (self.completed_at - self.started_at).total_seconds()
            data['duration_seconds'] = duration
        return data

class AuditLog(BaseModel):
    __tablename__ = 'audit_log'
    
    organization_id = db.Column(UUID(as_uuid=True), db.ForeignKey('organizations.id'))
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    table_name = db.Column(db.String(100), nullable=False)
    record_id = db.Column(UUID(as_uuid=True))
    action = db.Column(db.String(20), nullable=False)  # INSERT, UPDATE, DELETE
    old_values = db.Column(db.JSON)
    new_values = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))  # IPv6 compatible
    user_agent = db.Column(db.Text)
    
    __table_args__ = (
        db.CheckConstraint("action IN ('INSERT', 'UPDATE', 'DELETE')", name='check_audit_action'),
    )
    
    def __repr__(self):
        return f'<AuditLog {self.table_name} {self.action}>'
    
    @classmethod
    def log_action(cls, table_name, record_id, action, old_values=None, new_values=None, 
                   user_id=None, organization_id=None, ip_address=None, user_agent=None):
        """Log an audit action"""
        log_entry = cls(
            organization_id=organization_id,
            user_id=user_id,
            table_name=table_name,
            record_id=record_id,
            action=action,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(log_entry)
        return log_entry
    
    def to_dict(self, exclude=None):
        """Convert to dictionary"""
        data = super().to_dict(exclude)
        data['user_name'] = self.user.full_name if self.user else 'System'
        return data

