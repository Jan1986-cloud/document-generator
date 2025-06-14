"""
Google Docs and PDF generation service
"""
import os
import json
import tempfile
from typing import Dict, List, Any, Optional
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
import io
import re
from decimal import Decimal

class GoogleDocsService:
    """Service for interacting with Google Docs and Drive APIs"""
    
    # Template document IDs
    TEMPLATE_IDS = {
        'offerte': '1rOGgVCxwBTkJoA7fxNJm4TTdF5gt_322EO3vjQh9z1w',
        'factuur': '1C4g3E4JYEYAPydKtQVzswZe-Unpzp18bsTAtZ4JKuhs',
        'factuur_gecombineerd': '1zU9w9q7MB4KgrBh4-ETrYqm9qqfjltrZaNI98onlyOw',
        'werkbon': '1ZEX2wr7ROj69yq78fPTOQ0Gljx4S-Y2BpbuNIoa1iBc'
    }
    
    # Output folder ID
    OUTPUT_FOLDER_ID = '1Ug14PibLMQKU8IIoUGTGaLw-ZzvJRhQX'
    
    # Maximum loop items (configurable)
    MAX_LOOP_ITEMS = 10
    
    def __init__(self, credentials_path: str = None):
        """Initialize Google Docs service with credentials"""
        self.credentials_path = credentials_path or os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        self.scopes = [
            'https://www.googleapis.com/auth/documents',
            'https://www.googleapis.com/auth/drive'
        ]
        self.docs_service = None
        self.drive_service = None
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize Google API services"""
        try:
            if self.credentials_path and os.path.exists(self.credentials_path):
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path, scopes=self.scopes
                )
            else:
                # For development, you might want to use default credentials
                from google.auth import default
                credentials, _ = default(scopes=self.scopes)
            
            self.docs_service = build('docs', 'v1', credentials=credentials)
            self.drive_service = build('drive', 'v3', credentials=credentials)
            
        except Exception as e:
            print(f"Failed to initialize Google services: {e}")
            # For development without credentials, create mock services
            self.docs_service = None
            self.drive_service = None
    
    def generate_document(self, template_type: str, data: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate a document from template with provided data
        
        Args:
            template_type: Type of template ('offerte', 'factuur', etc.)
            data: Dictionary containing all the data to fill in the template
            
        Returns:
            Dictionary with document_id, pdf_url, and other metadata
        """
        if template_type not in self.TEMPLATE_IDS:
            raise ValueError(f"Unknown template type: {template_type}")
        
        template_id = self.TEMPLATE_IDS[template_type]
        
        try:
            # Step 1: Copy the template
            document_id = self._copy_template(template_id, data)
            
            # Step 2: Replace placeholders with actual data
            self._replace_placeholders(document_id, data)
            
            # Step 3: Export as PDF
            pdf_url = self._export_as_pdf(document_id, data)
            
            return {
                'document_id': document_id,
                'pdf_url': pdf_url,
                'template_type': template_type,
                'created_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Document generation failed: {str(e)}")
    
    def _copy_template(self, template_id: str, data: Dict[str, Any]) -> str:
        """Copy template document and return new document ID"""
        if not self.drive_service:
            # Mock for development
            return f"mock_doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # Generate document name
            doc_name = self._generate_document_name(data)
            
            # Copy the template
            copy_request = {
                'name': doc_name,
                'parents': [self.OUTPUT_FOLDER_ID]
            }
            
            copied_file = self.drive_service.files().copy(
                fileId=template_id,
                body=copy_request
            ).execute()
            
            return copied_file['id']
            
        except HttpError as e:
            raise Exception(f"Failed to copy template: {e}")
    
    def _generate_document_name(self, data: Dict[str, Any]) -> str:
        """Generate a meaningful document name"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Try to get meaningful identifiers from data
        doc_number = data.get('document_number', '')
        customer_name = data.get('customer', {}).get('company_name', 'Unknown')
        
        # Sanitize customer name for filename
        customer_name = re.sub(r'[^\w\s-]', '', customer_name)[:20]
        
        if doc_number:
            return f"{doc_number}_{customer_name}_{timestamp}"
        else:
            return f"Document_{customer_name}_{timestamp}"
    
    def _replace_placeholders(self, document_id: str, data: Dict[str, Any]):
        """Replace all placeholders in the document with actual data"""
        if not self.docs_service:
            # Mock for development
            print(f"Mock: Replacing placeholders in {document_id}")
            return
        
        try:
            # Get document content
            document = self.docs_service.documents().get(documentId=document_id).execute()
            
            # Prepare replacement requests
            requests = []
            
            # Basic replacements
            basic_replacements = self._prepare_basic_replacements(data)
            for placeholder, value in basic_replacements.items():
                requests.append({
                    'replaceAllText': {
                        'containsText': {
                            'text': placeholder,
                            'matchCase': False
                        },
                        'replaceText': str(value)
                    }
                })
            
            # Handle loop items (products/services)
            loop_requests = self._prepare_loop_replacements(data)
            requests.extend(loop_requests)
            
            # Execute all replacements
            if requests:
                self.docs_service.documents().batchUpdate(
                    documentId=document_id,
                    body={'requests': requests}
                ).execute()
                
        except HttpError as e:
            raise Exception(f"Failed to replace placeholders: {e}")
    
    def _prepare_basic_replacements(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Prepare basic placeholder replacements"""
        replacements = {}
        
        # Customer information
        customer = data.get('customer', {})
        replacements.update({
            '[KlantNaam]': customer.get('company_name', ''),
            '[KlantAdres]': customer.get('address', {}).get('street', ''),
            '[KlantPostcode]': customer.get('address', {}).get('postal_code', ''),
            '[KlantPlaats]': customer.get('address', {}).get('city', ''),
            '[KlantEmail]': customer.get('email', ''),
            '[KlantTelefoon]': customer.get('phone', ''),
            '[ContactPersoon]': customer.get('contact_person', ''),
        })
        
        # Document information
        replacements.update({
            '[DocumentNummer]': data.get('document_number', ''),
            '[Datum]': data.get('date', datetime.now().strftime('%d-%m-%Y')),
            '[Omschrijving]': data.get('description', ''),
            '[Notities]': data.get('notes', ''),
        })
        
        # Order information
        order = data.get('order', {})
        replacements.update({
            '[OpdrachtNummer]': order.get('order_number', ''),
            '[OpdrachtDatum]': order.get('order_date', ''),
            '[Status]': order.get('status', ''),
        })
        
        # Financial totals
        totals = data.get('totals', {})
        replacements.update({
            '[SubtotaalExclBTW]': self._format_currency(totals.get('subtotal_excl_btw', 0)),
            '[TotaalBTW]': self._format_currency(totals.get('total_btw', 0)),
            '[TotaalInclBTW]': self._format_currency(totals.get('total_incl_btw', 0)),
        })
        
        # Organization information (from settings)
        organization = data.get('organization', {})
        replacements.update({
            '[BedrijfNaam]': organization.get('name', ''),
            '[BedrijfAdres]': organization.get('address', ''),
            '[BedrijfPostcode]': organization.get('postal_code', ''),
            '[BedrijfPlaats]': organization.get('city', ''),
            '[BedrijfTelefoon]': organization.get('phone', ''),
            '[BedrijfEmail]': organization.get('email', ''),
            '[BedrijfWebsite]': organization.get('website', ''),
            '[KvKNummer]': organization.get('kvk_number', ''),
            '[BTWNummer]': organization.get('btw_number', ''),
            '[IBAN]': organization.get('iban', ''),
        })
        
        return replacements
    
    def _prepare_loop_replacements(self, data: Dict[str, Any]) -> List[Dict]:
        """Prepare replacements for loop items (products/services)"""
        requests = []
        
        # Get items from data
        items = data.get('items', [])
        
        # Limit items to prevent document bloat
        items = items[:self.MAX_LOOP_ITEMS]
        
        # Prepare loop replacements
        for i, item in enumerate(items, 1):
            item_replacements = {
                f'[LoopART_Aantal{i}]': str(item.get('quantity', '')),
                f'[LoopART_Omschrijving{i}]': item.get('description', ''),
                f'[LoopART_Eenheid{i}]': item.get('unit', ''),
                f'[LoopART_PrijsExclBTW{i}]': self._format_currency(item.get('unit_price_excl_btw', 0)),
                f'[LoopART_BTWPercentage{i}]': f"{item.get('btw_percentage', 0)}%",
                f'[LoopART_TotaalExclBTW{i}]': self._format_currency(item.get('total_excl_btw', 0)),
                f'[LoopART_TotaalInclBTW{i}]': self._format_currency(item.get('total_incl_btw', 0)),
                f'[LoopART_Notities{i}]': item.get('delivery_notes', ''),
            }
            
            # Add replacement requests for this item
            for placeholder, value in item_replacements.items():
                requests.append({
                    'replaceAllText': {
                        'containsText': {
                            'text': placeholder,
                            'matchCase': False
                        },
                        'replaceText': str(value)
                    }
                })
        
        # Clear unused loop placeholders
        for i in range(len(items) + 1, self.MAX_LOOP_ITEMS + 1):
            empty_replacements = {
                f'[LoopART_Aantal{i}]': '',
                f'[LoopART_Omschrijving{i}]': '',
                f'[LoopART_Eenheid{i}]': '',
                f'[LoopART_PrijsExclBTW{i}]': '',
                f'[LoopART_BTWPercentage{i}]': '',
                f'[LoopART_TotaalExclBTW{i}]': '',
                f'[LoopART_TotaalInclBTW{i}]': '',
                f'[LoopART_Notities{i}]': '',
            }
            
            for placeholder, value in empty_replacements.items():
                requests.append({
                    'replaceAllText': {
                        'containsText': {
                            'text': placeholder,
                            'matchCase': False
                        },
                        'replaceText': value
                    }
                })
        
        return requests
    
    def _format_currency(self, amount: Any) -> str:
        """Format amount as currency"""
        try:
            if isinstance(amount, (int, float, Decimal)):
                return f"€ {amount:.2f}".replace('.', ',')
            return str(amount)
        except:
            return "€ 0,00"
    
    def _export_as_pdf(self, document_id: str, data: Dict[str, Any]) -> str:
        """Export document as PDF and return download URL"""
        if not self.drive_service:
            # Mock for development
            return f"https://mock-pdf-url.com/{document_id}.pdf"
        
        try:
            # Export as PDF
            request = self.drive_service.files().export_media(
                fileId=document_id,
                mimeType='application/pdf'
            )
            
            # Download PDF content
            pdf_content = io.BytesIO()
            downloader = MediaIoBaseDownload(pdf_content, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            # Upload PDF to Drive
            pdf_name = f"{self._generate_document_name(data)}.pdf"
            pdf_metadata = {
                'name': pdf_name,
                'parents': [self.OUTPUT_FOLDER_ID]
            }
            
            pdf_content.seek(0)
            media = MediaFileUpload(
                io.BytesIO(pdf_content.getvalue()),
                mimetype='application/pdf',
                resumable=True
            )
            
            pdf_file = self.drive_service.files().create(
                body=pdf_metadata,
                media_body=media,
                fields='id,webViewLink'
            ).execute()
            
            return pdf_file.get('webViewLink', '')
            
        except HttpError as e:
            raise Exception(f"Failed to export PDF: {e}")
    
    def get_template_info(self, template_type: str) -> Dict[str, Any]:
        """Get information about a template"""
        if template_type not in self.TEMPLATE_IDS:
            raise ValueError(f"Unknown template type: {template_type}")
        
        template_id = self.TEMPLATE_IDS[template_type]
        
        if not self.drive_service:
            # Mock for development
            return {
                'id': template_id,
                'name': f"Template {template_type}",
                'type': template_type,
                'placeholders': self._get_template_placeholders(template_type)
            }
        
        try:
            file_info = self.drive_service.files().get(
                fileId=template_id,
                fields='id,name,modifiedTime,size'
            ).execute()
            
            return {
                'id': template_id,
                'name': file_info.get('name', ''),
                'type': template_type,
                'modified_time': file_info.get('modifiedTime', ''),
                'size': file_info.get('size', ''),
                'placeholders': self._get_template_placeholders(template_type)
            }
            
        except HttpError as e:
            raise Exception(f"Failed to get template info: {e}")
    
    def _get_template_placeholders(self, template_type: str) -> List[str]:
        """Get list of placeholders for a template type"""
        # Common placeholders for all templates
        common_placeholders = [
            '[KlantNaam]', '[KlantAdres]', '[KlantPostcode]', '[KlantPlaats]',
            '[KlantEmail]', '[KlantTelefoon]', '[ContactPersoon]',
            '[DocumentNummer]', '[Datum]', '[Omschrijving]', '[Notities]',
            '[BedrijfNaam]', '[BedrijfAdres]', '[BedrijfPostcode]', '[BedrijfPlaats]',
            '[BedrijfTelefoon]', '[BedrijfEmail]', '[BedrijfWebsite]',
            '[KvKNummer]', '[BTWNummer]', '[IBAN]'
        ]
        
        # Loop placeholders for items
        loop_placeholders = []
        for i in range(1, self.MAX_LOOP_ITEMS + 1):
            loop_placeholders.extend([
                f'[LoopART_Aantal{i}]',
                f'[LoopART_Omschrijving{i}]',
                f'[LoopART_Eenheid{i}]',
                f'[LoopART_PrijsExclBTW{i}]',
                f'[LoopART_BTWPercentage{i}]',
                f'[LoopART_TotaalExclBTW{i}]',
                f'[LoopART_TotaalInclBTW{i}]',
                f'[LoopART_Notities{i}]'
            ])
        
        # Financial placeholders
        financial_placeholders = [
            '[SubtotaalExclBTW]', '[TotaalBTW]', '[TotaalInclBTW]'
        ]
        
        # Template-specific placeholders
        template_specific = {
            'offerte': ['[GeldigTot]', '[OfferteNummer]'],
            'factuur': ['[FactuurNummer]', '[Vervaldatum]', '[BetalingsTermijn]'],
            'factuur_gecombineerd': ['[FactuurNummer]', '[Vervaldatum]', '[BetalingsTermijn]'],
            'werkbon': ['[WerkbonNummer]', '[Technicus]', '[Uitgevoerd]']
        }
        
        all_placeholders = (
            common_placeholders + 
            loop_placeholders + 
            financial_placeholders + 
            template_specific.get(template_type, [])
        )
        
        return sorted(list(set(all_placeholders)))
    
    def validate_data(self, template_type: str, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Validate data for document generation"""
        errors = []
        warnings = []
        
        # Required fields validation
        required_fields = {
            'customer': ['company_name'],
            'document_number': None,
            'date': None
        }
        
        for field, subfields in required_fields.items():
            if field not in data or not data[field]:
                errors.append(f"Missing required field: {field}")
            elif subfields:
                for subfield in subfields:
                    if subfield not in data[field] or not data[field][subfield]:
                        errors.append(f"Missing required field: {field}.{subfield}")
        
        # Items validation
        items = data.get('items', [])
        if not items:
            warnings.append("No items provided - document will be empty")
        else:
            for i, item in enumerate(items):
                if not item.get('description'):
                    errors.append(f"Item {i+1}: Missing description")
                if not item.get('quantity'):
                    warnings.append(f"Item {i+1}: Missing quantity")
        
        # Template-specific validation
        if template_type == 'factuur' and not data.get('totals', {}).get('total_incl_btw'):
            warnings.append("No total amount specified for invoice")
        
        return {
            'errors': errors,
            'warnings': warnings,
            'is_valid': len(errors) == 0
        }


# Utility functions for document generation
def prepare_document_data(order_data: Dict[str, Any], organization_data: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare data for document generation from order and organization data"""
    
    # Calculate totals
    items = order_data.get('items', [])
    subtotal_excl_btw = sum(item.get('total_excl_btw', 0) for item in items)
    total_btw = sum(item.get('total_btw', 0) for item in items)
    total_incl_btw = subtotal_excl_btw + total_btw
    
    return {
        'customer': order_data.get('customer', {}),
        'order': {
            'order_number': order_data.get('order_number', ''),
            'order_date': order_data.get('order_date', ''),
            'status': order_data.get('status', '')
        },
        'document_number': order_data.get('document_number', ''),
        'date': order_data.get('date', datetime.now().strftime('%d-%m-%Y')),
        'description': order_data.get('description', ''),
        'notes': order_data.get('notes', ''),
        'items': items,
        'totals': {
            'subtotal_excl_btw': subtotal_excl_btw,
            'total_btw': total_btw,
            'total_incl_btw': total_incl_btw
        },
        'organization': organization_data
    }


def generate_document_number(template_type: str, organization_id: str) -> str:
    """Generate a unique document number"""
    from datetime import datetime
    
    # Get current year and date
    now = datetime.now()
    year = now.year
    date_str = now.strftime('%Y%m%d')
    
    # Template prefixes
    prefixes = {
        'offerte': 'OFF',
        'factuur': 'FACT',
        'factuur_gecombineerd': 'FACT',
        'werkbon': 'WB'
    }
    
    prefix = prefixes.get(template_type, 'DOC')
    
    # TODO: In production, get next sequence number from database
    # For now, use timestamp-based number
    sequence = now.strftime('%H%M%S')
    
    return f"{prefix}-{year}-{sequence}"

