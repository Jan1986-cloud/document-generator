"""
Order management routes
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from sqlalchemy import or_
from decimal import Decimal
from datetime import date, datetime

from src.models.database import db
from src.models.order import Order, OrderItem, OrderStatus
from src.models.customer import Customer
from src.models.product import Product
from src.utils.auth import (
    get_current_user, require_permission, require_same_organization,
    format_error_response, format_success_response, paginate_query,
    extract_pagination_params, extract_search_params, audit_log
)
from src.utils.validators import validate_order_number

orders_bp = Blueprint('orders', __name__)

@orders_bp.route('', methods=['GET'])
@jwt_required()
@require_permission('view_orders')
@require_same_organization
def get_orders(current_organization_id):
    """Get all orders in organization"""
    try:
        page, per_page = extract_pagination_params(request.args)
        search, sort_by, sort_order = extract_search_params(request.args)
        status_filter = request.args.get('status')
        customer_filter = request.args.get('customer_id')
        assigned_filter = request.args.get('assigned_to')
        
        # Build query
        query = Order.query.filter_by(organization_id=current_organization_id)
        
        # Apply search filter
        if search:
            query = query.join(Customer).filter(
                or_(
                    Order.order_number.ilike(f'%{search}%'),
                    Order.description.ilike(f'%{search}%'),
                    Customer.company_name.ilike(f'%{search}%')
                )
            )
        
        # Apply status filter
        if status_filter:
            try:
                status_enum = OrderStatus(status_filter)
                query = query.filter_by(status=status_enum)
            except ValueError:
                pass
        
        # Apply customer filter
        if customer_filter:
            query = query.filter_by(customer_id=customer_filter)
        
        # Apply assigned filter
        if assigned_filter:
            query = query.filter_by(assigned_to=assigned_filter)
        
        # Apply sorting
        if hasattr(Order, sort_by):
            if sort_order == 'asc':
                query = query.order_by(getattr(Order, sort_by).asc())
            else:
                query = query.order_by(getattr(Order, sort_by).desc())
        
        # Paginate results
        result = paginate_query(query, page, per_page)
        
        return jsonify(result), 200
        
    except Exception as e:
        current_app.logger.error(f"Get orders error: {str(e)}")
        return format_error_response('Opdrachten ophalen gefaald', status_code=500)

@orders_bp.route('/<order_id>', methods=['GET'])
@jwt_required()
@require_permission('view_orders')
@require_same_organization
def get_order(order_id, current_organization_id):
    """Get specific order with full details"""
    try:
        order = Order.query.filter_by(
            id=order_id,
            organization_id=current_organization_id
        ).first()
        
        if not order:
            return format_error_response('Opdracht niet gevonden', status_code=404)
        
        order_data = order.to_dict(include_items=True)
        
        return jsonify({'order': order_data}), 200
        
    except Exception as e:
        current_app.logger.error(f"Get order error: {str(e)}")
        return format_error_response('Opdracht ophalen gefaald', status_code=500)

@orders_bp.route('', methods=['POST'])
@jwt_required()
@require_permission('manage_orders')
@require_same_organization
@audit_log('orders', 'INSERT')
def create_order(current_organization_id):
    """Create new order"""
    try:
        current_user = get_current_user()
        data = request.get_json()
        
        if not data:
            return format_error_response('Geen data ontvangen')
        
        # Validate required fields
        customer_id = data.get('customer_id')
        if not customer_id:
            return format_error_response('Klant is vereist')
        
        # Validate customer exists
        customer = Customer.query.filter_by(
            id=customer_id,
            organization_id=current_organization_id
        ).first()
        if not customer:
            return format_error_response('Ongeldige klant')
        
        # Generate order number if not provided
        order_number = data.get('order_number', '').strip()
        if not order_number:
            order_number = generate_order_number(current_organization_id)
        elif not validate_order_number(order_number):
            return format_error_response('Ongeldig opdrachtnummer')
        
        # Check if order number already exists
        if Order.query.filter_by(
            organization_id=current_organization_id,
            order_number=order_number
        ).first():
            return format_error_response('Opdrachtnummer is al in gebruik')
        
        # Parse order date
        order_date = data.get('order_date')
        if order_date:
            try:
                order_date = datetime.strptime(order_date, '%Y-%m-%d').date()
            except ValueError:
                return format_error_response('Ongeldige datum format (gebruik YYYY-MM-DD)')
        else:
            order_date = date.today()
        
        # Create order
        order = Order(
            organization_id=current_organization_id,
            customer_id=customer_id,
            order_number=order_number,
            order_date=order_date,
            description=data.get('description', '').strip(),
            status=OrderStatus.DRAFT,
            notes=data.get('notes', '').strip(),
            created_by=current_user.id,
            assigned_to=data.get('assigned_to')
        )
        
        db.session.add(order)
        db.session.flush()  # Get order ID
        
        # Add items if provided
        items_data = data.get('items', [])
        for item_data in items_data:
            item = create_order_item(order.id, item_data, current_organization_id)
            if isinstance(item, tuple):  # Error response
                return item
        
        # Calculate totals
        order.calculate_totals()
        
        db.session.commit()
        
        return format_success_response(
            'Opdracht succesvol aangemaakt',
            {'order': order.to_dict(include_items=True)},
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Create order error: {str(e)}")
        return format_error_response('Opdracht aanmaken gefaald', status_code=500)

@orders_bp.route('/<order_id>', methods=['PUT'])
@jwt_required()
@require_permission('manage_orders')
@require_same_organization
@audit_log('orders', 'UPDATE')
def update_order(order_id, current_organization_id):
    """Update order"""
    try:
        order = Order.query.filter_by(
            id=order_id,
            organization_id=current_organization_id
        ).first()
        
        if not order:
            return format_error_response('Opdracht niet gevonden', status_code=404)
        
        data = request.get_json()
        if not data:
            return format_error_response('Geen data ontvangen')
        
        # Update fields
        if 'description' in data:
            order.description = data['description'].strip()
        
        if 'notes' in data:
            order.notes = data['notes'].strip()
        
        if 'status' in data:
            try:
                status_enum = OrderStatus(data['status'])
                order.status = status_enum
            except ValueError:
                return format_error_response('Ongeldige status')
        
        if 'assigned_to' in data:
            order.assigned_to = data['assigned_to']
        
        if 'order_date' in data:
            try:
                order.order_date = datetime.strptime(data['order_date'], '%Y-%m-%d').date()
            except ValueError:
                return format_error_response('Ongeldige datum format (gebruik YYYY-MM-DD)')
        
        db.session.commit()
        
        return format_success_response(
            'Opdracht succesvol bijgewerkt',
            {'order': order.to_dict(include_items=True)}
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update order error: {str(e)}")
        return format_error_response('Opdracht bijwerken gefaald', status_code=500)

@orders_bp.route('/<order_id>/items', methods=['POST'])
@jwt_required()
@require_permission('manage_orders')
@require_same_organization
def add_order_item(order_id, current_organization_id):
    """Add item to order"""
    try:
        order = Order.query.filter_by(
            id=order_id,
            organization_id=current_organization_id
        ).first()
        
        if not order:
            return format_error_response('Opdracht niet gevonden', status_code=404)
        
        data = request.get_json()
        if not data:
            return format_error_response('Geen data ontvangen')
        
        item = create_order_item(order_id, data, current_organization_id)
        if isinstance(item, tuple):  # Error response
            return item
        
        # Recalculate order totals
        order.calculate_totals()
        
        db.session.commit()
        
        return format_success_response(
            'Item succesvol toegevoegd',
            {'item': item.to_dict()},
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Add order item error: {str(e)}")
        return format_error_response('Item toevoegen gefaald', status_code=500)

@orders_bp.route('/<order_id>/items/<item_id>', methods=['PUT'])
@jwt_required()
@require_permission('manage_orders')
@require_same_organization
def update_order_item(order_id, item_id, current_organization_id):
    """Update order item"""
    try:
        order = Order.query.filter_by(
            id=order_id,
            organization_id=current_organization_id
        ).first()
        
        if not order:
            return format_error_response('Opdracht niet gevonden', status_code=404)
        
        item = OrderItem.query.filter_by(
            id=item_id,
            order_id=order_id
        ).first()
        
        if not item:
            return format_error_response('Item niet gevonden', status_code=404)
        
        data = request.get_json()
        if not data:
            return format_error_response('Geen data ontvangen')
        
        # Update item fields
        if 'description' in data:
            item.description = data['description'].strip()
        
        if 'quantity' in data:
            try:
                item.quantity = Decimal(str(data['quantity']))
            except (ValueError, TypeError):
                return format_error_response('Ongeldige hoeveelheid')
        
        if 'unit_price_excl_btw' in data:
            try:
                item.unit_price_excl_btw = Decimal(str(data['unit_price_excl_btw']))
            except (ValueError, TypeError):
                return format_error_response('Ongeldige eenheidsprijs')
        
        if 'btw_percentage' in data:
            try:
                item.btw_percentage = Decimal(str(data['btw_percentage']))
            except (ValueError, TypeError):
                return format_error_response('Ongeldig BTW percentage')
        
        if 'delivery_notes' in data:
            item.delivery_notes = data['delivery_notes'].strip()
        
        # Recalculate item totals
        item.calculate_totals()
        
        # Recalculate order totals
        order.calculate_totals()
        
        db.session.commit()
        
        return format_success_response(
            'Item succesvol bijgewerkt',
            {'item': item.to_dict()}
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update order item error: {str(e)}")
        return format_error_response('Item bijwerken gefaald', status_code=500)

@orders_bp.route('/<order_id>/items/<item_id>', methods=['DELETE'])
@jwt_required()
@require_permission('manage_orders')
@require_same_organization
def delete_order_item(order_id, item_id, current_organization_id):
    """Delete order item"""
    try:
        order = Order.query.filter_by(
            id=order_id,
            organization_id=current_organization_id
        ).first()
        
        if not order:
            return format_error_response('Opdracht niet gevonden', status_code=404)
        
        item = OrderItem.query.filter_by(
            id=item_id,
            order_id=order_id
        ).first()
        
        if not item:
            return format_error_response('Item niet gevonden', status_code=404)
        
        db.session.delete(item)
        
        # Recalculate order totals
        order.calculate_totals()
        
        db.session.commit()
        
        return format_success_response('Item succesvol verwijderd')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Delete order item error: {str(e)}")
        return format_error_response('Item verwijderen gefaald', status_code=500)

def generate_order_number(organization_id):
    """Generate next order number"""
    from sqlalchemy import func
    
    # Get current year
    current_year = date.today().year
    
    # Find last order number for this year
    last_order = db.session.query(func.max(Order.order_number)).filter(
        Order.organization_id == organization_id,
        Order.order_number.like(f'ORD-{current_year}-%')
    ).scalar()
    
    if last_order:
        try:
            last_number = int(last_order.split('-')[2])
            next_number = last_number + 1
        except (IndexError, ValueError):
            next_number = 1
    else:
        next_number = 1
    
    return f"ORD-{current_year}-{next_number:04d}"

def create_order_item(order_id, item_data, organization_id):
    """Helper function to create order item"""
    try:
        # Validate required fields
        description = item_data.get('description', '').strip()
        quantity = item_data.get('quantity', 1)
        unit_price_excl_btw = item_data.get('unit_price_excl_btw', 0)
        
        if not description:
            return format_error_response('Omschrijving is vereist')
        
        try:
            quantity = Decimal(str(quantity))
            unit_price_excl_btw = Decimal(str(unit_price_excl_btw))
        except (ValueError, TypeError):
            return format_error_response('Ongeldige hoeveelheid of prijs')
        
        # Validate product if provided
        product_id = item_data.get('product_id')
        if product_id:
            product = Product.query.filter_by(
                id=product_id,
                organization_id=organization_id
            ).first()
            if not product:
                return format_error_response('Ongeldig product')
            
            # Use product data if not provided
            if not description:
                description = product.name
            if unit_price_excl_btw == 0 and product.price_excl_btw:
                unit_price_excl_btw = product.price_excl_btw
        
        # Create item
        item = OrderItem(
            order_id=order_id,
            product_id=product_id,
            description=description,
            quantity=quantity,
            unit=item_data.get('unit', 'stuk'),
            unit_price_excl_btw=unit_price_excl_btw,
            btw_percentage=Decimal(str(item_data.get('btw_percentage', 21.00))),
            delivery_notes=item_data.get('delivery_notes', '').strip(),
            sort_order=item_data.get('sort_order', 0)
        )
        
        # Calculate totals
        item.calculate_totals()
        
        db.session.add(item)
        return item
        
    except Exception as e:
        return format_error_response(f'Item aanmaken gefaald: {str(e)}', status_code=500)

