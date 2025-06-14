"""
Document generation routes
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from sqlalchemy import or_

from src.models.database import db
from src.models.document import DocumentTemplate, GeneratedDocument
from src.models.order import Order
from src.models.customer import Customer
from src.models.organization import Organization
from src.services.google_docs_service import GoogleDocsService, prepare_document_data, generate_document_number
from src.utils.auth import (
    get_current_user, require_permission, require_same_organization,
    format_error_response, format_success_response, paginate_query,
    extract_pagination_params, extract_search_params, audit_log
)

documents_bp = Blueprint('documents', __name__)

# Initialize Google Docs service
google_docs_service = GoogleDocsService()

@documents_bp.route('', methods=['GET'])
@jwt_required()
@require_permission('view_documents')
@require_same_organization
def get_documents(current_organization_id):
    """Get all generated documents"""
    try:
        page, per_page = extract_pagination_params(request.args)
        search, sort_by, sort_order = extract_search_params(request.args)
        template_type_filter = request.args.get('template_type')
        
        # Build query
        query = GeneratedDocument.query.filter_by(organization_id=current_organization_id)
        
        # Apply search filter
        if search:
            query = query.filter(
                or_(
                    GeneratedDocument.document_number.ilike(f'%{search}%'),
                    GeneratedDocument.file_name.ilike(f'%{search}%')
                )
            )
        
        # Apply template type filter
        if template_type_filter:
            query = query.filter_by(template_type=template_type_filter)
        
        # Apply sorting
        if hasattr(GeneratedDocument, sort_by):
            if sort_order == 'asc':
                query = query.order_by(getattr(GeneratedDocument, sort_by).asc())
            else:
                query = query.order_by(getattr(GeneratedDocument, sort_by).desc())
        
        # Paginate results
        result = paginate_query(query, page, per_page)
        
        return jsonify(result), 200
        
    except Exception as e:
        current_app.logger.error(f"Get documents error: {str(e)}")
        return format_error_response('Documenten ophalen gefaald', status_code=500)

@documents_bp.route('/<document_id>', methods=['GET'])
@jwt_required()
@require_permission('view_documents')
@require_same_organization
def get_document(document_id, current_organization_id):
    """Get specific document"""
    try:
        document = GeneratedDocument.query.filter_by(
            id=document_id,
            organization_id=current_organization_id
        ).first()
        
        if not document:
            return format_error_response('Document niet gevonden', status_code=404)
        
        document_data = document.to_dict()
        
        # Include related data
        if document.order:
            document_data['order'] = document.order.to_dict()
        if document.customer:
            document_data['customer'] = document.customer.to_dict()
        
        return jsonify({'document': document_data}), 200
        
    except Exception as e:
        current_app.logger.error(f"Get document error: {str(e)}")
        return format_error_response('Document ophalen gefaald', status_code=500)

@documents_bp.route('/templates', methods=['GET'])
@jwt_required()
@require_permission('view_documents')
@require_same_organization
def get_templates(current_organization_id):
    """Get all document templates"""
    try:
        # Get templates from database
        db_templates = DocumentTemplate.query.filter_by(
            organization_id=current_organization_id,
            is_active=True
        ).all()
        
        # Get Google Docs template info
        google_templates = []
        for template_type in google_docs_service.TEMPLATE_IDS.keys():
            try:
                template_info = google_docs_service.get_template_info(template_type)
                google_templates.append({
                    'type': template_type,
                    'name': template_info['name'],
                    'google_doc_id': template_info['id'],
                    'placeholders': template_info['placeholders'],
                    'is_google_template': True
                })
            except Exception as e:
                current_app.logger.warning(f"Failed to get template info for {template_type}: {e}")
        
        # Combine database and Google templates
        all_templates = [template.to_dict() for template in db_templates] + google_templates
        
        return jsonify({'templates': all_templates}), 200
        
    except Exception as e:
        current_app.logger.error(f"Get templates error: {str(e)}")
        return format_error_response('Sjablonen ophalen gefaald', status_code=500)

@documents_bp.route('/generate', methods=['POST'])
@jwt_required()
@require_permission('generate_documents')
@require_same_organization
@audit_log('generated_documents', 'INSERT')
def generate_document(current_organization_id):
    """Generate document from template"""
    try:
        current_user = get_current_user()
        data = request.get_json()
        
        if not data:
            return format_error_response('Geen data ontvangen')
        
        # Validate required fields
        template_type = data.get('template_type')
        if not template_type:
            return format_error_response('Template type is vereist')
        
        if template_type not in google_docs_service.TEMPLATE_IDS:
            return format_error_response('Ongeldig template type')
        
        # Get order data if order_id is provided
        order_id = data.get('order_id')
        order_data = {}
        customer_data = {}
        
        if order_id:
            order = Order.query.filter_by(
                id=order_id,
                organization_id=current_organization_id
            ).first()
            
            if not order:
                return format_error_response('Opdracht niet gevonden')
            
            order_data = order.to_dict(include_items=True)
            customer_data = order.customer.to_dict() if order.customer else {}
        else:
            # Use provided data
            order_data = data.get('order_data', {})
            customer_data = data.get('customer_data', {})
        
        # Get organization data
        organization = Organization.query.get(current_organization_id)
        organization_data = organization.to_dict() if organization else {}
        
        # Generate document number if not provided
        document_number = data.get('document_number')
        if not document_number:
            document_number = generate_document_number(template_type, current_organization_id)
        
        # Prepare document data
        document_data = prepare_document_data(
            {**order_data, 'document_number': document_number, **data},
            organization_data
        )
        
        # Add customer data if not in order
        if not document_data.get('customer') and customer_data:
            document_data['customer'] = customer_data
        
        # Validate data
        validation_result = google_docs_service.validate_data(template_type, document_data)
        if not validation_result['is_valid']:
            return format_error_response(
                'Data validatie gefaald',
                {'errors': validation_result['errors'], 'warnings': validation_result['warnings']}
            )
        
        # Generate document
        result = google_docs_service.generate_document(template_type, document_data)
        
        # Save to database
        generated_doc = GeneratedDocument(
            organization_id=current_organization_id,
            order_id=order_id,
            customer_id=order_data.get('customer_id') if order_id else None,
            template_type=template_type,
            document_number=document_number,
            file_name=f"{document_number}.pdf",
            google_doc_id=result['document_id'],
            pdf_url=result['pdf_url'],
            generation_data=document_data,
            created_by=current_user.id
        )
        
        db.session.add(generated_doc)
        db.session.commit()
        
        return format_success_response(
            'Document succesvol gegenereerd',
            {
                'document': generated_doc.to_dict(),
                'pdf_url': result['pdf_url'],
                'google_doc_id': result['document_id']
            },
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Generate document error: {str(e)}")
        return format_error_response(f'Document genereren gefaald: {str(e)}', status_code=500)

@documents_bp.route('/generate/preview', methods=['POST'])
@jwt_required()
@require_permission('generate_documents')
@require_same_organization
def preview_document(current_organization_id):
    """Preview document data without generating"""
    try:
        data = request.get_json()
        
        if not data:
            return format_error_response('Geen data ontvangen')
        
        template_type = data.get('template_type')
        if not template_type:
            return format_error_response('Template type is vereist')
        
        if template_type not in google_docs_service.TEMPLATE_IDS:
            return format_error_response('Ongeldig template type')
        
        # Get organization data
        organization = Organization.query.get(current_organization_id)
        organization_data = organization.to_dict() if organization else {}
        
        # Prepare document data
        document_data = prepare_document_data(data, organization_data)
        
        # Validate data
        validation_result = google_docs_service.validate_data(template_type, document_data)
        
        # Get template placeholders
        template_info = google_docs_service.get_template_info(template_type)
        
        return jsonify({
            'template_info': template_info,
            'document_data': document_data,
            'validation': validation_result,
            'preview_ready': validation_result['is_valid']
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Preview document error: {str(e)}")
        return format_error_response('Document preview gefaald', status_code=500)

@documents_bp.route('/<document_id>/regenerate', methods=['POST'])
@jwt_required()
@require_permission('generate_documents')
@require_same_organization
@audit_log('generated_documents', 'UPDATE')
def regenerate_document(document_id, current_organization_id):
    """Regenerate an existing document"""
    try:
        document = GeneratedDocument.query.filter_by(
            id=document_id,
            organization_id=current_organization_id
        ).first()
        
        if not document:
            return format_error_response('Document niet gevonden', status_code=404)
        
        # Use original generation data
        document_data = document.generation_data or {}
        
        # Allow data override from request
        request_data = request.get_json() or {}
        document_data.update(request_data)
        
        # Regenerate document
        result = google_docs_service.generate_document(document.template_type, document_data)
        
        # Update database record
        document.google_doc_id = result['document_id']
        document.pdf_url = result['pdf_url']
        document.generation_data = document_data
        
        db.session.commit()
        
        return format_success_response(
            'Document succesvol opnieuw gegenereerd',
            {
                'document': document.to_dict(),
                'pdf_url': result['pdf_url'],
                'google_doc_id': result['document_id']
            }
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Regenerate document error: {str(e)}")
        return format_error_response('Document opnieuw genereren gefaald', status_code=500)

@documents_bp.route('/<document_id>', methods=['DELETE'])
@jwt_required()
@require_permission('manage_documents')
@require_same_organization
@audit_log('generated_documents', 'DELETE')
def delete_document(document_id, current_organization_id):
    """Delete generated document"""
    try:
        document = GeneratedDocument.query.filter_by(
            id=document_id,
            organization_id=current_organization_id
        ).first()
        
        if not document:
            return format_error_response('Document niet gevonden', status_code=404)
        
        # TODO: Optionally delete from Google Drive as well
        
        db.session.delete(document)
        db.session.commit()
        
        return format_success_response('Document succesvol verwijderd')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Delete document error: {str(e)}")
        return format_error_response('Document verwijderen gefaald', status_code=500)

@documents_bp.route('/templates/<template_type>/placeholders', methods=['GET'])
@jwt_required()
@require_permission('view_documents')
def get_template_placeholders(template_type):
    """Get placeholders for a specific template type"""
    try:
        if template_type not in google_docs_service.TEMPLATE_IDS:
            return format_error_response('Ongeldig template type', status_code=404)
        
        template_info = google_docs_service.get_template_info(template_type)
        
        return jsonify({
            'template_type': template_type,
            'placeholders': template_info['placeholders']
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get template placeholders error: {str(e)}")
        return format_error_response('Template placeholders ophalen gefaald', status_code=500)

