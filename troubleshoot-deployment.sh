#!/bin/bash

# GitHub Actions Troubleshooter
# Dit script helpt je de deployment failure te diagnosticeren

echo "🔍 GitHub Actions Deployment Troubleshooter"
echo "==========================================="

# Kleuren
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo -e "${RED}❌ Deployment Status: FAILED${NC}"
echo "   - test-backend: Failed (exit code 1)"
echo "   - test-frontend: Failed (exit code 1)"
echo "   - deploy-staging: Skipped"
echo "   - deploy-production: Skipped"

echo ""
echo -e "${BLUE}🔍 Diagnose Checklist:${NC}"
echo "====================="

echo ""
echo "1. GitHub Repository Secrets"
echo "   Ga naar: https://github.com/Jan1986-cloud/document-generator/settings/secrets/actions"
echo ""
echo "   Controleer of deze secrets bestaan:"
echo "   [ ] GOOGLE_CLOUD_PROJECT"
echo "   [ ] GOOGLE_CLOUD_REGION" 
echo "   [ ] GOOGLE_CLOUD_SA_KEY"
echo "   [ ] CLOUDSQL_INSTANCE"

echo ""
echo "2. Service Account Key Genereren"
echo "   Als GOOGLE_CLOUD_SA_KEY ontbreekt:"
echo ""
echo "   gcloud iam service-accounts keys create deployment-sa-key.json \\"
echo "       --iam-account=deployment-sa@gen-lang-client-0695866337.iam.gserviceaccount.com"
echo ""
echo "   base64 -w 0 deployment-sa-key.json"

echo ""
echo "3. Gedetailleerde Logs Bekijken"
echo "   Ga naar: https://github.com/Jan1986-cloud/document-generator/actions"
echo "   Klik op de gefaalde workflow"
echo "   Klik op 'test-backend' job"
echo "   Expand alle stappen voor error details"

echo ""
echo -e "${YELLOW}⚡ Snelle Oplossingen:${NC}"
echo "===================="

echo ""
echo "Optie A: Fix Secrets (Aanbevolen)"
echo "   1. Voeg ontbrekende GitHub secrets toe"
echo "   2. Re-run de gefaalde workflow"
echo "   3. Monitor de nieuwe deployment"

echo ""
echo "Optie B: Bypass Tests (Tijdelijk)"
echo "   1. Edit .github/workflows/deploy.yml"
echo "   2. Comment out 'needs: [test-backend, test-frontend]'"
echo "   3. Commit en push"

echo ""
echo -e "${GREEN}📋 Benodigde Secret Values:${NC}"
echo "=========================="
echo ""
echo "GOOGLE_CLOUD_PROJECT=gen-lang-client-0695866337"
echo "GOOGLE_CLOUD_REGION=europe-west4"
echo "GOOGLE_CLOUD_SA_KEY=[base64 van deployment-sa-key.json]"
echo "CLOUDSQL_INSTANCE=gen-lang-client-0695866337:europe-west4:document-generator-db"

echo ""
echo -e "${BLUE}🎯 Volgende Stappen:${NC}"
echo "=================="
echo "1. Controleer GitHub secrets (5 min)"
echo "2. Bekijk job logs voor specifieke errors (5 min)"
echo "3. Fix identified issues (10 min)"
echo "4. Re-run workflow (1 min)"
echo "5. Monitor nieuwe deployment (10 min)"

echo ""
echo -e "${GREEN}💡 Tips:${NC}"
echo "======="
echo "- GitHub secret names zijn case-sensitive"
echo "- Base64 encoding moet zonder newlines (-w 0)"
echo "- Service account moet deployment permissions hebben"
echo "- Workflow re-run via 'Re-run jobs' button"

echo ""
echo "🔗 Nuttige Links:"
echo "================"
echo "GitHub Secrets: https://github.com/Jan1986-cloud/document-generator/settings/secrets/actions"
echo "GitHub Actions: https://github.com/Jan1986-cloud/document-generator/actions"
echo "Google Cloud Console: https://console.cloud.google.com"

