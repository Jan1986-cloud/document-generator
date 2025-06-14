"""
Validation utilities
"""
import re
from typing import Optional

def validate_email(email: str) -> bool:
    """Validate email address format"""
    if not email or not isinstance(email, str):
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))

def validate_password(password: str) -> bool:
    """Validate password strength"""
    if not password or not isinstance(password, str):
        return False
    
    # Minimum 8 characters
    return len(password) >= 8

def validate_phone(phone: str) -> bool:
    """Validate phone number format"""
    if not phone or not isinstance(phone, str):
        return False
    
    # Remove spaces, dashes, and parentheses
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    
    # Check if it contains only digits and optional + at start
    pattern = r'^\+?[0-9]{8,15}$'
    return bool(re.match(pattern, cleaned))

def validate_postal_code(postal_code: str, country: str = 'NL') -> bool:
    """Validate postal code format"""
    if not postal_code or not isinstance(postal_code, str):
        return False
    
    postal_code = postal_code.strip().upper()
    
    if country == 'NL':
        # Dutch postal code: 1234 AB
        pattern = r'^[0-9]{4}\s?[A-Z]{2}$'
        return bool(re.match(pattern, postal_code))
    
    # Generic validation for other countries
    return len(postal_code) >= 3

def validate_btw_number(btw_number: str, country: str = 'NL') -> bool:
    """Validate BTW/VAT number format"""
    if not btw_number or not isinstance(btw_number, str):
        return False
    
    btw_number = btw_number.strip().upper()
    
    if country == 'NL':
        # Dutch BTW number: NL123456789B01
        pattern = r'^NL[0-9]{9}B[0-9]{2}$'
        return bool(re.match(pattern, btw_number))
    
    # Generic validation for other countries
    return len(btw_number) >= 8

def validate_kvk_number(kvk_number: str) -> bool:
    """Validate KvK number format"""
    if not kvk_number or not isinstance(kvk_number, str):
        return False
    
    # Remove spaces and check if it's 8 digits
    cleaned = re.sub(r'\s', '', kvk_number)
    pattern = r'^[0-9]{8}$'
    return bool(re.match(pattern, cleaned))

def validate_iban(iban: str) -> bool:
    """Validate IBAN format"""
    if not iban or not isinstance(iban, str):
        return False
    
    # Remove spaces and convert to uppercase
    iban = re.sub(r'\s', '', iban.upper())
    
    # Basic IBAN format check (2 letters + 2 digits + up to 30 alphanumeric)
    pattern = r'^[A-Z]{2}[0-9]{2}[A-Z0-9]{1,30}$'
    if not re.match(pattern, iban):
        return False
    
    # IBAN checksum validation (simplified)
    # Move first 4 characters to end
    rearranged = iban[4:] + iban[:4]
    
    # Replace letters with numbers (A=10, B=11, etc.)
    numeric = ''
    for char in rearranged:
        if char.isalpha():
            numeric += str(ord(char) - ord('A') + 10)
        else:
            numeric += char
    
    # Check if mod 97 equals 1
    try:
        return int(numeric) % 97 == 1
    except ValueError:
        return False

def validate_article_number(article_number: str) -> bool:
    """Validate article number format"""
    if not article_number or not isinstance(article_number, str):
        return False
    
    # Allow alphanumeric characters, dashes, and underscores
    pattern = r'^[A-Za-z0-9\-_]{1,50}$'
    return bool(re.match(pattern, article_number.strip()))

def validate_customer_number(customer_number: str) -> bool:
    """Validate customer number format"""
    if not customer_number or not isinstance(customer_number, str):
        return False
    
    # Allow alphanumeric characters, dashes, and underscores
    pattern = r'^[A-Za-z0-9\-_]{1,20}$'
    return bool(re.match(pattern, customer_number.strip()))

def validate_order_number(order_number: str) -> bool:
    """Validate order number format"""
    if not order_number or not isinstance(order_number, str):
        return False
    
    # Allow alphanumeric characters, dashes, and underscores
    pattern = r'^[A-Za-z0-9\-_]{1,50}$'
    return bool(re.match(pattern, order_number.strip()))

def validate_document_number(document_number: str) -> bool:
    """Validate document number format"""
    if not document_number or not isinstance(document_number, str):
        return False
    
    # Allow alphanumeric characters, dashes, and underscores
    pattern = r'^[A-Za-z0-9\-_]{1,50}$'
    return bool(re.match(pattern, document_number.strip()))

def validate_url(url: str) -> bool:
    """Validate URL format"""
    if not url or not isinstance(url, str):
        return False
    
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(pattern, url.strip()))

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    if not filename or not isinstance(filename, str):
        return 'untitled'
    
    # Remove or replace unsafe characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    sanitized = re.sub(r'\s+', '_', sanitized)
    sanitized = sanitized.strip('._')
    
    # Limit length
    if len(sanitized) > 100:
        name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
        sanitized = name[:95] + ('.' + ext if ext else '')
    
    return sanitized or 'untitled'

def validate_decimal(value: str, max_digits: int = 10, decimal_places: int = 2) -> bool:
    """Validate decimal number format"""
    if not value or not isinstance(value, str):
        return False
    
    try:
        from decimal import Decimal, InvalidOperation
        decimal_value = Decimal(value.strip())
        
        # Check if it fits within the specified precision
        sign, digits, exponent = decimal_value.as_tuple()
        
        if exponent < -decimal_places:
            return False
        
        total_digits = len(digits)
        if total_digits > max_digits:
            return False
        
        return True
    except (InvalidOperation, ValueError):
        return False

