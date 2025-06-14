"""
Organization model
"""
from src.models.database import db, BaseModel

class Organization(BaseModel):
    __tablename__ = 'organizations'
    
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(255))
    postal_code = db.Column(db.String(20))
    city = db.Column(db.String(100))
    country = db.Column(db.String(100), default='Nederland')
    phone = db.Column(db.String(50))
    email = db.Column(db.String(255))
    website = db.Column(db.String(255))
    kvk_number = db.Column(db.String(20))
    btw_number = db.Column(db.String(30))
    iban = db.Column(db.String(50))
    logo_url = db.Column(db.String(500))
    
    # Relationships
    users = db.relationship('User', backref='organization', lazy=True, cascade='all, delete-orphan')
    customers = db.relationship('Customer', backref='organization', lazy=True, cascade='all, delete-orphan')
    products = db.relationship('Product', backref='organization', lazy=True, cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='organization', lazy=True, cascade='all, delete-orphan')
    document_templates = db.relationship('DocumentTemplate', backref='organization', lazy=True, cascade='all, delete-orphan')
    generated_documents = db.relationship('GeneratedDocument', backref='organization', lazy=True, cascade='all, delete-orphan')
    system_settings = db.relationship('SystemSetting', backref='organization', lazy=True, cascade='all, delete-orphan')
    widget_configurations = db.relationship('WidgetConfiguration', backref='organization', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Organization {self.name}>'
    
    def to_dict(self, exclude=None):
        """Convert to dictionary with additional fields"""
        data = super().to_dict(exclude)
        data['user_count'] = len(self.users)
        data['customer_count'] = len(self.customers)
        data['product_count'] = len(self.products)
        return data

