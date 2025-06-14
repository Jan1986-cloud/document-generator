#!/bin/bash

# Google Cloud Setup Verificatie Script
# Controleer of het setup-gcp script succesvol is uitgevoerd

echo "🔍 Google Cloud Setup Verificatie"
echo "=================================="

PROJECT_ID="gen-lang-client-0695866337"
REGION="europe-west4"

# Kleuren voor output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

success_count=0
total_checks=0

check_item() {
    local description="$1"
    local command="$2"
    total_checks=$((total_checks + 1))
    
    echo -n "Checking: $description... "
    
    if eval "$command" &> /dev/null; then
        echo -e "${GREEN}✅ OK${NC}"
        success_count=$((success_count + 1))
    else
        echo -e "${RED}❌ FAILED${NC}"
    fi
}

echo ""
echo "📋 1. Configuratiebestanden"
echo "----------------------------"
check_item "Production environment file" "test -f .env.production"
check_item "GitHub secrets template" "test -f github-secrets-template.txt"
check_item "Service account credentials" "test -f credentials/service-account.json"

echo ""
echo "🔐 2. Google Cloud Secrets"
echo "---------------------------"
check_item "JWT secret key" "gcloud secrets describe jwt-secret-key --project=$PROJECT_ID"
check_item "JWT staging secret" "gcloud secrets describe jwt-secret-key-staging --project=$PROJECT_ID"
check_item "Database password" "gcloud secrets describe db-password --project=$PROJECT_ID"
check_item "Database staging password" "gcloud secrets describe db-password-staging --project=$PROJECT_ID"
check_item "Database URL" "gcloud secrets describe database-url --project=$PROJECT_ID"
check_item "Database staging URL" "gcloud secrets describe database-url-staging --project=$PROJECT_ID"
check_item "Google API credentials" "gcloud secrets describe google-api-credentials --project=$PROJECT_ID"

echo ""
echo "👤 3. Service Accounts"
echo "----------------------"
check_item "Document Generator SA" "gcloud iam service-accounts describe document-generator@$PROJECT_ID.iam.gserviceaccount.com"
check_item "Deployment SA (existing)" "gcloud iam service-accounts describe deployment-sa@$PROJECT_ID.iam.gserviceaccount.com"

echo ""
echo "🔧 4. Enabled APIs"
echo "------------------"
check_item "Cloud Build API" "gcloud services list --enabled --project=$PROJECT_ID --filter='name:cloudbuild.googleapis.com' --format='value(name)'"
check_item "Cloud Run API" "gcloud services list --enabled --project=$PROJECT_ID --filter='name:run.googleapis.com' --format='value(name)'"
check_item "Cloud SQL API" "gcloud services list --enabled --project=$PROJECT_ID --filter='name:sqladmin.googleapis.com' --format='value(name)'"
check_item "Secret Manager API" "gcloud services list --enabled --project=$PROJECT_ID --filter='name:secretmanager.googleapis.com' --format='value(name)'"
check_item "Google Drive API" "gcloud services list --enabled --project=$PROJECT_ID --filter='name:drive.googleapis.com' --format='value(name)'"
check_item "Google Docs API" "gcloud services list --enabled --project=$PROJECT_ID --filter='name:docs.googleapis.com' --format='value(name)'"

echo ""
echo "🎯 5. IAM Permissions"
echo "---------------------"
check_item "Document Generator SQL permissions" "gcloud projects get-iam-policy $PROJECT_ID --flatten='bindings[].members' --filter='bindings.members:*document-generator* AND bindings.role:roles/cloudsql.client' --format='value(bindings.role)'"
check_item "Document Generator Secret permissions" "gcloud projects get-iam-policy $PROJECT_ID --flatten='bindings[].members' --filter='bindings.members:*document-generator* AND bindings.role:roles/secretmanager.secretAccessor' --format='value(bindings.role)'"

echo ""
echo "📊 Samenvatting"
echo "==============="
echo -e "Geslaagde checks: ${GREEN}$success_count${NC}/$total_checks"

if [ $success_count -eq $total_checks ]; then
    echo -e "${GREEN}🎉 Alle checks geslaagd! Setup is compleet.${NC}"
    echo ""
    echo "✅ Volgende stappen:"
    echo "   1. Update Google API credentials secret met echte credentials"
    echo "   2. Configureer GitHub repository secrets"
    echo "   3. Test de deployment pipeline"
elif [ $success_count -gt $((total_checks / 2)) ]; then
    echo -e "${YELLOW}⚠️  Setup is grotendeels compleet, maar er zijn enkele issues.${NC}"
    echo ""
    echo "🔧 Aanbevolen acties:"
    echo "   1. Controleer de gefaalde items hierboven"
    echo "   2. Run het setup script opnieuw indien nodig"
    echo "   3. Controleer je permissions"
else
    echo -e "${RED}❌ Setup is niet compleet. Veel items zijn gefaald.${NC}"
    echo ""
    echo "🚨 Aanbevolen acties:"
    echo "   1. Controleer of je ingelogd bent: gcloud auth list"
    echo "   2. Controleer je project permissions"
    echo "   3. Run het setup script opnieuw"
fi

echo ""
echo "🔍 Voor gedetailleerde informatie, run:"
echo "   gcloud secrets list --project=$PROJECT_ID"
echo "   gcloud iam service-accounts list --project=$PROJECT_ID"
echo "   gcloud services list --enabled --project=$PROJECT_ID"

