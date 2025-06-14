"""
Customer management routes
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from sqlalchemy import or_

from src.models.database import db
from src.models.customer import Customer, CustomerAddress, CustomerContact
from src.utils.auth import (
    get_current_user, require_permission, require_same_organization,
    format_error_response, format_success_response, paginate_query,
    extract_pagination_params, extract_search_params, audit_log
)
from src.utils.validators import (
    validate_email, validate_phone, validate_postal_code, 
    validate_btw_number, validate_customer_number
)

customers_bp = Blueprint('customers', __name__)

@customers_bp.route('', methods=['GET'])
@jwt_required()
@require_permission('view_customers')
@require_same_organization
def get_customers(current_organization_id):
    """Get all customers in organization"""
    try:
        page, per_page = extract_pagination_params(request.args)
        search, sort_by, sort_order = extract_search_params(request.args)
        active_filter = request.args.get('active')
        
        # Build query
        query = Customer.query.filter_by(organization_id=current_organization_id)
        
        # Apply search filter
        if search:
            query = query.filter(
                or_(
                    Customer.company_name.ilike(f'%{search}%'),
                    Customer.contact_person.ilike(f'%{search}%'),
                    Customer.email.ilike(f'%{search}%'),
                    Customer.customer_number.ilike(f'%{search}%')
                )
            )
        
        # Apply active filter
        if active_filter is not None:
            is_active = active_filter.lower() in ['true', '1', 'yes']
            query = query.filter_by(is_active=is_active)
        
        # Apply sorting
        if hasattr(Customer, sort_by):
            if sort_order == 'asc':
                query = query.order_by(getattr(Customer, sort_by).asc())
            else:
                query = query.order_by(getattr(Customer, sort_by).desc())
        
        # Paginate results
        result = paginate_query(query, page, per_page)
        
        return jsonify(result), 200
        
    except Exception as e:
        current_app.logger.error(f"Get customers error: {str(e)}")
        return format_error_response('Klanten ophalen gefaald', status_code=500)

@customers_bp.route('/<customer_id>', methods=['GET'])
@jwt_required()
@require_permission('view_customers')
@require_same_organization
def get_customer(customer_id, current_organization_id):
    """Get specific customer with full details"""
    try:
        customer = Customer.query.filter_by(
            id=customer_id,
            organization_id=current_organization_id
        ).first()
        
        if not customer:
            return format_error_response('Klant niet gevonden', status_code=404)
        
        customer_data = customer.to_dict(include_relations=True)
        
        return jsonify({'customer': customer_data}), 200
        
    except Exception as e:
        current_app.logger.error(f"Get customer error: {str(e)}")
        return format_error_response('Klant ophalen gefaald', status_code=500)

@customers_bp.route('', methods=['POST'])
@jwt_required()
@require_permission('manage_customers')
@require_same_organization
@audit_log('customers', 'INSERT')
def create_customer(current_organization_id):
    """Create new customer"""
    try:
        current_user = get_current_user()
        data = request.get_json()
        
        if not data:
            return format_error_response('Geen data ontvangen')
        
        # Validate required fields
        company_name = data.get('company_name', '').strip()
        if not company_name:
            return format_error_response('Bedrijfsnaam is vereist')
        
        # Validate optional fields
        email = data.get('email', '').strip()
        if email and not validate_email(email):
            return format_error_response('Ongeldig email adres')
        
        phone = data.get('phone', '').strip()
        if phone and not validate_phone(phone):
            return format_error_response('Ongeldig telefoonnummer')
        
        btw_number = data.get('btw_number', '').strip()
        if btw_number and not validate_btw_number(btw_number):
            return format_error_response('Ongeldig BTW nummer')
        
        # Generate customer number if not provided
        customer_number = data.get('customer_number', '').strip()
        if not customer_number:
            # Generate next customer number
            last_customer = Customer.query.filter_by(
                organization_id=current_organization_id
            ).order_by(Customer.customer_number.desc()).first()
            
            if last_customer and last_customer.customer_number:
                try:
                    last_number = int(last_customer.customer_number)
                    customer_number = f"{last_number + 1:06d}"
                except ValueError:
                    customer_number = "000001"
            else:
                customer_number = "000001"
        elif not validate_customer_number(customer_number):
            return format_error_response('Ongeldig klantnummer')
        
        # Check if customer number already exists
        if Customer.query.filter_by(
            organization_id=current_organization_id,
            customer_number=customer_number
        ).first():
            return format_error_response('Klantnummer is al in gebruik')
        
        # Create customer
        customer = Customer(
            organization_id=current_organization_id,
            customer_number=customer_number,
            company_name=company_name,
            contact_person=data.get('contact_person', '').strip(),
            email=email,
            phone=phone,
            btw_number=btw_number,
            payment_terms=data.get('payment_terms', 30),
            notes=data.get('notes', '').strip(),
            is_active=data.get('is_active', True),
            created_by=current_user.id
        )
        
        db.session.add(customer)
        db.session.flush()  # Get customer ID
        
        # Add address if provided
        address_data = data.get('address')
        if address_data:
            address = create_customer_address(customer.id, address_data)
            if isinstance(address, tuple):  # Error response
                return address
        
        # Add contact if provided
        contact_data = data.get('contact')
        if contact_data:
            contact = create_customer_contact(customer.id, contact_data)
            if isinstance(contact, tuple):  # Error response
                return contact
        
        db.session.commit()
        
        return format_success_response(
            'Klant succesvol aangemaakt',
            {'customer': customer.to_dict(include_relations=True)},
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Create customer error: {str(e)}")
        return format_error_response('Klant aanmaken gefaald', status_code=500)

@customers_bp.route('/<customer_id>', methods=['PUT'])
@jwt_required()
@require_permission('manage_customers')
@require_same_organization
@audit_log('customers', 'UPDATE')
def update_customer(customer_id, current_organization_id):
    """Update customer"""
    try:
        customer = Customer.query.filter_by(
            id=customer_id,
            organization_id=current_organization_id
        ).first()
        
        if not customer:
            return format_error_response('Klant niet gevonden', status_code=404)
        
        data = request.get_json()
        if not data:
            return format_error_response('Geen data ontvangen')
        
        # Update fields
        if 'company_name' in data:
            company_name = data['company_name'].strip()
            if not company_name:
                return format_error_response('Bedrijfsnaam is vereist')
            customer.company_name = company_name
        
        if 'contact_person' in data:
            customer.contact_person = data['contact_person'].strip()
        
        if 'email' in data:
            email = data['email'].strip()
            if email and not validate_email(email):
                return format_error_response('Ongeldig email adres')
            customer.email = email
        
        if 'phone' in data:
            phone = data['phone'].strip()
            if phone and not validate_phone(phone):
                return format_error_response('Ongeldig telefoonnummer')
            customer.phone = phone
        
        if 'btw_number' in data:
            btw_number = data['btw_number'].strip()
            if btw_number and not validate_btw_number(btw_number):
                return format_error_response('Ongeldig BTW nummer')
            customer.btw_number = btw_number
        
        if 'payment_terms' in data:
            try:
                customer.payment_terms = int(data['payment_terms'])
            except (ValueError, TypeError):
                return format_error_response('Ongeldige betalingstermijn')
        
        if 'notes' in data:
            customer.notes = data['notes'].strip()
        
        if 'is_active' in data:
            customer.is_active = bool(data['is_active'])
        
        db.session.commit()
        
        return format_success_response(
            'Klant succesvol bijgewerkt',
            {'customer': customer.to_dict(include_relations=True)}
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update customer error: {str(e)}")
        return format_error_response('Klant bijwerken gefaald', status_code=500)

@customers_bp.route('/<customer_id>', methods=['DELETE'])
@jwt_required()
@require_permission('manage_customers')
@require_same_organization
@audit_log('customers', 'DELETE')
def delete_customer(customer_id, current_organization_id):
    """Delete customer (soft delete by deactivating)"""
    try:
        customer = Customer.query.filter_by(
            id=customer_id,
            organization_id=current_organization_id
        ).first()
        
        if not customer:
            return format_error_response('Klant niet gevonden', status_code=404)
        
        # Check if customer has orders
        if customer.orders:
            return format_error_response(
                'Klant kan niet worden verwijderd omdat er opdrachten aan gekoppeld zijn'
            )
        
        # Soft delete by deactivating
        customer.is_active = False
        db.session.commit()
        
        return format_success_response('Klant succesvol gedeactiveerd')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Delete customer error: {str(e)}")
        return format_error_response('Klant verwijderen gefaald', status_code=500)

@customers_bp.route('/<customer_id>/addresses', methods=['POST'])
@jwt_required()
@require_permission('manage_customers')
@require_same_organization
def add_customer_address(customer_id, current_organization_id):
    """Add address to customer"""
    try:
        customer = Customer.query.filter_by(
            id=customer_id,
            organization_id=current_organization_id
        ).first()
        
        if not customer:
            return format_error_response('Klant niet gevonden', status_code=404)
        
        data = request.get_json()
        if not data:
            return format_error_response('Geen data ontvangen')
        
        address = create_customer_address(customer_id, data)
        if isinstance(address, tuple):  # Error response
            return address
        
        db.session.commit()
        
        return format_success_response(
            'Adres succesvol toegevoegd',
            {'address': address.to_dict()},
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Add customer address error: {str(e)}")
        return format_error_response('Adres toevoegen gefaald', status_code=500)

@customers_bp.route('/<customer_id>/contacts', methods=['POST'])
@jwt_required()
@require_permission('manage_customers')
@require_same_organization
def add_customer_contact(customer_id, current_organization_id):
    """Add contact to customer"""
    try:
        customer = Customer.query.filter_by(
            id=customer_id,
            organization_id=current_organization_id
        ).first()
        
        if not customer:
            return format_error_response('Klant niet gevonden', status_code=404)
        
        data = request.get_json()
        if not data:
            return format_error_response('Geen data ontvangen')
        
        contact = create_customer_contact(customer_id, data)
        if isinstance(contact, tuple):  # Error response
            return contact
        
        db.session.commit()
        
        return format_success_response(
            'Contact succesvol toegevoegd',
            {'contact': contact.to_dict()},
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Add customer contact error: {str(e)}")
        return format_error_response('Contact toevoegen gefaald', status_code=500)

def create_customer_address(customer_id, address_data):
    """Helper function to create customer address"""
    try:
        # Validate required fields
        street = address_data.get('street', '').strip()
        postal_code = address_data.get('postal_code', '').strip()
        city = address_data.get('city', '').strip()
        address_type = address_data.get('address_type', 'both')
        
        if not street or not postal_code or not city:
            return format_error_response('Straat, postcode en plaats zijn vereist')
        
        if address_type not in ['billing', 'delivery', 'both']:
            return format_error_response('Ongeldig adrestype')
        
        if not validate_postal_code(postal_code):
            return format_error_response('Ongeldige postcode')
        
        # Create address
        address = CustomerAddress(
            customer_id=customer_id,
            address_type=address_type,
            street=street,
            postal_code=postal_code,
            city=city,
            country=address_data.get('country', 'Nederland'),
            is_primary=address_data.get('is_primary', True)
        )
        
        # If this is primary, unset other primary addresses
        if address.is_primary:
            CustomerAddress.query.filter_by(
                customer_id=customer_id,
                is_primary=True
            ).update({'is_primary': False})
        
        db.session.add(address)
        return address
        
    except Exception as e:
        return format_error_response(f'Adres aanmaken gefaald: {str(e)}', status_code=500)

def create_customer_contact(customer_id, contact_data):
    """Helper function to create customer contact"""
    try:
        # Validate required fields
        first_name = contact_data.get('first_name', '').strip()
        last_name = contact_data.get('last_name', '').strip()
        
        if not first_name or not last_name:
            return format_error_response('Voornaam en achternaam zijn vereist')
        
        # Validate optional fields
        email = contact_data.get('email', '').strip()
        if email and not validate_email(email):
            return format_error_response('Ongeldig email adres')
        
        phone = contact_data.get('phone', '').strip()
        if phone and not validate_phone(phone):
            return format_error_response('Ongeldig telefoonnummer')
        
        mobile = contact_data.get('mobile', '').strip()
        if mobile and not validate_phone(mobile):
            return format_error_response('Ongeldig mobiel nummer')
        
        # Create contact
        contact = CustomerContact(
            customer_id=customer_id,
            first_name=first_name,
            last_name=last_name,
            title=contact_data.get('title', '').strip(),
            email=email,
            phone=phone,
            mobile=mobile,
            department=contact_data.get('department', '').strip(),
            is_primary=contact_data.get('is_primary', True)
        )
        
        # If this is primary, unset other primary contacts
        if contact.is_primary:
            CustomerContact.query.filter_by(
                customer_id=customer_id,
                is_primary=True
            ).update({'is_primary': False})
        
        db.session.add(contact)
        return contact
        
    except Exception as e:
        return format_error_response(f'Contact aanmaken gefaald: {str(e)}', status_code=500)

