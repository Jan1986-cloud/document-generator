"""
Order models
"""
from src.models.database import db, BaseModel
from sqlalchemy.dialects.postgresql import UUID
from decimal import Decimal
import enum
from datetime import date

class OrderStatus(enum.Enum):
    DRAFT = 'draft'
    CONFIRMED = 'confirmed'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'

class Order(BaseModel):
    __tablename__ = 'orders'
    
    organization_id = db.Column(UUID(as_uuid=True), db.ForeignKey('organizations.id'), nullable=False)
    customer_id = db.Column(UUID(as_uuid=True), db.ForeignKey('customers.id'), nullable=False)
    order_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    order_date = db.Column(db.Date, nullable=False, default=date.today)
    description = db.Column(db.Text)
    status = db.Column(db.Enum(OrderStatus), default=OrderStatus.DRAFT)
    subtotal_excl_btw = db.Column(db.Numeric(10, 2), default=Decimal('0.00'))
    btw_amount = db.Column(db.Numeric(10, 2), default=Decimal('0.00'))
    total_incl_btw = db.Column(db.Numeric(10, 2), default=Decimal('0.00'))
    notes = db.Column(db.Text)
    created_by = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    assigned_to = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    
    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    generated_documents = db.relationship('GeneratedDocument', backref='order', lazy=True)
    
    def __repr__(self):
        return f'<Order {self.order_number}>'
    
    def calculate_totals(self):
        """Calculate order totals from items"""
        self.subtotal_excl_btw = sum(item.total_excl_btw for item in self.items)
        self.btw_amount = sum(item.btw_amount for item in self.items)
        self.total_incl_btw = sum(item.total_incl_btw for item in self.items)
    
    def add_item(self, product_id=None, description=None, quantity=1, unit_price_excl_btw=0, 
                 unit=None, btw_percentage=21.00, delivery_notes=None):
        """Add item to order"""
        item = OrderItem(
            order_id=self.id,
            product_id=product_id,
            description=description,
            quantity=Decimal(str(quantity)),
            unit=unit or 'stuk',
            unit_price_excl_btw=Decimal(str(unit_price_excl_btw)),
            btw_percentage=Decimal(str(btw_percentage)),
            delivery_notes=delivery_notes,
            sort_order=len(self.items)
        )
        item.calculate_totals()
        self.items.append(item)
        self.calculate_totals()
        return item
    
    def to_dict(self, include_items=False):
        """Convert to dictionary"""
        data = super().to_dict()
        data['status'] = self.status.value
        data['customer_name'] = self.customer.company_name if self.customer else None
        data['creator_name'] = self.creator.full_name if self.creator else None
        data['assignee_name'] = self.assignee.full_name if self.assignee else None
        
        # Convert Decimal to float for JSON serialization
        if data.get('subtotal_excl_btw'):
            data['subtotal_excl_btw'] = float(data['subtotal_excl_btw'])
        if data.get('btw_amount'):
            data['btw_amount'] = float(data['btw_amount'])
        if data.get('total_incl_btw'):
            data['total_incl_btw'] = float(data['total_incl_btw'])
        
        data['item_count'] = len(self.items)
        
        if include_items:
            data['items'] = [item.to_dict() for item in self.items]
        
        return data

class OrderItem(BaseModel):
    __tablename__ = 'order_items'
    
    order_id = db.Column(UUID(as_uuid=True), db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(UUID(as_uuid=True), db.ForeignKey('products.id'))
    description = db.Column(db.Text, nullable=False)
    quantity = db.Column(db.Numeric(10, 3), nullable=False)
    unit = db.Column(db.String(50), nullable=False)
    unit_price_excl_btw = db.Column(db.Numeric(10, 2), nullable=False)
    unit_price_incl_btw = db.Column(db.Numeric(10, 2), nullable=False)
    btw_percentage = db.Column(db.Numeric(5, 2), nullable=False)
    total_excl_btw = db.Column(db.Numeric(10, 2), nullable=False)
    total_incl_btw = db.Column(db.Numeric(10, 2), nullable=False)
    delivery_notes = db.Column(db.Text)
    sort_order = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<OrderItem {self.description[:50]}>'
    
    def calculate_totals(self):
        """Calculate item totals"""
        # Calculate unit price including BTW
        btw_multiplier = 1 + (self.btw_percentage / 100)
        self.unit_price_incl_btw = self.unit_price_excl_btw * btw_multiplier
        
        # Calculate totals
        self.total_excl_btw = self.unit_price_excl_btw * self.quantity
        self.total_incl_btw = self.unit_price_incl_btw * self.quantity
    
    @property
    def btw_amount(self):
        """Calculate BTW amount for this item"""
        return self.total_incl_btw - self.total_excl_btw
    
    def to_dict(self, exclude=None):
        """Convert to dictionary"""
        data = super().to_dict(exclude)
        
        # Convert Decimal to float for JSON serialization
        numeric_fields = [
            'quantity', 'unit_price_excl_btw', 'unit_price_incl_btw', 
            'btw_percentage', 'total_excl_btw', 'total_incl_btw'
        ]
        for field in numeric_fields:
            if data.get(field) is not None:
                data[field] = float(data[field])
        
        data['btw_amount'] = float(self.btw_amount)
        data['product_name'] = self.product.name if self.product else None
        
        return data

