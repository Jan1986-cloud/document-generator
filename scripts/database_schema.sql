-- Document Generatie App - Database Schema
-- PostgreSQL Database Schema voor alle entiteiten

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Enum types
CREATE TYPE user_role_type AS ENUM ('admin', 'director', 'sales', 'technician', 'accountant');
CREATE TYPE document_type AS ENUM ('quote', 'work_order', 'invoice', 'combined_invoice');
CREATE TYPE document_status AS ENUM ('draft', 'sent', 'approved', 'rejected', 'paid', 'cancelled');
CREATE TYPE order_status AS ENUM ('draft', 'confirmed', 'in_progress', 'completed', 'cancelled');

-- Organizations tabel
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    address VARCHAR(255),
    postal_code VARCHAR(20),
    city VARCHAR(100),
    country VARCHAR(100) DEFAULT 'Nederland',
    phone VARCHAR(50),
    email VARCHAR(255),
    website VARCHAR(255),
    kvk_number VARCHAR(20),
    btw_number VARCHAR(30),
    iban VARCHAR(50),
    logo_url VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Users tabel
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(50),
    role user_role_type NOT NULL DEFAULT 'technician',
    is_active BOOLEAN DEFAULT true,
    email_verified BOOLEAN DEFAULT false,
    google_id VARCHAR(255) UNIQUE,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User sessions tabel
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User preferences tabel
CREATE TABLE user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    dashboard_config JSONB DEFAULT '{}',
    notification_settings JSONB DEFAULT '{}',
    theme VARCHAR(20) DEFAULT 'light',
    language VARCHAR(10) DEFAULT 'nl',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Customers tabel
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    customer_number VARCHAR(50) UNIQUE,
    company_name VARCHAR(255) NOT NULL,
    contact_person VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    btw_number VARCHAR(30),
    payment_terms INTEGER DEFAULT 30,
    notes TEXT,
    is_active BOOLEAN DEFAULT true,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Customer addresses tabel
CREATE TABLE customer_addresses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    address_type VARCHAR(20) NOT NULL CHECK (address_type IN ('billing', 'delivery', 'both')),
    street VARCHAR(255) NOT NULL,
    postal_code VARCHAR(20) NOT NULL,
    city VARCHAR(100) NOT NULL,
    country VARCHAR(100) DEFAULT 'Nederland',
    is_primary BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Customer contacts tabel
CREATE TABLE customer_contacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    title VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(50),
    mobile VARCHAR(50),
    department VARCHAR(100),
    is_primary BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Product categories tabel
CREATE TABLE product_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    parent_id UUID REFERENCES product_categories(id),
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Products tabel
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    category_id UUID REFERENCES product_categories(id),
    article_number VARCHAR(100),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    unit VARCHAR(50) NOT NULL DEFAULT 'stuk',
    price_excl_btw DECIMAL(10,2),
    price_incl_btw DECIMAL(10,2),
    btw_percentage DECIMAL(5,2) DEFAULT 21.00,
    is_active BOOLEAN DEFAULT true,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Product attachments tabel
CREATE TABLE product_attachments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_url VARCHAR(500) NOT NULL,
    file_type VARCHAR(50),
    attachment_type VARCHAR(50) CHECK (attachment_type IN ('datasheet', 'photo', 'manual', 'other')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Orders tabel
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    customer_id UUID NOT NULL REFERENCES customers(id),
    order_number VARCHAR(50) UNIQUE NOT NULL,
    order_date DATE NOT NULL DEFAULT CURRENT_DATE,
    description TEXT,
    status order_status DEFAULT 'draft',
    subtotal_excl_btw DECIMAL(10,2) DEFAULT 0,
    btw_amount DECIMAL(10,2) DEFAULT 0,
    total_incl_btw DECIMAL(10,2) DEFAULT 0,
    notes TEXT,
    created_by UUID REFERENCES users(id),
    assigned_to UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Order items tabel
CREATE TABLE order_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(id),
    description TEXT NOT NULL,
    quantity DECIMAL(10,3) NOT NULL,
    unit VARCHAR(50) NOT NULL,
    unit_price_excl_btw DECIMAL(10,2) NOT NULL,
    unit_price_incl_btw DECIMAL(10,2) NOT NULL,
    btw_percentage DECIMAL(5,2) NOT NULL,
    total_excl_btw DECIMAL(10,2) NOT NULL,
    total_incl_btw DECIMAL(10,2) NOT NULL,
    delivery_notes TEXT,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Document templates tabel
CREATE TABLE document_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    document_type document_type NOT NULL,
    google_doc_id VARCHAR(255),
    template_url VARCHAR(500),
    is_active BOOLEAN DEFAULT true,
    placeholders JSONB DEFAULT '[]',
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Generated documents tabel
CREATE TABLE generated_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    order_id UUID NOT NULL REFERENCES orders(id),
    template_id UUID NOT NULL REFERENCES document_templates(id),
    document_number VARCHAR(50) NOT NULL,
    document_type document_type NOT NULL,
    status document_status DEFAULT 'draft',
    file_url VARCHAR(500),
    google_doc_id VARCHAR(255),
    generated_data JSONB,
    sent_at TIMESTAMP WITH TIME ZONE,
    sent_to VARCHAR(255),
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- System settings tabel
CREATE TABLE system_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    setting_key VARCHAR(100) NOT NULL,
    setting_value TEXT,
    setting_type VARCHAR(50) DEFAULT 'string',
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(organization_id, setting_key)
);

-- Widget configurations tabel
CREATE TABLE widget_configurations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    widget_name VARCHAR(100) NOT NULL,
    widget_config JSONB DEFAULT '{}',
    roles user_role_type[] DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Google Sheets sync log tabel
CREATE TABLE sheets_sync_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    sheet_id VARCHAR(255) NOT NULL,
    sheet_name VARCHAR(255),
    sync_type VARCHAR(50) NOT NULL,
    sync_status VARCHAR(50) NOT NULL,
    records_processed INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Audit log tabel
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id),
    user_id UUID REFERENCES users(id),
    table_name VARCHAR(100) NOT NULL,
    record_id UUID,
    action VARCHAR(20) NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes voor performance
CREATE INDEX idx_users_organization_id ON users(organization_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_google_id ON users(google_id);
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_token_hash ON user_sessions(token_hash);
CREATE INDEX idx_user_sessions_expires_at ON user_sessions(expires_at);

CREATE INDEX idx_customers_organization_id ON customers(organization_id);
CREATE INDEX idx_customers_customer_number ON customers(customer_number);
CREATE INDEX idx_customer_addresses_customer_id ON customer_addresses(customer_id);
CREATE INDEX idx_customer_contacts_customer_id ON customer_contacts(customer_id);

CREATE INDEX idx_products_organization_id ON products(organization_id);
CREATE INDEX idx_products_category_id ON products(category_id);
CREATE INDEX idx_products_article_number ON products(article_number);
CREATE INDEX idx_product_attachments_product_id ON product_attachments(product_id);

CREATE INDEX idx_orders_organization_id ON orders(organization_id);
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_orders_order_number ON orders(order_number);
CREATE INDEX idx_orders_order_date ON orders(order_date);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_product_id ON order_items(product_id);

CREATE INDEX idx_generated_documents_organization_id ON generated_documents(organization_id);
CREATE INDEX idx_generated_documents_order_id ON generated_documents(order_id);
CREATE INDEX idx_generated_documents_document_number ON generated_documents(document_number);
CREATE INDEX idx_generated_documents_document_type ON generated_documents(document_type);

CREATE INDEX idx_system_settings_organization_id ON system_settings(organization_id);
CREATE INDEX idx_audit_log_organization_id ON audit_log(organization_id);
CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_log_table_name ON audit_log(table_name);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at);

-- Triggers voor updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON organizations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON user_preferences FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_customers_updated_at BEFORE UPDATE ON customers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_customer_addresses_updated_at BEFORE UPDATE ON customer_addresses FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_customer_contacts_updated_at BEFORE UPDATE ON customer_contacts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_product_categories_updated_at BEFORE UPDATE ON product_categories FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_document_templates_updated_at BEFORE UPDATE ON document_templates FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_generated_documents_updated_at BEFORE UPDATE ON generated_documents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_system_settings_updated_at BEFORE UPDATE ON system_settings FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Audit trigger functie
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        INSERT INTO audit_log (table_name, record_id, action, old_values)
        VALUES (TG_TABLE_NAME, OLD.id, TG_OP, row_to_json(OLD));
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_log (table_name, record_id, action, old_values, new_values)
        VALUES (TG_TABLE_NAME, NEW.id, TG_OP, row_to_json(OLD), row_to_json(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        INSERT INTO audit_log (table_name, record_id, action, new_values)
        VALUES (TG_TABLE_NAME, NEW.id, TG_OP, row_to_json(NEW));
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Audit triggers voor belangrijke tabellen
CREATE TRIGGER audit_organizations AFTER INSERT OR UPDATE OR DELETE ON organizations FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
CREATE TRIGGER audit_users AFTER INSERT OR UPDATE OR DELETE ON users FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
CREATE TRIGGER audit_customers AFTER INSERT OR UPDATE OR DELETE ON customers FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
CREATE TRIGGER audit_products AFTER INSERT OR UPDATE OR DELETE ON products FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
CREATE TRIGGER audit_orders AFTER INSERT OR UPDATE OR DELETE ON orders FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
CREATE TRIGGER audit_generated_documents AFTER INSERT OR UPDATE OR DELETE ON generated_documents FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

-- Views voor rapportage
CREATE VIEW customer_summary AS
SELECT 
    c.id,
    c.customer_number,
    c.company_name,
    c.contact_person,
    c.email,
    c.phone,
    COUNT(o.id) as total_orders,
    COALESCE(SUM(o.total_incl_btw), 0) as total_revenue,
    MAX(o.order_date) as last_order_date
FROM customers c
LEFT JOIN orders o ON c.id = o.customer_id
GROUP BY c.id, c.customer_number, c.company_name, c.contact_person, c.email, c.phone;

CREATE VIEW product_summary AS
SELECT 
    p.id,
    p.article_number,
    p.name,
    p.description,
    p.unit,
    p.price_excl_btw,
    p.price_incl_btw,
    pc.name as category_name,
    COUNT(oi.id) as times_ordered,
    COALESCE(SUM(oi.quantity), 0) as total_quantity_sold,
    COALESCE(SUM(oi.total_incl_btw), 0) as total_revenue
FROM products p
LEFT JOIN product_categories pc ON p.category_id = pc.id
LEFT JOIN order_items oi ON p.id = oi.product_id
GROUP BY p.id, p.article_number, p.name, p.description, p.unit, p.price_excl_btw, p.price_incl_btw, pc.name;

CREATE VIEW order_summary AS
SELECT 
    o.id,
    o.order_number,
    o.order_date,
    o.status,
    c.company_name as customer_name,
    c.customer_number,
    o.subtotal_excl_btw,
    o.btw_amount,
    o.total_incl_btw,
    COUNT(oi.id) as item_count,
    u1.first_name || ' ' || u1.last_name as created_by_name,
    u2.first_name || ' ' || u2.last_name as assigned_to_name
FROM orders o
JOIN customers c ON o.customer_id = c.id
LEFT JOIN order_items oi ON o.id = oi.order_id
LEFT JOIN users u1 ON o.created_by = u1.id
LEFT JOIN users u2 ON o.assigned_to = u2.id
GROUP BY o.id, o.order_number, o.order_date, o.status, c.company_name, c.customer_number, 
         o.subtotal_excl_btw, o.btw_amount, o.total_incl_btw, u1.first_name, u1.last_name, u2.first_name, u2.last_name;

-- Functies voor automatische nummering
CREATE OR REPLACE FUNCTION generate_customer_number(org_id UUID)
RETURNS VARCHAR(50) AS $$
DECLARE
    next_number INTEGER;
    customer_number VARCHAR(50);
BEGIN
    SELECT COALESCE(MAX(CAST(SUBSTRING(customer_number FROM '[0-9]+') AS INTEGER)), 0) + 1
    INTO next_number
    FROM customers 
    WHERE organization_id = org_id 
    AND customer_number ~ '^[0-9]+$';
    
    customer_number := LPAD(next_number::TEXT, 6, '0');
    RETURN customer_number;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION generate_order_number(org_id UUID, order_year INTEGER DEFAULT NULL)
RETURNS VARCHAR(50) AS $$
DECLARE
    next_number INTEGER;
    order_number VARCHAR(50);
    year_suffix VARCHAR(4);
BEGIN
    IF order_year IS NULL THEN
        order_year := EXTRACT(YEAR FROM CURRENT_DATE);
    END IF;
    
    year_suffix := RIGHT(order_year::TEXT, 2);
    
    SELECT COALESCE(MAX(CAST(SUBSTRING(order_number FROM '[0-9]+') AS INTEGER)), 0) + 1
    INTO next_number
    FROM orders 
    WHERE organization_id = org_id 
    AND EXTRACT(YEAR FROM order_date) = order_year;
    
    order_number := LPAD(next_number::TEXT, 4, '0') || '-' || year_suffix;
    RETURN order_number;
END;
$$ LANGUAGE plpgsql;

-- Seed data voor standaard instellingen
INSERT INTO system_settings (organization_id, setting_key, setting_value, setting_type, description) 
SELECT 
    o.id,
    unnest(ARRAY['default_btw_percentage', 'default_payment_terms', 'max_loop_items', 'document_prefix_quote', 'document_prefix_invoice', 'document_prefix_work_order']),
    unnest(ARRAY['21.00', '30', '10', 'OFF', 'FACT', 'WB']),
    unnest(ARRAY['decimal', 'integer', 'integer', 'string', 'string', 'string']),
    unnest(ARRAY['Standaard BTW percentage', 'Standaard betalingstermijn in dagen', 'Maximum aantal loop items in documenten', 'Prefix voor offerte nummers', 'Prefix voor factuur nummers', 'Prefix voor werkbon nummers'])
FROM organizations o
WHERE NOT EXISTS (
    SELECT 1 FROM system_settings ss 
    WHERE ss.organization_id = o.id 
    AND ss.setting_key IN ('default_btw_percentage', 'default_payment_terms', 'max_loop_items', 'document_prefix_quote', 'document_prefix_invoice', 'document_prefix_work_order')
);

-- Standaard widget configuraties
INSERT INTO widget_configurations (organization_id, widget_name, widget_config, roles, sort_order)
SELECT 
    o.id,
    unnest(ARRAY['recent_orders', 'revenue_chart', 'customer_stats', 'product_stats', 'pending_documents', 'system_status']),
    unnest(ARRAY[
        '{"title": "Recente Opdrachten", "limit": 10}',
        '{"title": "Omzet Overzicht", "period": "month"}',
        '{"title": "Klant Statistieken", "show_new": true}',
        '{"title": "Product Statistieken", "show_top": 5}',
        '{"title": "Openstaande Documenten", "types": ["quote", "invoice"]}',
        '{"title": "Systeem Status", "show_health": true}'
    ]::jsonb[]),
    unnest(ARRAY[
        ARRAY['admin', 'director', 'sales', 'accountant']::user_role_type[],
        ARRAY['admin', 'director', 'accountant']::user_role_type[],
        ARRAY['admin', 'director', 'sales']::user_role_type[],
        ARRAY['admin', 'director', 'sales']::user_role_type[],
        ARRAY['admin', 'director', 'sales', 'accountant']::user_role_type[],
        ARRAY['admin']::user_role_type[]
    ]),
    unnest(ARRAY[1, 2, 3, 4, 5, 6])
FROM organizations o
WHERE NOT EXISTS (
    SELECT 1 FROM widget_configurations wc 
    WHERE wc.organization_id = o.id
);

COMMENT ON DATABASE document_generator IS 'Database voor Document Generatie App - bevat alle entiteiten voor klanten, producten, opdrachten en documentgeneratie';

