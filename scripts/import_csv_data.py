#!/usr/bin/env python3
"""
Document Generatie App - CSV Data Import Script
Importeert voorbeelddata uit CSV bestanden naar de database
"""

import csv
import os
import sys
import uuid
import re
from decimal import Decimal
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import argparse

class CSVDataImporter:
    def __init__(self, database_url):
        """Initialiseer de CSV data importer"""
        self.database_url = database_url
        self.conn = None
        self.organization_id = None
        
    def connect(self):
        """Maak verbinding met de database"""
        try:
            self.conn = psycopg2.connect(self.database_url)
            self.conn.autocommit = False
            print("✅ Database verbinding succesvol")
        except Exception as e:
            print(f"❌ Database verbinding gefaald: {e}")
            sys.exit(1)
    
    def disconnect(self):
        """Sluit database verbinding"""
        if self.conn:
            self.conn.close()
            print("✅ Database verbinding gesloten")
    
    def get_or_create_organization(self, org_name="Demo Bedrijf"):
        """Haal organisatie op of maak nieuwe aan"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Zoek bestaande organisatie
            cur.execute("SELECT id FROM organizations WHERE name = %s", (org_name,))
            result = cur.fetchone()
            
            if result:
                self.organization_id = result['id']
                print(f"✅ Bestaande organisatie gevonden: {org_name}")
            else:
                # Maak nieuwe organisatie aan
                org_id = str(uuid.uuid4())
                cur.execute("""
                    INSERT INTO organizations (id, name, address, postal_code, city, phone, email, website, kvk_number, btw_number, iban)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    org_id, org_name, "Voorbeeldstraat 123", "1234 AB", "Amsterdam",
                    "020-1234567", "info@demobedrijf.nl", "www.demobedrijf.nl",
                    "12345678", "NL123456789B01", "NL12ABCD0123456789"
                ))
                self.organization_id = org_id
                print(f"✅ Nieuwe organisatie aangemaakt: {org_name}")
            
            self.conn.commit()
    
    def clean_price(self, price_str):
        """Maak prijs string schoon en converteer naar Decimal"""
        if not price_str or price_str.strip() == "":
            return Decimal('0.00')
        
        # Verwijder euro teken, spaties en vervang komma door punt
        cleaned = re.sub(r'[€\s]', '', price_str)
        cleaned = cleaned.replace(',', '.')
        
        try:
            return Decimal(cleaned)
        except:
            return Decimal('0.00')
    
    def import_product_categories(self):
        """Maak standaard product categorieën aan"""
        categories = [
            ("Montage", "Montage werkzaamheden"),
            ("Materiaal", "Materialen en onderdelen"),
            ("Abonnementen", "Service abonnementen"),
            ("Apparatuur", "Apparatuur en systemen"),
            ("Transport", "Transport en logistiek")
        ]
        
        with self.conn.cursor() as cur:
            for name, description in categories:
                # Controleer of categorie al bestaat
                cur.execute("""
                    SELECT id FROM product_categories 
                    WHERE organization_id = %s AND name = %s
                """, (self.organization_id, name))
                
                if not cur.fetchone():
                    cur.execute("""
                        INSERT INTO product_categories (id, organization_id, name, description)
                        VALUES (%s, %s, %s, %s)
                    """, (str(uuid.uuid4()), self.organization_id, name, description))
        
        self.conn.commit()
        print("✅ Product categorieën aangemaakt")
    
    def get_category_id(self, product_name):
        """Bepaal categorie ID op basis van product naam"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Eenvoudige categorisatie op basis van keywords
            if any(word in product_name.lower() for word in ['monteur', 'reistijd']):
                category_name = 'Montage'
            elif any(word in product_name.lower() for word in ['abonnement']):
                category_name = 'Abonnementen'
            elif any(word in product_name.lower() for word in ['materiaal', 'kabel', 'schroef', 'plug']):
                category_name = 'Materiaal'
            elif any(word in product_name.lower() for word in ['kubie', 'omvormer', 'zaptec', 'pytess', 'solis']):
                category_name = 'Apparatuur'
            elif any(word in product_name.lower() for word in ['lift', 'steiger', 'transport']):
                category_name = 'Transport'
            else:
                category_name = 'Materiaal'  # Default
            
            cur.execute("""
                SELECT id FROM product_categories 
                WHERE organization_id = %s AND name = %s
            """, (self.organization_id, category_name))
            
            result = cur.fetchone()
            return result['id'] if result else None
    
    def import_products_from_csv(self, csv_file_path):
        """Importeer producten uit CSV bestand"""
        if not os.path.exists(csv_file_path):
            print(f"❌ CSV bestand niet gevonden: {csv_file_path}")
            return
        
        products_imported = 0
        
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            # Detecteer delimiter
            sample = file.read(1024)
            file.seek(0)
            delimiter = ',' if sample.count(',') > sample.count(';') else ';'
            
            reader = csv.DictReader(file, delimiter=delimiter)
            
            with self.conn.cursor() as cur:
                for row in reader:
                    # Skip lege rijen
                    if not row.get('Product', '').strip():
                        continue
                    
                    # Extract data
                    article_number = row.get('Artikelnummer', '').strip()
                    product_name = row.get('Product', '').strip()
                    description = row.get('Omschrijving', '').strip()
                    unit = row.get('Eenheid', 'stuk').strip() or 'stuk'
                    price_incl_str = row.get('Prijs incl. BTW', '0')
                    price_excl_str = row.get('Prijs excl BTW', '0')
                    datasheet_url = row.get('Data sheet', '').strip()
                    photo_url = row.get('Foto', '').strip()
                    
                    # Clean prices
                    price_incl_btw = self.clean_price(price_incl_str)
                    price_excl_btw = self.clean_price(price_excl_str)
                    
                    # Calculate BTW percentage
                    if price_excl_btw > 0:
                        btw_percentage = ((price_incl_btw - price_excl_btw) / price_excl_btw * 100).quantize(Decimal('0.01'))
                    else:
                        btw_percentage = Decimal('21.00')
                    
                    # Get category
                    category_id = self.get_category_id(product_name)
                    
                    # Check if product already exists
                    cur.execute("""
                        SELECT id FROM products 
                        WHERE organization_id = %s AND (name = %s OR article_number = %s)
                    """, (self.organization_id, product_name, article_number))
                    
                    if cur.fetchone():
                        continue  # Skip existing products
                    
                    # Insert product
                    product_id = str(uuid.uuid4())
                    cur.execute("""
                        INSERT INTO products (
                            id, organization_id, category_id, article_number, name, description,
                            unit, price_excl_btw, price_incl_btw, btw_percentage, is_active
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        product_id, self.organization_id, category_id, article_number or None,
                        product_name, description, unit, price_excl_btw, price_incl_btw,
                        btw_percentage, True
                    ))
                    
                    # Add attachments if available
                    if datasheet_url:
                        cur.execute("""
                            INSERT INTO product_attachments (id, product_id, file_name, file_url, attachment_type)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (str(uuid.uuid4()), product_id, 'Datasheet', datasheet_url, 'datasheet'))
                    
                    if photo_url:
                        cur.execute("""
                            INSERT INTO product_attachments (id, product_id, file_name, file_url, attachment_type)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (str(uuid.uuid4()), product_id, 'Product foto', photo_url, 'photo'))
                    
                    products_imported += 1
        
        self.conn.commit()
        print(f"✅ {products_imported} producten geïmporteerd uit {csv_file_path}")
    
    def create_demo_customers(self):
        """Maak demo klanten aan"""
        customers = [
            {
                'company_name': 'Weterings B.V.',
                'contact_person': 'Jan Weterings',
                'email': 'jan@weterings.nl',
                'phone': '030-1234567',
                'street': 'Industrieweg 45',
                'postal_code': '3542 AD',
                'city': 'Utrecht'
            },
            {
                'company_name': 'F. Smit Panelen',
                'contact_person': 'Frank Smit',
                'email': 'frank@smitpanelen.nl',
                'phone': '020-9876543',
                'street': 'Zonnelaan 123',
                'postal_code': '1012 AB',
                'city': 'Amsterdam'
            },
            {
                'company_name': 'Groene Energie Solutions',
                'contact_person': 'Maria van der Berg',
                'email': 'maria@groeneenergie.nl',
                'phone': '010-5555666',
                'street': 'Duurzaamheidsstraat 78',
                'postal_code': '3011 CD',
                'city': 'Rotterdam'
            }
        ]
        
        with self.conn.cursor() as cur:
            for i, customer_data in enumerate(customers, 1):
                # Check if customer exists
                cur.execute("""
                    SELECT id FROM customers 
                    WHERE organization_id = %s AND company_name = %s
                """, (self.organization_id, customer_data['company_name']))
                
                if cur.fetchone():
                    continue
                
                # Create customer
                customer_id = str(uuid.uuid4())
                customer_number = f"{i:06d}"
                
                cur.execute("""
                    INSERT INTO customers (
                        id, organization_id, customer_number, company_name, contact_person,
                        email, phone, payment_terms, is_active
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    customer_id, self.organization_id, customer_number,
                    customer_data['company_name'], customer_data['contact_person'],
                    customer_data['email'], customer_data['phone'], 30, True
                ))
                
                # Create address
                cur.execute("""
                    INSERT INTO customer_addresses (
                        id, customer_id, address_type, street, postal_code, city, is_primary
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    str(uuid.uuid4()), customer_id, 'both',
                    customer_data['street'], customer_data['postal_code'],
                    customer_data['city'], True
                ))
        
        self.conn.commit()
        print("✅ Demo klanten aangemaakt")
    
    def create_demo_user(self):
        """Maak demo gebruiker aan"""
        with self.conn.cursor() as cur:
            # Check if demo user exists
            cur.execute("""
                SELECT id FROM users 
                WHERE organization_id = %s AND email = %s
            """, (self.organization_id, 'admin@demobedrijf.nl'))
            
            if cur.fetchone():
                print("✅ Demo gebruiker bestaat al")
                return
            
            # Create demo user
            user_id = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO users (
                    id, organization_id, email, first_name, last_name,
                    role, is_active, email_verified
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id, self.organization_id, 'admin@demobedrijf.nl',
                'Demo', 'Admin', 'admin', True, True
            ))
        
        self.conn.commit()
        print("✅ Demo gebruiker aangemaakt")
    
    def run_import(self, csv_files):
        """Voer complete import uit"""
        print("🚀 Start CSV data import...")
        
        try:
            self.connect()
            self.get_or_create_organization()
            self.import_product_categories()
            self.create_demo_customers()
            self.create_demo_user()
            
            # Import products from CSV files
            for csv_file in csv_files:
                if os.path.exists(csv_file):
                    self.import_products_from_csv(csv_file)
                else:
                    print(f"⚠️  CSV bestand niet gevonden: {csv_file}")
            
            print("✅ CSV data import voltooid!")
            
        except Exception as e:
            print(f"❌ Import gefaald: {e}")
            if self.conn:
                self.conn.rollback()
            raise
        finally:
            self.disconnect()

def main():
    parser = argparse.ArgumentParser(description='Import CSV data naar Document Generatie App database')
    parser.add_argument('--database-url', required=True, help='PostgreSQL database URL')
    parser.add_argument('--csv-files', nargs='+', required=True, help='CSV bestanden om te importeren')
    parser.add_argument('--organization', default='Demo Bedrijf', help='Organisatie naam')
    
    args = parser.parse_args()
    
    importer = CSVDataImporter(args.database_url)
    importer.run_import(args.csv_files)

if __name__ == '__main__':
    main()

