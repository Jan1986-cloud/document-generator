#!/bin/bash

# Document Generatie App - Database Migratie Script
# Voert database migraties uit en beheert schema versies

set -e

# Kleuren voor output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functies
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuratie
DATABASE_URL=""
MIGRATIONS_DIR="./migrations"
SCHEMA_FILE="./database_schema.sql"

# Functie om database URL te valideren
validate_database_url() {
    if [ -z "$DATABASE_URL" ]; then
        error "DATABASE_URL omgevingsvariabele is niet ingesteld"
        exit 1
    fi
    
    # Test database verbinding
    if ! psql "$DATABASE_URL" -c "SELECT 1;" >/dev/null 2>&1; then
        error "Kan geen verbinding maken met database"
        exit 1
    fi
    
    success "Database verbinding succesvol"
}

# Functie om migratie tabel aan te maken
create_migration_table() {
    log "Aanmaken van migratie tabel..."
    
    psql "$DATABASE_URL" << 'EOF'
CREATE TABLE IF NOT EXISTS schema_migrations (
    id SERIAL PRIMARY KEY,
    version VARCHAR(255) UNIQUE NOT NULL,
    filename VARCHAR(255) NOT NULL,
    checksum VARCHAR(64) NOT NULL,
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    execution_time_ms INTEGER,
    success BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_schema_migrations_version ON schema_migrations(version);
CREATE INDEX IF NOT EXISTS idx_schema_migrations_executed_at ON schema_migrations(executed_at);
EOF
    
    success "Migratie tabel aangemaakt"
}

# Functie om checksum te berekenen
calculate_checksum() {
    local file="$1"
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$file" | cut -d' ' -f1
    elif command -v shasum >/dev/null 2>&1; then
        shasum -a 256 "$file" | cut -d' ' -f1
    else
        error "Geen SHA256 tool gevonden"
        exit 1
    fi
}

# Functie om migratie versie uit bestandsnaam te halen
extract_version() {
    local filename="$1"
    echo "$filename" | sed -E 's/^([0-9]{4}_[0-9]{2}_[0-9]{2}_[0-9]{6})_.*/\1/'
}

# Functie om uitgevoerde migraties op te halen
get_executed_migrations() {
    psql "$DATABASE_URL" -t -c "SELECT version FROM schema_migrations WHERE success = TRUE ORDER BY version;" | tr -d ' '
}

# Functie om pending migraties te vinden
find_pending_migrations() {
    local executed_migrations
    executed_migrations=$(get_executed_migrations)
    
    local pending_migrations=()
    
    if [ -d "$MIGRATIONS_DIR" ]; then
        for migration_file in "$MIGRATIONS_DIR"/*.sql; do
            if [ -f "$migration_file" ]; then
                local version
                version=$(extract_version "$(basename "$migration_file")")
                
                if ! echo "$executed_migrations" | grep -q "^$version$"; then
                    pending_migrations+=("$migration_file")
                fi
            fi
        done
    fi
    
    printf '%s\n' "${pending_migrations[@]}" | sort
}

# Functie om enkele migratie uit te voeren
execute_migration() {
    local migration_file="$1"
    local filename
    filename=$(basename "$migration_file")
    local version
    version=$(extract_version "$filename")
    local checksum
    checksum=$(calculate_checksum "$migration_file")
    
    log "Uitvoeren migratie: $filename"
    
    local start_time
    start_time=$(date +%s%3N)
    
    # Begin transactie en voer migratie uit
    if psql "$DATABASE_URL" << EOF
BEGIN;

-- Voer migratie uit
\i $migration_file

-- Registreer migratie
INSERT INTO schema_migrations (version, filename, checksum, execution_time_ms)
VALUES ('$version', '$filename', '$checksum', $(date +%s%3N) - $start_time);

COMMIT;
EOF
    then
        local end_time
        end_time=$(date +%s%3N)
        local execution_time=$((end_time - start_time))
        
        success "Migratie $filename succesvol uitgevoerd (${execution_time}ms)"
        return 0
    else
        error "Migratie $filename gefaald"
        
        # Registreer gefaalde migratie
        psql "$DATABASE_URL" << EOF
INSERT INTO schema_migrations (version, filename, checksum, success)
VALUES ('$version', '$filename', '$checksum', FALSE)
ON CONFLICT (version) DO UPDATE SET success = FALSE;
EOF
        return 1
    fi
}

# Functie om alle pending migraties uit te voeren
run_migrations() {
    log "Zoeken naar pending migraties..."
    
    local pending_migrations
    pending_migrations=$(find_pending_migrations)
    
    if [ -z "$pending_migrations" ]; then
        success "Geen pending migraties gevonden"
        return 0
    fi
    
    local migration_count
    migration_count=$(echo "$pending_migrations" | wc -l)
    log "Gevonden $migration_count pending migratie(s)"
    
    local failed_count=0
    
    while IFS= read -r migration_file; do
        if [ -n "$migration_file" ]; then
            if ! execute_migration "$migration_file"; then
                ((failed_count++))
                if [ "$CONTINUE_ON_ERROR" != "true" ]; then
                    error "Stoppen vanwege gefaalde migratie"
                    break
                fi
            fi
        fi
    done <<< "$pending_migrations"
    
    if [ $failed_count -eq 0 ]; then
        success "Alle migraties succesvol uitgevoerd"
    else
        error "$failed_count migratie(s) gefaald"
        return 1
    fi
}

# Functie om migratie status te tonen
show_status() {
    log "Migratie status:"
    
    echo
    echo "Uitgevoerde migraties:"
    psql "$DATABASE_URL" -c "
        SELECT version, filename, executed_at, execution_time_ms, success
        FROM schema_migrations 
        ORDER BY version;
    "
    
    echo
    local pending_migrations
    pending_migrations=$(find_pending_migrations)
    
    if [ -n "$pending_migrations" ]; then
        echo "Pending migraties:"
        while IFS= read -r migration_file; do
            if [ -n "$migration_file" ]; then
                echo "  - $(basename "$migration_file")"
            fi
        done <<< "$pending_migrations"
    else
        echo "Geen pending migraties"
    fi
}

# Functie om database schema te initialiseren
init_schema() {
    log "Initialiseren database schema..."
    
    if [ ! -f "$SCHEMA_FILE" ]; then
        error "Schema bestand niet gevonden: $SCHEMA_FILE"
        exit 1
    fi
    
    # Controleer of database al geïnitialiseerd is
    if psql "$DATABASE_URL" -c "SELECT 1 FROM information_schema.tables WHERE table_name = 'organizations';" | grep -q "1 row"; then
        warning "Database lijkt al geïnitialiseerd te zijn"
        read -p "Wil je doorgaan en het schema opnieuw uitvoeren? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log "Schema initialisatie geannuleerd"
            return 0
        fi
    fi
    
    local start_time
    start_time=$(date +%s%3N)
    
    if psql "$DATABASE_URL" -f "$SCHEMA_FILE"; then
        local end_time
        end_time=$(date +%s%3N)
        local execution_time=$((end_time - start_time))
        
        success "Database schema geïnitialiseerd (${execution_time}ms)"
        
        # Registreer schema initialisatie als migratie
        local version="0000_00_00_000000"
        local checksum
        checksum=$(calculate_checksum "$SCHEMA_FILE")
        
        psql "$DATABASE_URL" << EOF
INSERT INTO schema_migrations (version, filename, checksum, execution_time_ms)
VALUES ('$version', 'initial_schema.sql', '$checksum', $execution_time)
ON CONFLICT (version) DO NOTHING;
EOF
    else
        error "Schema initialisatie gefaald"
        return 1
    fi
}

# Functie om nieuwe migratie bestand aan te maken
create_migration() {
    local migration_name="$1"
    
    if [ -z "$migration_name" ]; then
        error "Migratie naam is vereist"
        echo "Gebruik: $0 create <migration_name>"
        exit 1
    fi
    
    # Maak migrations directory aan als deze niet bestaat
    mkdir -p "$MIGRATIONS_DIR"
    
    # Genereer timestamp
    local timestamp
    timestamp=$(date +"%Y_%m_%d_%H%M%S")
    
    # Maak bestandsnaam
    local filename="${timestamp}_${migration_name}.sql"
    local filepath="$MIGRATIONS_DIR/$filename"
    
    # Maak migratie bestand aan met template
    cat > "$filepath" << EOF
-- Migration: $migration_name
-- Created: $(date)
-- Description: [Beschrijf hier wat deze migratie doet]

-- Voeg hier je SQL statements toe
-- Bijvoorbeeld:

-- CREATE TABLE example (
--     id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
--     name VARCHAR(255) NOT NULL,
--     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
-- );

-- CREATE INDEX idx_example_name ON example(name);
EOF
    
    success "Migratie bestand aangemaakt: $filepath"
    log "Bewerk het bestand en voeg je SQL statements toe"
}

# Functie om migratie terug te draaien (rollback)
rollback_migration() {
    local version="$1"
    
    if [ -z "$version" ]; then
        error "Migratie versie is vereist voor rollback"
        exit 1
    fi
    
    warning "Rollback functionaliteit is nog niet geïmplementeerd"
    warning "Voor rollback moet je handmatig de database wijzigingen ongedaan maken"
    
    # Markeer migratie als niet uitgevoerd
    psql "$DATABASE_URL" << EOF
DELETE FROM schema_migrations WHERE version = '$version';
EOF
    
    success "Migratie $version gemarkeerd als niet uitgevoerd"
}

# Functie om database backup te maken
backup_database() {
    local backup_file="backup_$(date +%Y%m%d_%H%M%S).sql"
    
    log "Maken van database backup: $backup_file"
    
    if pg_dump "$DATABASE_URL" > "$backup_file"; then
        success "Database backup aangemaakt: $backup_file"
    else
        error "Database backup gefaald"
        return 1
    fi
}

# Functie om help te tonen
show_help() {
    echo "Document Generatie App - Database Migratie Tool"
    echo
    echo "Gebruik: $0 [OPTIE] [COMMANDO]"
    echo
    echo "Commando's:"
    echo "  init                 Initialiseer database schema"
    echo "  migrate              Voer alle pending migraties uit"
    echo "  status               Toon migratie status"
    echo "  create <naam>        Maak nieuwe migratie aan"
    echo "  rollback <versie>    Draai migratie terug"
    echo "  backup               Maak database backup"
    echo "  help                 Toon deze help"
    echo
    echo "Omgevingsvariabelen:"
    echo "  DATABASE_URL         PostgreSQL database URL (vereist)"
    echo "  CONTINUE_ON_ERROR    Ga door bij gefaalde migraties (true/false)"
    echo
    echo "Voorbeelden:"
    echo "  $0 init"
    echo "  $0 migrate"
    echo "  $0 create add_user_preferences"
    echo "  $0 status"
}

# Hoofdfunctie
main() {
    local command="${1:-help}"
    
    case "$command" in
        "init")
            validate_database_url
            create_migration_table
            init_schema
            ;;
        "migrate")
            validate_database_url
            create_migration_table
            run_migrations
            ;;
        "status")
            validate_database_url
            create_migration_table
            show_status
            ;;
        "create")
            create_migration "$2"
            ;;
        "rollback")
            validate_database_url
            rollback_migration "$2"
            ;;
        "backup")
            validate_database_url
            backup_database
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            error "Onbekend commando: $command"
            echo
            show_help
            exit 1
            ;;
    esac
}

# Voer script uit als het direct wordt aangeroepen
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi

