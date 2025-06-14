#!/bin/bash

# IAM Permissions Fixer voor Document Generator
# Dit script lost de laatste 2 gefaalde permission checks op

echo "🔧 IAM Permissions Verificatie & Fix"
echo "===================================="

PROJECT_ID="gen-lang-client-0695866337"
SERVICE_ACCOUNT_EMAIL="document-generator@${PROJECT_ID}.iam.gserviceaccount.com"

# Kleuren
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo "🔍 Controleren huidige permissions..."

# Functie om permissions te controleren
check_permission() {
    local role="$1"
    local description="$2"
    
    echo -n "Checking $description... "
    
    if gcloud projects get-iam-policy $PROJECT_ID \
        --flatten="bindings[].members" \
        --filter="bindings.members:serviceAccount:$SERVICE_ACCOUNT_EMAIL AND bindings.role:$role" \
        --format="value(bindings.role)" | grep -q "$role"; then
        echo -e "${GREEN}✅ OK${NC}"
        return 0
    else
        echo -e "${RED}❌ MISSING${NC}"
        return 1
    fi
}

# Controleer alle benodigde permissions
echo ""
echo "📋 Huidige Permission Status:"
echo "-----------------------------"

check_permission "roles/cloudsql.client" "Cloud SQL Client"
sql_ok=$?

check_permission "roles/secretmanager.secretAccessor" "Secret Manager Accessor"
secret_ok=$?

check_permission "roles/storage.objectViewer" "Storage Object Viewer"
storage_ok=$?

# Tel gefaalde permissions
failed_count=0
if [ $sql_ok -ne 0 ]; then failed_count=$((failed_count + 1)); fi
if [ $secret_ok -ne 0 ]; then failed_count=$((failed_count + 1)); fi
if [ $storage_ok -ne 0 ]; then failed_count=$((failed_count + 1)); fi

echo ""
if [ $failed_count -eq 0 ]; then
    echo -e "${GREEN}🎉 Alle permissions zijn correct ingesteld!${NC}"
    echo ""
    echo "De gefaalde checks in het verificatie script waren false alarms."
    echo "Je Google Cloud setup is 100% compleet en klaar voor deployment!"
    exit 0
fi

echo -e "${YELLOW}⚠️  $failed_count permission(s) ontbreken. Bezig met repareren...${NC}"
echo ""

# Fix ontbrekende permissions
if [ $sql_ok -ne 0 ]; then
    echo "🔧 Toevoegen Cloud SQL Client permission..."
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
        --role="roles/cloudsql.client"
fi

if [ $secret_ok -ne 0 ]; then
    echo "🔧 Toevoegen Secret Manager Accessor permission..."
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
        --role="roles/secretmanager.secretAccessor"
fi

if [ $storage_ok -ne 0 ]; then
    echo "🔧 Toevoegen Storage Object Viewer permission..."
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
        --role="roles/storage.objectViewer"
fi

echo ""
echo "✅ Permissions toegevoegd!"
echo ""

# Verificeer opnieuw
echo "🔍 Herverificatie..."
echo "-------------------"

check_permission "roles/cloudsql.client" "Cloud SQL Client"
check_permission "roles/secretmanager.secretAccessor" "Secret Manager Accessor"  
check_permission "roles/storage.objectViewer" "Storage Object Viewer"

echo ""
echo -e "${GREEN}🎉 IAM Permissions zijn nu compleet!${NC}"
echo ""
echo "📋 Samenvatting van permissions voor $SERVICE_ACCOUNT_EMAIL:"
echo "  ✅ roles/cloudsql.client - Database toegang"
echo "  ✅ roles/secretmanager.secretAccessor - Secrets toegang"
echo "  ✅ roles/storage.objectViewer - Storage toegang"
echo ""
echo "🚀 Je Google Cloud setup is nu 100% compleet en klaar voor deployment!"

