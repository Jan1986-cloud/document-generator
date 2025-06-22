#!/bin/bash

# Document Generator - Complete Deployment Script
# Dit script deployt de volledige applicatie naar Google Cloud

set -e

# Kleuren voor output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 Document Generator - Complete Deployment${NC}"
echo "=============================================="

# Check if config.yaml exists
if [ ! -f "config.yaml" ]; then
    echo -e "${RED}❌ config.yaml niet gevonden!${NC}"
    echo "Kopieer config.yaml.template naar config.yaml en pas de instellingen aan."
    exit 1
fi

# Parse config.yaml (simplified - in real implementation would use yq)
PROJECT_ID=$(grep "id:" config.yaml | head -1 | sed 's/.*id: *"\([^"]*\)".*/\1/')
REGION=$(grep "region:" config.yaml | head -1 | sed 's/.*region: *"\([^"]*\)".*/\1/')
ENVIRONMENT=$(grep "environment:" config.yaml | head -1 | sed 's/.*environment: *"\([^"]*\)".*/\1/')

echo -e "${YELLOW}📋 Configuratie:${NC}"
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Environment: $ENVIRONMENT"

echo ""
echo -e "${BLUE}🔍 Pre-deployment Checks${NC}"
echo "========================="

# Check gcloud authentication
echo "Checking gcloud authentication..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${RED}❌ Not authenticated with gcloud${NC}"
    echo "Run: gcloud auth login"
    exit 1
fi
echo -e "${GREEN}✅ gcloud authenticated${NC}"

# Check project access
echo "Checking project access..."
if ! gcloud projects describe $PROJECT_ID >/dev/null 2>&1; then
    echo -e "${RED}❌ Cannot access project $PROJECT_ID${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Project access confirmed${NC}"

# Check Terraform
echo "Checking Terraform..."
if ! command -v terraform &> /dev/null; then
    echo -e "${RED}❌ Terraform not installed${NC}"
    echo "Install from: https://www.terraform.io/downloads.html"
    exit 1
fi
echo -e "${GREEN}✅ Terraform available${NC}"


echo -e "${BLUE}🏗️  Step 1: Infrastructure Deployment${NC}"
echo "====================================="

cd terraform

# Create terraform.tfvars from config.yaml
echo "Generating terraform.tfvars from config.yaml..."
cat > terraform.tfvars << EOF
project_id         = "$PROJECT_ID"
region            = "$REGION"
environment       = "$ENVIRONMENT"
notification_email = "$(grep "notification_email:" ../config.yaml | sed 's/.*notification_email: *"\([^"]*\)".*/\1/')"
db_tier           = "$(grep "tier:" ../config.yaml | sed 's/.*tier: *"\([^"]*\)".*/\1/')"
db_disk_size      = $(grep "disk_size:" ../config.yaml | sed 's/.*disk_size: *\([0-9]*\).*/\1/')
EOF

# Initialize and apply Terraform
# Clean up any existing local Terraform data to avoid backend configuration errors
# (equivalent to running "rm -rf terraform/.terraform*" from the repository root)
echo "Initializing Terraform..."
rm -rf .terraform*
terraform init -reconfigure

echo "Planning infrastructure..."
terraform plan -var-file="terraform.tfvars" -out=tfplan

echo "Applying infrastructure..."
terraform apply tfplan

echo "Saving Terraform outputs..."
terraform output -json > ../terraform-outputs.json

cd ..

echo -e "${GREEN}✅ Infrastructure deployed${NC}"


echo -e "${BLUE}🔧 Step 2: Application Deployment${NC}"
echo "================================="

# Extract Terraform outputs
DB_CONNECTION=$(jq -r '.database_connection_name.value' terraform-outputs.json)
VPC_CONNECTOR=$(jq -r '.vpc_connector_name.value' terraform-outputs.json)
APP_SA_EMAIL=$(jq -r '.app_service_account_email.value' terraform-outputs.json)
DEPLOY_SA_EMAIL=$(jq -r '.deploy_service_account_email.value' terraform-outputs.json)

echo "Database Connection: $DB_CONNECTION"
echo "VPC Connector: $VPC_CONNECTOR"
echo "App Service Account: $APP_SA_EMAIL"
echo "Deploy Service Account: $DEPLOY_SA_EMAIL"

# Create service account key for deployment
echo "Creating deployment service account key..."
gcloud iam service-accounts keys create deployment-sa-key.json \
    --iam-account=$DEPLOY_SA_EMAIL

# Convert to base64
SA_KEY_BASE64=$(base64 -w 0 deployment-sa-key.json)


echo -e "${BLUE}🔐 Step 3: GitHub Secrets Setup${NC}"
echo "==============================="

echo "Creating GitHub secrets configuration..."
cat > github-secrets-setup.txt << EOF
# GitHub Repository Secrets Configuration
# Ga naar: https://github.com/Jan1986-cloud/document-generator/settings/secrets/actions

# Voeg deze secrets toe:

GOOGLE_CLOUD_PROJECT=$PROJECT_ID
GOOGLE_CLOUD_REGION=$REGION
GOOGLE_CLOUD_SA_KEY=$SA_KEY_BASE64
CLOUDSQL_INSTANCE=$DB_CONNECTION
VPC_CONNECTOR=$VPC_CONNECTOR
SERVICE_ACCOUNT_EMAIL=$APP_SA_EMAIL
DEPLOY_SERVICE_ACCOUNT_EMAIL=$DEPLOY_SA_EMAIL

# Database secrets (automatisch aangemaakt door Terraform)
# Deze zijn al beschikbaar in Secret Manager
EOF


echo -e "${BLUE}📦 Step 4: Code Deployment${NC}"
echo "=========================="

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "Initializing git repository..."
    git init
    git remote add origin https://github.com/Jan1986-cloud/document-generator.git
fi

# Copy fixed application files
echo "Copying corrected application files..."
cp -r application/* .

# Commit and push
echo "Committing changes..."
git add .
git commit -m "Deploy corrected Document Generator application"

echo "Pushing to GitHub..."
git push origin main


echo -e "${GREEN}🎉 Deployment Completed Successfully!${NC}"
echo "===================================="


echo -e "${BLUE}📋 Next Steps:${NC}"
echo "=============="
echo "1. Configure GitHub secrets using: github-secrets-setup.txt"
echo "2. Monitor deployment at: https://github.com/Jan1986-cloud/document-generator/actions"
echo "3. Access your application URLs (will be available after GitHub Actions completes)"


echo -e "${BLUE}🔗 Useful Commands:${NC}"
echo "=================="
echo "# Monitor deployment:"
echo "gh run list --repo Jan1986-cloud/document-generator"

echo "# View infrastructure:"
echo "cd terraform && terraform show"

echo "# Update configuration:"
echo "# Edit config.yaml and run: ./deploy.sh"


echo -e "${GREEN}✅ All done! Your Document Generator is being deployed.${NC}"
