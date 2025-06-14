#!/bin/bash

# GitHub Secrets Setup Helper
# Dit script helpt je met het configureren van GitHub secrets

echo "🔐 GitHub Secrets Setup Helper"
echo "=============================="

PROJECT_ID="gen-lang-client-0695866337"
REGION="europe-west4"

# Kleuren
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo -e "${BLUE}📋 Benodigde GitHub Repository Secrets:${NC}"
echo "========================================"

echo ""
echo "1. GOOGLE_CLOUD_PROJECT"
echo -e "   Value: ${GREEN}$PROJECT_ID${NC}"

echo ""
echo "2. GOOGLE_CLOUD_REGION"  
echo -e "   Value: ${GREEN}$REGION${NC}"

echo ""
echo "3. CLOUDSQL_INSTANCE"
echo -e "   Value: ${GREEN}$PROJECT_ID:$REGION:document-generator-db${NC}"

echo ""
echo "4. GOOGLE_CLOUD_SA_KEY"
echo "   Dit is de base64 encoded service account key voor deployment."

# Controleer of deployment-sa key bestaat
if [ -f "deployment-sa-key.json" ]; then
    echo -e "   ${GREEN}✅ deployment-sa-key.json gevonden${NC}"
    echo "   Base64 value:"
    echo -e "   ${YELLOW}$(base64 -w 0 deployment-sa-key.json)${NC}"
else
    echo -e "   ${YELLOW}⚠️  deployment-sa-key.json niet gevonden${NC}"
    echo ""
    echo "   Maak eerst een key aan:"
    echo "   gcloud iam service-accounts keys create deployment-sa-key.json \\"
    echo "       --iam-account=deployment-sa@$PROJECT_ID.iam.gserviceaccount.com"
    echo ""
    echo "   Dan converteer naar base64:"
    echo "   base64 -w 0 deployment-sa-key.json"
fi

echo ""
echo -e "${BLUE}🔧 Stappen om secrets toe te voegen:${NC}"
echo "=================================="
echo "1. Ga naar: https://github.com/Jan1986-cloud/document-generator"
echo "2. Klik op 'Settings' tab"
echo "3. Ga naar 'Secrets and variables' → 'Actions'"
echo "4. Klik 'New repository secret' voor elke secret hierboven"

echo ""
echo -e "${BLUE}📝 Template Bestanden:${NC}"
echo "====================="

if [ -f "github-secrets-template.txt" ]; then
    echo -e "${GREEN}✅ github-secrets-template.txt${NC}"
    echo "Inhoud:"
    cat github-secrets-template.txt
else
    echo -e "${YELLOW}⚠️  github-secrets-template.txt niet gevonden${NC}"
fi

echo ""
echo -e "${BLUE}🚀 Na het instellen van secrets:${NC}"
echo "==============================="
echo "1. Push een commit naar main branch:"
echo "   git add ."
echo "   git commit -m 'Configure deployment'"
echo "   git push origin main"
echo ""
echo "2. Monitor deployment in GitHub Actions:"
echo "   https://github.com/Jan1986-cloud/document-generator/actions"
echo ""
echo "3. Controleer Cloud Run services:"
echo "   gcloud run services list --project=$PROJECT_ID"

echo ""
echo -e "${GREEN}🎯 Je bent klaar voor deployment!${NC}"

