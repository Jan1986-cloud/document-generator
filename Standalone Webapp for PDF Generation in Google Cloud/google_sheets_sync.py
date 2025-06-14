#!/usr/bin/env python3
"""
Document Generatie App - Google Sheets Synchronisatie Service
Bidirectionele synchronisatie tussen PostgreSQL database en Google Sheets
"""

import os
import sys
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import argparse
import time

class GoogleSheetsSync:
    def __init__(self, database_url: str, service_account_file: str):
        """Initialiseer Google Sheets synchronisatie service"""
        self.database_url = database_url
        self.service_account_file = service_account_file
        self.conn = None
        self.sheets_service = None
        self.organization_id = None
        
        # Google Sheets API scopes
        self.scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive.file'
        ]
        
        # Mapping van database tabellen naar sheet configuraties
        self.table_configs = {
            'customers': {
                'sheet_name': 'Klanten',
                'columns': [
                    'customer_number', 'company_name', 'contact_person', 'email', 
                    'phone', 'btw_number', 'payment_terms', 'notes', 'is_active'
                ],
                'headers': [
                    'Klantnummer', 'Bedrijfsnaam', 'Contactpersoon', 'Email',
                    'Telefoon', 'BTW Nummer', 'Betalingstermijn', 'Notities', 'Actief'
                ],
                'key_column': 'customer_number'
            },
            'products': {
                'sheet_name': 'Producten',
                'columns': [
                    'article_number', 'name', 'description', 'unit',
                    'price_excl_btw', 'price_incl_btw', 'btw_percentage', 'is_active'
                ],
                'headers': [
                    'Artikelnummer', 'Naam', 'Omschrijving', 'Eenheid',
                    'Prijs excl. BTW', 'Prijs incl. BTW', 'BTW %', 'Actief'
                ],
                'key_column': 'article_number'
            },
            'orders': {
                'sheet_name': 'Opdrachten',
                'columns': [
                    'order_number', 'order_date', 'customer_name', 'description',
                    'status', 'subtotal_excl_btw', 'btw_amount', 'total_incl_btw'
                ],
                'headers': [
                    'Opdrachtnummer', 'Datum', 'Klant', 'Omschrijving',
                    'Status', 'Subtotaal excl. BTW', 'BTW Bedrag', 'Totaal incl. BTW'
                ],
                'key_column': 'order_number',
                'read_only': True  # Orders worden alleen gelezen, niet geschreven naar sheets
            }
        }
    
    def connect_database(self):
        """Maak verbinding met de database"""
        try:
            self.conn = psycopg2.connect(self.database_url)
            self.conn.autocommit = False
            print("✅ Database verbinding succesvol")
        except Exception as e:
            print(f"❌ Database verbinding gefaald: {e}")
            sys.exit(1)
    
    def connect_google_sheets(self):
        """Maak verbinding met Google Sheets API"""
        try:
            credentials = Credentials.from_service_account_file(
                self.service_account_file, scopes=self.scopes
            )
            self.sheets_service = build('sheets', 'v4', credentials=credentials)
            print("✅ Google Sheets API verbinding succesvol")
        except Exception as e:
            print(f"❌ Google Sheets API verbinding gefaald: {e}")
            sys.exit(1)
    
    def get_organization_id(self, org_name: str = None) -> str:
        """Haal organisatie ID op"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            if org_name:
                cur.execute("SELECT id FROM organizations WHERE name = %s", (org_name,))
            else:
                cur.execute("SELECT id FROM organizations LIMIT 1")
            
            result = cur.fetchone()
            if not result:
                raise ValueError("Geen organisatie gevonden")
            
            self.organization_id = result['id']
            return self.organization_id
    
    def create_or_get_spreadsheet(self, title: str) -> str:
        """Maak nieuwe spreadsheet aan of haal bestaande op"""
        try:
            # Probeer bestaande spreadsheet te vinden via titel
            # Voor productie zou je dit beter opslaan in de database
            
            # Maak nieuwe spreadsheet aan
            spreadsheet = {
                'properties': {
                    'title': title
                },
                'sheets': []
            }
            
            # Voeg sheets toe voor elke tabel
            for table_name, config in self.table_configs.items():
                sheet = {
                    'properties': {
                        'title': config['sheet_name']
                    }
                }
                spreadsheet['sheets'].append(sheet)
            
            result = self.sheets_service.spreadsheets().create(body=spreadsheet).execute()
            spreadsheet_id = result['spreadsheetId']
            
            print(f"✅ Spreadsheet aangemaakt: {title} (ID: {spreadsheet_id})")
            return spreadsheet_id
            
        except HttpError as e:
            print(f"❌ Fout bij aanmaken spreadsheet: {e}")
            raise
    
    def setup_sheet_headers(self, spreadsheet_id: str, table_name: str):
        """Stel headers in voor een sheet"""
        config = self.table_configs[table_name]
        
        try:
            # Schrijf headers naar de eerste rij
            range_name = f"{config['sheet_name']}!A1:{chr(65 + len(config['headers']) - 1)}1"
            
            body = {
                'values': [config['headers']]
            }
            
            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            # Maak header rij vet
            requests = [{
                'repeatCell': {
                    'range': {
                        'sheetId': self.get_sheet_id(spreadsheet_id, config['sheet_name']),
                        'startRowIndex': 0,
                        'endRowIndex': 1
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'textFormat': {
                                'bold': True
                            }
                        }
                    },
                    'fields': 'userEnteredFormat.textFormat.bold'
                }
            }]
            
            self.sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={'requests': requests}
            ).execute()
            
            print(f"✅ Headers ingesteld voor {config['sheet_name']}")
            
        except HttpError as e:
            print(f"❌ Fout bij instellen headers voor {table_name}: {e}")
    
    def get_sheet_id(self, spreadsheet_id: str, sheet_name: str) -> int:
        """Haal sheet ID op basis van naam"""
        try:
            spreadsheet = self.sheets_service.spreadsheets().get(
                spreadsheetId=spreadsheet_id
            ).execute()
            
            for sheet in spreadsheet['sheets']:
                if sheet['properties']['title'] == sheet_name:
                    return sheet['properties']['sheetId']
            
            raise ValueError(f"Sheet '{sheet_name}' niet gevonden")
            
        except HttpError as e:
            print(f"❌ Fout bij ophalen sheet ID: {e}")
            raise
    
    def export_table_to_sheet(self, spreadsheet_id: str, table_name: str):
        """Exporteer database tabel naar Google Sheet"""
        config = self.table_configs[table_name]
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                if table_name == 'customers':
                    query = """
                        SELECT customer_number, company_name, contact_person, email, phone,
                               btw_number, payment_terms, notes, is_active
                        FROM customers 
                        WHERE organization_id = %s
                        ORDER BY customer_number
                    """
                elif table_name == 'products':
                    query = """
                        SELECT article_number, name, description, unit,
                               price_excl_btw, price_incl_btw, btw_percentage, is_active
                        FROM products 
                        WHERE organization_id = %s
                        ORDER BY name
                    """
                elif table_name == 'orders':
                    query = """
                        SELECT o.order_number, o.order_date, c.company_name as customer_name,
                               o.description, o.status, o.subtotal_excl_btw, o.btw_amount, o.total_incl_btw
                        FROM orders o
                        JOIN customers c ON o.customer_id = c.id
                        WHERE o.organization_id = %s
                        ORDER BY o.order_date DESC
                    """
                else:
                    raise ValueError(f"Onbekende tabel: {table_name}")
                
                cur.execute(query, (self.organization_id,))
                rows = cur.fetchall()
                
                # Converteer naar lijst van lijsten voor Google Sheets
                values = []
                for row in rows:
                    row_values = []
                    for column in config['columns']:
                        value = row.get(column)
                        if value is None:
                            row_values.append('')
                        elif isinstance(value, bool):
                            row_values.append('Ja' if value else 'Nee')
                        elif isinstance(value, datetime):
                            row_values.append(value.strftime('%Y-%m-%d'))
                        else:
                            row_values.append(str(value))
                    values.append(row_values)
                
                # Schrijf data naar sheet (start vanaf rij 2, rij 1 heeft headers)
                if values:
                    range_name = f"{config['sheet_name']}!A2:{chr(65 + len(config['columns']) - 1)}{len(values) + 1}"
                    
                    body = {
                        'values': values
                    }
                    
                    # Clear bestaande data eerst
                    self.sheets_service.spreadsheets().values().clear(
                        spreadsheetId=spreadsheet_id,
                        range=f"{config['sheet_name']}!A2:Z1000"
                    ).execute()
                    
                    # Schrijf nieuwe data
                    self.sheets_service.spreadsheets().values().update(
                        spreadsheetId=spreadsheet_id,
                        range=range_name,
                        valueInputOption='RAW',
                        body=body
                    ).execute()
                    
                    print(f"✅ {len(values)} rijen geëxporteerd naar {config['sheet_name']}")
                else:
                    print(f"⚠️  Geen data gevonden voor {table_name}")
                    
        except Exception as e:
            print(f"❌ Fout bij exporteren {table_name}: {e}")
            raise
    
    def import_sheet_to_table(self, spreadsheet_id: str, table_name: str):
        """Importeer Google Sheet naar database tabel"""
        if self.table_configs[table_name].get('read_only'):
            print(f"⚠️  {table_name} is read-only, import overgeslagen")
            return
        
        config = self.table_configs[table_name]
        
        try:
            # Lees data uit sheet
            range_name = f"{config['sheet_name']}!A2:Z1000"
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            if not values:
                print(f"⚠️  Geen data gevonden in {config['sheet_name']}")
                return
            
            updated_count = 0
            inserted_count = 0
            
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                for row_values in values:
                    # Pad row met lege strings als nodig
                    while len(row_values) < len(config['columns']):
                        row_values.append('')
                    
                    # Maak dictionary van kolom -> waarde
                    row_data = {}
                    for i, column in enumerate(config['columns']):
                        value = row_values[i].strip() if i < len(row_values) else ''
                        
                        # Converteer speciale waarden
                        if column.endswith('_active') or column == 'is_active':
                            row_data[column] = value.lower() in ['ja', 'yes', 'true', '1']
                        elif 'price' in column or 'amount' in column or 'percentage' in column:
                            try:
                                row_data[column] = float(value.replace(',', '.')) if value else 0
                            except ValueError:
                                row_data[column] = 0
                        elif 'terms' in column:
                            try:
                                row_data[column] = int(value) if value else 30
                            except ValueError:
                                row_data[column] = 30
                        else:
                            row_data[column] = value
                    
                    # Skip lege rijen
                    key_value = row_data.get(config['key_column'])
                    if not key_value:
                        continue
                    
                    # Check of record bestaat
                    if table_name == 'customers':
                        cur.execute("""
                            SELECT id FROM customers 
                            WHERE organization_id = %s AND customer_number = %s
                        """, (self.organization_id, key_value))
                    elif table_name == 'products':
                        cur.execute("""
                            SELECT id FROM products 
                            WHERE organization_id = %s AND (article_number = %s OR name = %s)
                        """, (self.organization_id, key_value, row_data.get('name', '')))
                    
                    existing = cur.fetchone()
                    
                    if existing:
                        # Update bestaand record
                        if table_name == 'customers':
                            cur.execute("""
                                UPDATE customers SET
                                    company_name = %s, contact_person = %s, email = %s, phone = %s,
                                    btw_number = %s, payment_terms = %s, notes = %s, is_active = %s,
                                    updated_at = CURRENT_TIMESTAMP
                                WHERE id = %s
                            """, (
                                row_data['company_name'], row_data['contact_person'], 
                                row_data['email'], row_data['phone'], row_data['btw_number'],
                                row_data['payment_terms'], row_data['notes'], row_data['is_active'],
                                existing['id']
                            ))
                        elif table_name == 'products':
                            cur.execute("""
                                UPDATE products SET
                                    name = %s, description = %s, unit = %s,
                                    price_excl_btw = %s, price_incl_btw = %s, btw_percentage = %s,
                                    is_active = %s, updated_at = CURRENT_TIMESTAMP
                                WHERE id = %s
                            """, (
                                row_data['name'], row_data['description'], row_data['unit'],
                                row_data['price_excl_btw'], row_data['price_incl_btw'],
                                row_data['btw_percentage'], row_data['is_active'], existing['id']
                            ))
                        updated_count += 1
                    else:
                        # Insert nieuw record
                        record_id = str(uuid.uuid4())
                        
                        if table_name == 'customers':
                            cur.execute("""
                                INSERT INTO customers (
                                    id, organization_id, customer_number, company_name, contact_person,
                                    email, phone, btw_number, payment_terms, notes, is_active
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """, (
                                record_id, self.organization_id, row_data['customer_number'],
                                row_data['company_name'], row_data['contact_person'],
                                row_data['email'], row_data['phone'], row_data['btw_number'],
                                row_data['payment_terms'], row_data['notes'], row_data['is_active']
                            ))
                        elif table_name == 'products':
                            cur.execute("""
                                INSERT INTO products (
                                    id, organization_id, article_number, name, description, unit,
                                    price_excl_btw, price_incl_btw, btw_percentage, is_active
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """, (
                                record_id, self.organization_id, row_data['article_number'],
                                row_data['name'], row_data['description'], row_data['unit'],
                                row_data['price_excl_btw'], row_data['price_incl_btw'],
                                row_data['btw_percentage'], row_data['is_active']
                            ))
                        inserted_count += 1
            
            self.conn.commit()
            print(f"✅ {config['sheet_name']}: {inserted_count} toegevoegd, {updated_count} bijgewerkt")
            
        except Exception as e:
            print(f"❌ Fout bij importeren {table_name}: {e}")
            self.conn.rollback()
            raise
    
    def log_sync_operation(self, sheet_id: str, sheet_name: str, sync_type: str, 
                          status: str, records_processed: int = 0, error_message: str = None):
        """Log synchronisatie operatie"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO sheets_sync_log (
                        id, organization_id, sheet_id, sheet_name, sync_type, sync_status,
                        records_processed, error_message, completed_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    str(uuid.uuid4()), self.organization_id, sheet_id, sheet_name,
                    sync_type, status, records_processed, error_message,
                    datetime.now(timezone.utc)
                ))
            self.conn.commit()
        except Exception as e:
            print(f"⚠️  Fout bij loggen sync operatie: {e}")
    
    def full_sync(self, spreadsheet_id: str, direction: str = 'both'):
        """Voer volledige synchronisatie uit"""
        print(f"🚀 Start volledige synchronisatie (richting: {direction})")
        
        try:
            for table_name in self.table_configs.keys():
                config = self.table_configs[table_name]
                
                if direction in ['export', 'both']:
                    print(f"📤 Exporteren {table_name} naar {config['sheet_name']}...")
                    try:
                        self.export_table_to_sheet(spreadsheet_id, table_name)
                        self.log_sync_operation(
                            spreadsheet_id, config['sheet_name'], 'export', 'success'
                        )
                    except Exception as e:
                        self.log_sync_operation(
                            spreadsheet_id, config['sheet_name'], 'export', 'error', 
                            error_message=str(e)
                        )
                        raise
                
                if direction in ['import', 'both'] and not config.get('read_only'):
                    print(f"📥 Importeren {config['sheet_name']} naar {table_name}...")
                    try:
                        self.import_sheet_to_table(spreadsheet_id, table_name)
                        self.log_sync_operation(
                            spreadsheet_id, config['sheet_name'], 'import', 'success'
                        )
                    except Exception as e:
                        self.log_sync_operation(
                            spreadsheet_id, config['sheet_name'], 'import', 'error',
                            error_message=str(e)
                        )
                        raise
                
                # Kleine pauze tussen operaties
                time.sleep(1)
            
            print("✅ Volledige synchronisatie voltooid!")
            
        except Exception as e:
            print(f"❌ Synchronisatie gefaald: {e}")
            raise
    
    def setup_new_spreadsheet(self, title: str) -> str:
        """Stel nieuwe spreadsheet in met alle benodigde sheets"""
        print(f"🚀 Instellen nieuwe spreadsheet: {title}")
        
        # Maak spreadsheet aan
        spreadsheet_id = self.create_or_get_spreadsheet(title)
        
        # Stel headers in voor alle sheets
        for table_name in self.table_configs.keys():
            self.setup_sheet_headers(spreadsheet_id, table_name)
        
        # Exporteer alle data
        self.full_sync(spreadsheet_id, direction='export')
        
        print(f"✅ Spreadsheet setup voltooid!")
        print(f"🔗 URL: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
        
        return spreadsheet_id
    
    def disconnect(self):
        """Sluit verbindingen"""
        if self.conn:
            self.conn.close()
            print("✅ Database verbinding gesloten")

def main():
    parser = argparse.ArgumentParser(description='Google Sheets synchronisatie voor Document Generatie App')
    parser.add_argument('--database-url', required=True, help='PostgreSQL database URL')
    parser.add_argument('--service-account-file', required=True, help='Google Service Account JSON bestand')
    parser.add_argument('--organization', help='Organisatie naam')
    parser.add_argument('--action', choices=['setup', 'sync', 'export', 'import'], 
                       default='sync', help='Actie om uit te voeren')
    parser.add_argument('--spreadsheet-id', help='Google Spreadsheet ID')
    parser.add_argument('--spreadsheet-title', default='Document Generator Data', 
                       help='Titel voor nieuwe spreadsheet')
    
    args = parser.parse_args()
    
    # Initialiseer sync service
    sync_service = GoogleSheetsSync(args.database_url, args.service_account_file)
    
    try:
        # Maak verbindingen
        sync_service.connect_database()
        sync_service.connect_google_sheets()
        sync_service.get_organization_id(args.organization)
        
        if args.action == 'setup':
            # Stel nieuwe spreadsheet in
            spreadsheet_id = sync_service.setup_new_spreadsheet(args.spreadsheet_title)
            print(f"Spreadsheet ID: {spreadsheet_id}")
            
        elif args.action in ['sync', 'export', 'import']:
            if not args.spreadsheet_id:
                print("❌ --spreadsheet-id is vereist voor sync/export/import acties")
                sys.exit(1)
            
            # Voer synchronisatie uit
            direction = 'both' if args.action == 'sync' else args.action
            sync_service.full_sync(args.spreadsheet_id, direction)
    
    except Exception as e:
        print(f"❌ Fout: {e}")
        sys.exit(1)
    finally:
        sync_service.disconnect()

if __name__ == '__main__':
    main()

