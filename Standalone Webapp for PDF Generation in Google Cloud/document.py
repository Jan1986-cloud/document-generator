"""
Document models
"""
from src.models.database import db, BaseModel
from sqlalchemy.dialects.postgresql import UUID
import enum

class DocumentType(enum.Enum):
    QUOTE = 'quote'
    WORK_ORDER = 'work_order'
    INVOICE = 'invoice'
    COMBINED_INVOICE = 'combined_invoice'

class DocumentStatus(enum.Enum):
    DRAFT = 'draft'
    SENT = 'sent'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    PAID = 'paid'
    CANCELLED = 'cancelled'

class DocumentTemplate(BaseModel):
    __tablename__ = 'document_templates'
    
    organization_id = db.Column(UUID(as_uuid=True), db.ForeignKey('organizations.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    document_type = db.Column(db.Enum(DocumentType), nullable=False)
    google_doc_id = db.Column(db.String(255))
    template_url = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    placeholders = db.Column(db.JSON, default=list)
    created_by = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    
    # Relationships
    generated_documents = db.relationship('GeneratedDocument', backref='template', lazy=True)
    
    def __repr__(self):
        return f'<DocumentTemplate {self.name}>'
    
    def to_dict(self, exclude=None):
        """Convert to dictionary"""
        data = super().to_dict(exclude)
        data['document_type'] = self.document_type.value
        data['creator_name'] = self.creator.full_name if self.creator else None
        data['usage_count'] = len(self.generated_documents)
        return data
    
    def get_placeholders(self):
        """Get list of placeholders in template"""
        return self.placeholders or []
    
    def add_placeholder(self, placeholder):
        """Add placeholder to template"""
        if not self.placeholders:
            self.placeholders = []
        if placeholder not in self.placeholders:
            self.placeholders.append(placeholder)
    
    def remove_placeholder(self, placeholder):
        """Remove placeholder from template"""
        if self.placeholders and placeholder in self.placeholders:
            self.placeholders.remove(placeholder)

class GeneratedDocument(BaseModel):
    __tablename__ = 'generated_documents'
    
    organization_id = db.Column(UUID(as_uuid=True), db.ForeignKey('organizations.id'), nullable=False)
    order_id = db.Column(UUID(as_uuid=True), db.ForeignKey('orders.id'), nullable=False)
    template_id = db.Column(UUID(as_uuid=True), db.ForeignKey('document_templates.id'), nullable=False)
    document_number = db.Column(db.String(50), nullable=False, index=True)
    document_type = db.Column(db.Enum(DocumentType), nullable=False)
    status = db.Column(db.Enum(DocumentStatus), default=DocumentStatus.DRAFT)
    file_url = db.Column(db.String(500))
    google_doc_id = db.Column(db.String(255))
    generated_data = db.Column(db.JSON)
    sent_at = db.Column(db.DateTime(timezone=True))
    sent_to = db.Column(db.String(255))
    created_by = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    
    def __repr__(self):
        return f'<GeneratedDocument {self.document_number}>'
    
    def to_dict(self, exclude=None):
        """Convert to dictionary"""
        data = super().to_dict(exclude)
        data['document_type'] = self.document_type.value
        data['status'] = self.status.value
        data['order_number'] = self.order.order_number if self.order else None
        data['customer_name'] = self.order.customer.company_name if self.order and self.order.customer else None
        data['template_name'] = self.template.name if self.template else None
        data['creator_name'] = self.creator.full_name if self.creator else None
        return data
    
    def generate_document_number(self, prefix=None):
        """Generate document number"""
        if not prefix:
            prefix_map = {
                DocumentType.QUOTE: 'OFF',
                DocumentType.WORK_ORDER: 'WB',
                DocumentType.INVOICE: 'FACT',
                DocumentType.COMBINED_INVOICE: 'FACT'
            }
            prefix = prefix_map.get(self.document_type, 'DOC')
        
        # Get next number for this type and organization
        from sqlalchemy import func
        last_doc = db.session.query(func.max(GeneratedDocument.document_number)).filter(
            GeneratedDocument.organization_id == self.organization_id,
            GeneratedDocument.document_type == self.document_type,
            GeneratedDocument.document_number.like(f'{prefix}%')
        ).scalar()
        
        if last_doc:
            try:
                last_number = int(last_doc.split('-')[1])
                next_number = last_number + 1
            except (IndexError, ValueError):
                next_number = 1
        else:
            next_number = 1
        
        # Format: PREFIX-YYYY-NNNN
        from datetime import datetime
        year = datetime.now().year
        self.document_number = f"{prefix}-{year}-{next_number:04d}"
        
        return self.document_number

