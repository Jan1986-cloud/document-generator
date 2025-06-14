"""
Product management routes
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from sqlalchemy import or_
from decimal import Decimal

from src.models.database import db
from src.models.product import Product, ProductCategory, ProductAttachment
from src.utils.auth import (
    get_current_user, require_permission, require_same_organization,
    format_error_response, format_success_response, paginate_query,
    extract_pagination_params, extract_search_params, audit_log
)
from src.utils.validators import (
    validate_article_number, validate_decimal, validate_url
)

products_bp = Blueprint('products', __name__)

@products_bp.route('', methods=['GET'])
@jwt_required()
@require_permission('view_products')
@require_same_organization
def get_products(current_organization_id):
    """Get all products in organization"""
    try:
        page, per_page = extract_pagination_params(request.args)
        search, sort_by, sort_order = extract_search_params(request.args)
        category_filter = request.args.get('category_id')
        active_filter = request.args.get('active')
        
        # Build query
        query = Product.query.filter_by(organization_id=current_organization_id)
        
        # Apply search filter
        if search:
            query = query.filter(
                or_(
                    Product.name.ilike(f'%{search}%'),
                    Product.description.ilike(f'%{search}%'),
                    Product.article_number.ilike(f'%{search}%')
                )
            )
        
        # Apply category filter
        if category_filter:
            query = query.filter_by(category_id=category_filter)
        
        # Apply active filter
        if active_filter is not None:
            is_active = active_filter.lower() in ['true', '1', 'yes']
            query = query.filter_by(is_active=is_active)
        
        # Apply sorting
        if hasattr(Product, sort_by):
            if sort_order == 'asc':
                query = query.order_by(getattr(Product, sort_by).asc())
            else:
                query = query.order_by(getattr(Product, sort_by).desc())
        
        # Paginate results
        result = paginate_query(query, page, per_page)
        
        return jsonify(result), 200
        
    except Exception as e:
        current_app.logger.error(f"Get products error: {str(e)}")
        return format_error_response('Producten ophalen gefaald', status_code=500)

@products_bp.route('/<product_id>', methods=['GET'])
@jwt_required()
@require_permission('view_products')
@require_same_organization
def get_product(product_id, current_organization_id):
    """Get specific product with full details"""
    try:
        product = Product.query.filter_by(
            id=product_id,
            organization_id=current_organization_id
        ).first()
        
        if not product:
            return format_error_response('Product niet gevonden', status_code=404)
        
        product_data = product.to_dict(include_attachments=True)
        
        return jsonify({'product': product_data}), 200
        
    except Exception as e:
        current_app.logger.error(f"Get product error: {str(e)}")
        return format_error_response('Product ophalen gefaald', status_code=500)

@products_bp.route('', methods=['POST'])
@jwt_required()
@require_permission('manage_products')
@require_same_organization
@audit_log('products', 'INSERT')
def create_product(current_organization_id):
    """Create new product"""
    try:
        current_user = get_current_user()
        data = request.get_json()
        
        if not data:
            return format_error_response('Geen data ontvangen')
        
        # Validate required fields
        name = data.get('name', '').strip()
        if not name:
            return format_error_response('Productnaam is vereist')
        
        # Validate optional fields
        article_number = data.get('article_number', '').strip()
        if article_number and not validate_article_number(article_number):
            return format_error_response('Ongeldig artikelnummer')
        
        # Check if article number already exists
        if article_number:
            existing = Product.query.filter_by(
                organization_id=current_organization_id,
                article_number=article_number
            ).first()
            if existing:
                return format_error_response('Artikelnummer is al in gebruik')
        
        # Validate prices
        price_excl_btw = data.get('price_excl_btw')
        price_incl_btw = data.get('price_incl_btw')
        btw_percentage = data.get('btw_percentage', 21.00)
        
        if price_excl_btw is not None:
            try:
                price_excl_btw = Decimal(str(price_excl_btw))
            except (ValueError, TypeError):
                return format_error_response('Ongeldige prijs exclusief BTW')
        
        if price_incl_btw is not None:
            try:
                price_incl_btw = Decimal(str(price_incl_btw))
            except (ValueError, TypeError):
                return format_error_response('Ongeldige prijs inclusief BTW')
        
        try:
            btw_percentage = Decimal(str(btw_percentage))
        except (ValueError, TypeError):
            return format_error_response('Ongeldig BTW percentage')
        
        # Validate category
        category_id = data.get('category_id')
        if category_id:
            category = ProductCategory.query.filter_by(
                id=category_id,
                organization_id=current_organization_id
            ).first()
            if not category:
                return format_error_response('Ongeldige categorie')
        
        # Create product
        product = Product(
            organization_id=current_organization_id,
            category_id=category_id,
            article_number=article_number,
            name=name,
            description=data.get('description', '').strip(),
            unit=data.get('unit', 'stuk').strip(),
            price_excl_btw=price_excl_btw,
            price_incl_btw=price_incl_btw,
            btw_percentage=btw_percentage,
            is_active=data.get('is_active', True),
            created_by=current_user.id
        )
        
        # Calculate missing price
        product.calculate_prices()
        
        db.session.add(product)
        db.session.flush()  # Get product ID
        
        # Add attachments if provided
        attachments_data = data.get('attachments', [])
        for attachment_data in attachments_data:
            attachment = create_product_attachment(product.id, attachment_data)
            if isinstance(attachment, tuple):  # Error response
                return attachment
        
        db.session.commit()
        
        return format_success_response(
            'Product succesvol aangemaakt',
            {'product': product.to_dict(include_attachments=True)},
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Create product error: {str(e)}")
        return format_error_response('Product aanmaken gefaald', status_code=500)

@products_bp.route('/<product_id>', methods=['PUT'])
@jwt_required()
@require_permission('manage_products')
@require_same_organization
@audit_log('products', 'UPDATE')
def update_product(product_id, current_organization_id):
    """Update product"""
    try:
        product = Product.query.filter_by(
            id=product_id,
            organization_id=current_organization_id
        ).first()
        
        if not product:
            return format_error_response('Product niet gevonden', status_code=404)
        
        data = request.get_json()
        if not data:
            return format_error_response('Geen data ontvangen')
        
        # Update fields
        if 'name' in data:
            name = data['name'].strip()
            if not name:
                return format_error_response('Productnaam is vereist')
            product.name = name
        
        if 'article_number' in data:
            article_number = data['article_number'].strip()
            if article_number and not validate_article_number(article_number):
                return format_error_response('Ongeldig artikelnummer')
            
            # Check if article number already exists (excluding current product)
            if article_number:
                existing = Product.query.filter(
                    Product.organization_id == current_organization_id,
                    Product.article_number == article_number,
                    Product.id != product_id
                ).first()
                if existing:
                    return format_error_response('Artikelnummer is al in gebruik')
            
            product.article_number = article_number
        
        if 'description' in data:
            product.description = data['description'].strip()
        
        if 'unit' in data:
            product.unit = data['unit'].strip() or 'stuk'
        
        if 'category_id' in data:
            category_id = data['category_id']
            if category_id:
                category = ProductCategory.query.filter_by(
                    id=category_id,
                    organization_id=current_organization_id
                ).first()
                if not category:
                    return format_error_response('Ongeldige categorie')
            product.category_id = category_id
        
        # Update prices
        if 'price_excl_btw' in data:
            try:
                product.price_excl_btw = Decimal(str(data['price_excl_btw'])) if data['price_excl_btw'] is not None else None
            except (ValueError, TypeError):
                return format_error_response('Ongeldige prijs exclusief BTW')
        
        if 'price_incl_btw' in data:
            try:
                product.price_incl_btw = Decimal(str(data['price_incl_btw'])) if data['price_incl_btw'] is not None else None
            except (ValueError, TypeError):
                return format_error_response('Ongeldige prijs inclusief BTW')
        
        if 'btw_percentage' in data:
            try:
                product.btw_percentage = Decimal(str(data['btw_percentage']))
            except (ValueError, TypeError):
                return format_error_response('Ongeldig BTW percentage')
        
        if 'is_active' in data:
            product.is_active = bool(data['is_active'])
        
        # Recalculate prices
        product.calculate_prices()
        
        db.session.commit()
        
        return format_success_response(
            'Product succesvol bijgewerkt',
            {'product': product.to_dict(include_attachments=True)}
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update product error: {str(e)}")
        return format_error_response('Product bijwerken gefaald', status_code=500)

@products_bp.route('/<product_id>', methods=['DELETE'])
@jwt_required()
@require_permission('manage_products')
@require_same_organization
@audit_log('products', 'DELETE')
def delete_product(product_id, current_organization_id):
    """Delete product (soft delete by deactivating)"""
    try:
        product = Product.query.filter_by(
            id=product_id,
            organization_id=current_organization_id
        ).first()
        
        if not product:
            return format_error_response('Product niet gevonden', status_code=404)
        
        # Check if product is used in orders
        if product.order_items:
            return format_error_response(
                'Product kan niet worden verwijderd omdat het gebruikt wordt in opdrachten'
            )
        
        # Soft delete by deactivating
        product.is_active = False
        db.session.commit()
        
        return format_success_response('Product succesvol gedeactiveerd')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Delete product error: {str(e)}")
        return format_error_response('Product verwijderen gefaald', status_code=500)

@products_bp.route('/categories', methods=['GET'])
@jwt_required()
@require_permission('view_products')
@require_same_organization
def get_categories(current_organization_id):
    """Get all product categories"""
    try:
        categories = ProductCategory.query.filter_by(
            organization_id=current_organization_id
        ).order_by(ProductCategory.sort_order, ProductCategory.name).all()
        
        categories_data = [cat.to_dict(include_children=True) for cat in categories if not cat.parent_id]
        
        return jsonify({'categories': categories_data}), 200
        
    except Exception as e:
        current_app.logger.error(f"Get categories error: {str(e)}")
        return format_error_response('Categorieën ophalen gefaald', status_code=500)

@products_bp.route('/categories', methods=['POST'])
@jwt_required()
@require_permission('manage_products')
@require_same_organization
@audit_log('product_categories', 'INSERT')
def create_category(current_organization_id):
    """Create new product category"""
    try:
        data = request.get_json()
        
        if not data:
            return format_error_response('Geen data ontvangen')
        
        name = data.get('name', '').strip()
        if not name:
            return format_error_response('Categorienaam is vereist')
        
        # Check if category name already exists
        existing = ProductCategory.query.filter_by(
            organization_id=current_organization_id,
            name=name
        ).first()
        if existing:
            return format_error_response('Categorienaam is al in gebruik')
        
        # Validate parent category
        parent_id = data.get('parent_id')
        if parent_id:
            parent = ProductCategory.query.filter_by(
                id=parent_id,
                organization_id=current_organization_id
            ).first()
            if not parent:
                return format_error_response('Ongeldige bovenliggende categorie')
        
        category = ProductCategory(
            organization_id=current_organization_id,
            name=name,
            description=data.get('description', '').strip(),
            parent_id=parent_id,
            sort_order=data.get('sort_order', 0)
        )
        
        db.session.add(category)
        db.session.commit()
        
        return format_success_response(
            'Categorie succesvol aangemaakt',
            {'category': category.to_dict()},
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Create category error: {str(e)}")
        return format_error_response('Categorie aanmaken gefaald', status_code=500)

@products_bp.route('/<product_id>/attachments', methods=['POST'])
@jwt_required()
@require_permission('manage_products')
@require_same_organization
def add_product_attachment(product_id, current_organization_id):
    """Add attachment to product"""
    try:
        product = Product.query.filter_by(
            id=product_id,
            organization_id=current_organization_id
        ).first()
        
        if not product:
            return format_error_response('Product niet gevonden', status_code=404)
        
        data = request.get_json()
        if not data:
            return format_error_response('Geen data ontvangen')
        
        attachment = create_product_attachment(product_id, data)
        if isinstance(attachment, tuple):  # Error response
            return attachment
        
        db.session.commit()
        
        return format_success_response(
            'Bijlage succesvol toegevoegd',
            {'attachment': attachment.to_dict()},
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Add product attachment error: {str(e)}")
        return format_error_response('Bijlage toevoegen gefaald', status_code=500)

def create_product_attachment(product_id, attachment_data):
    """Helper function to create product attachment"""
    try:
        # Validate required fields
        file_name = attachment_data.get('file_name', '').strip()
        file_url = attachment_data.get('file_url', '').strip()
        attachment_type = attachment_data.get('attachment_type', 'other')
        
        if not file_name or not file_url:
            return format_error_response('Bestandsnaam en URL zijn vereist')
        
        if attachment_type not in ['datasheet', 'photo', 'manual', 'other']:
            return format_error_response('Ongeldig bijlagetype')
        
        if not validate_url(file_url):
            return format_error_response('Ongeldige URL')
        
        # Create attachment
        attachment = ProductAttachment(
            product_id=product_id,
            file_name=file_name,
            file_url=file_url,
            file_type=attachment_data.get('file_type', '').strip(),
            attachment_type=attachment_type
        )
        
        db.session.add(attachment)
        return attachment
        
    except Exception as e:
        return format_error_response(f'Bijlage aanmaken gefaald: {str(e)}', status_code=500)

