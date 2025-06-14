"""
Product models
"""
from src.models.database import db, BaseModel
from sqlalchemy.dialects.postgresql import UUID
from decimal import Decimal

class ProductCategory(BaseModel):
    __tablename__ = 'product_categories'
    
    organization_id = db.Column(UUID(as_uuid=True), db.ForeignKey('organizations.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    parent_id = db.Column(UUID(as_uuid=True), db.ForeignKey('product_categories.id'))
    sort_order = db.Column(db.Integer, default=0)
    
    # Self-referential relationship for hierarchical categories
    children = db.relationship('ProductCategory', backref=db.backref('parent', remote_side='ProductCategory.id'), lazy=True)
    products = db.relationship('Product', backref='category', lazy=True)
    
    def __repr__(self):
        return f'<ProductCategory {self.name}>'
    
    def to_dict(self, include_children=False):
        """Convert to dictionary"""
        data = super().to_dict()
        data['product_count'] = len(self.products)
        
        if include_children:
            data['children'] = [child.to_dict() for child in self.children]
        
        return data

class Product(BaseModel):
    __tablename__ = 'products'
    
    organization_id = db.Column(UUID(as_uuid=True), db.ForeignKey('organizations.id'), nullable=False)
    category_id = db.Column(UUID(as_uuid=True), db.ForeignKey('product_categories.id'))
    article_number = db.Column(db.String(100), index=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    unit = db.Column(db.String(50), nullable=False, default='stuk')
    price_excl_btw = db.Column(db.Numeric(10, 2))
    price_incl_btw = db.Column(db.Numeric(10, 2))
    btw_percentage = db.Column(db.Numeric(5, 2), default=Decimal('21.00'))
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    
    # Relationships
    attachments = db.relationship('ProductAttachment', backref='product', lazy=True, cascade='all, delete-orphan')
    order_items = db.relationship('OrderItem', backref='product', lazy=True)
    
    def __repr__(self):
        return f'<Product {self.name}>'
    
    def calculate_prices(self):
        """Calculate prices based on BTW percentage"""
        if self.price_excl_btw and self.btw_percentage:
            btw_multiplier = 1 + (self.btw_percentage / 100)
            self.price_incl_btw = self.price_excl_btw * btw_multiplier
        elif self.price_incl_btw and self.btw_percentage:
            btw_multiplier = 1 + (self.btw_percentage / 100)
            self.price_excl_btw = self.price_incl_btw / btw_multiplier
    
    @property
    def btw_amount(self):
        """Calculate BTW amount"""
        if self.price_excl_btw and self.btw_percentage:
            return self.price_excl_btw * (self.btw_percentage / 100)
        return Decimal('0.00')
    
    def to_dict(self, include_attachments=False):
        """Convert to dictionary"""
        data = super().to_dict()
        
        # Convert Decimal to float for JSON serialization
        if data.get('price_excl_btw'):
            data['price_excl_btw'] = float(data['price_excl_btw'])
        if data.get('price_incl_btw'):
            data['price_incl_btw'] = float(data['price_incl_btw'])
        if data.get('btw_percentage'):
            data['btw_percentage'] = float(data['btw_percentage'])
        
        data['btw_amount'] = float(self.btw_amount)
        data['category_name'] = self.category.name if self.category else None
        
        if include_attachments:
            data['attachments'] = [att.to_dict() for att in self.attachments]
        
        return data

class ProductAttachment(BaseModel):
    __tablename__ = 'product_attachments'
    
    product_id = db.Column(UUID(as_uuid=True), db.ForeignKey('products.id'), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_url = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(50))
    attachment_type = db.Column(db.String(50))  # datasheet, photo, manual, other
    
    __table_args__ = (
        db.CheckConstraint("attachment_type IN ('datasheet', 'photo', 'manual', 'other')", name='check_attachment_type'),
    )
    
    def __repr__(self):
        return f'<ProductAttachment {self.file_name}>'

