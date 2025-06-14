"""
Customer models
"""
from src.models.database import db, BaseModel
from sqlalchemy.dialects.postgresql import UUID

class Customer(BaseModel):
    __tablename__ = 'customers'
    
    organization_id = db.Column(UUID(as_uuid=True), db.ForeignKey('organizations.id'), nullable=False)
    customer_number = db.Column(db.String(50), unique=True, index=True)
    company_name = db.Column(db.String(255), nullable=False)
    contact_person = db.Column(db.String(255))
    email = db.Column(db.String(255))
    phone = db.Column(db.String(50))
    btw_number = db.Column(db.String(30))
    payment_terms = db.Column(db.Integer, default=30)
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    
    # Relationships
    addresses = db.relationship('CustomerAddress', backref='customer', lazy=True, cascade='all, delete-orphan')
    contacts = db.relationship('CustomerContact', backref='customer', lazy=True, cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='customer', lazy=True)
    
    def __repr__(self):
        return f'<Customer {self.company_name}>'
    
    @property
    def primary_address(self):
        """Get primary address"""
        return next((addr for addr in self.addresses if addr.is_primary), None)
    
    @property
    def billing_address(self):
        """Get billing address"""
        return next((addr for addr in self.addresses if addr.address_type in ['billing', 'both']), None)
    
    @property
    def delivery_address(self):
        """Get delivery address"""
        return next((addr for addr in self.addresses if addr.address_type in ['delivery', 'both']), None)
    
    @property
    def primary_contact(self):
        """Get primary contact"""
        return next((contact for contact in self.contacts if contact.is_primary), None)
    
    def to_dict(self, include_relations=False):
        """Convert to dictionary"""
        data = super().to_dict()
        
        if include_relations:
            data['addresses'] = [addr.to_dict() for addr in self.addresses]
            data['contacts'] = [contact.to_dict() for contact in self.contacts]
            data['order_count'] = len(self.orders)
            data['total_revenue'] = sum(order.total_incl_btw or 0 for order in self.orders)
        
        return data

class CustomerAddress(BaseModel):
    __tablename__ = 'customer_addresses'
    
    customer_id = db.Column(UUID(as_uuid=True), db.ForeignKey('customers.id'), nullable=False)
    address_type = db.Column(db.String(20), nullable=False)  # billing, delivery, both
    street = db.Column(db.String(255), nullable=False)
    postal_code = db.Column(db.String(20), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(100), default='Nederland')
    is_primary = db.Column(db.Boolean, default=False)
    
    __table_args__ = (
        db.CheckConstraint("address_type IN ('billing', 'delivery', 'both')", name='check_address_type'),
    )
    
    def __repr__(self):
        return f'<CustomerAddress {self.customer_id} {self.address_type}>'
    
    @property
    def full_address(self):
        """Get formatted full address"""
        return f"{self.street}, {self.postal_code} {self.city}, {self.country}"

class CustomerContact(BaseModel):
    __tablename__ = 'customer_contacts'
    
    customer_id = db.Column(UUID(as_uuid=True), db.ForeignKey('customers.id'), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(100))
    email = db.Column(db.String(255))
    phone = db.Column(db.String(50))
    mobile = db.Column(db.String(50))
    department = db.Column(db.String(100))
    is_primary = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<CustomerContact {self.first_name} {self.last_name}>'
    
    @property
    def full_name(self):
        """Get full name"""
        return f"{self.first_name} {self.last_name}"
    
    def to_dict(self, exclude=None):
        """Convert to dictionary"""
        data = super().to_dict(exclude)
        data['full_name'] = self.full_name
        return data

