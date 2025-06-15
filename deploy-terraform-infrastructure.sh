#!/bin/bash

# Complete Terraform Infrastructure Deployment
# Voor Document Generator App op Google Cloud

set -e

# Kleuren
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🏗️  Document Generator - Terraform Infrastructure Setup${NC}"
echo "============================================================"

# Configuratie
PROJECT_ID="gen-lang-client-0695866337"
REGION="europe-west4"
ZONE="europe-west4-a"
ENVIRONMENT="production"
NOTIFICATION_EMAIL="jan@pvmonteur.nl"

echo ""
echo -e "${YELLOW}📋 Configuratie:${NC}"
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Environment: $ENVIRONMENT"
echo "Notification Email: $NOTIFICATION_EMAIL"

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

# Check Terraform installation
echo "Checking Terraform installation..."
if ! command -v terraform &> /dev/null; then
    echo -e "${RED}❌ Terraform not installed${NC}"
    echo "Install from: https://www.terraform.io/downloads.html"
    exit 1
fi
echo -e "${GREEN}✅ Terraform installed: $(terraform version -json | jq -r .terraform_version)${NC}"

echo ""
echo -e "${BLUE}🪣 Step 1: Terraform State Bucket${NC}"
echo "=================================="

STATE_BUCKET="terraform-state-document-generator-$PROJECT_ID"
echo "Creating state bucket: $STATE_BUCKET"

# Check if bucket exists
if gsutil ls -b gs://$STATE_BUCKET >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  State bucket already exists${NC}"
else
    echo "Creating new state bucket..."
    gsutil mb -p $PROJECT_ID -c STANDARD -l $REGION gs://$STATE_BUCKET
    gsutil versioning set on gs://$STATE_BUCKET
    echo -e "${GREEN}✅ State bucket created${NC}"
fi

echo ""
echo -e "${BLUE}📝 Step 2: Terraform Configuration${NC}"
echo "=================================="

# Create terraform directory if it doesn't exist
mkdir -p terraform
cd terraform

# Copy Terraform files
echo "Setting up Terraform files..."
cp /home/ubuntu/upload/main.tf .
cp /home/ubuntu/upload/variables.tf .

# Create terraform.tfvars
echo "Creating terraform.tfvars..."
cat > terraform.tfvars << EOF
project_id         = "$PROJECT_ID"
region            = "$REGION"
zone              = "$ZONE"
environment       = "$ENVIRONMENT"
notification_email = "$NOTIFICATION_EMAIL"
db_tier           = "db-f1-micro"
db_disk_size      = 20
min_instances     = 0
max_instances     = 10
cpu_limit         = "1000m"
memory_limit      = "512Mi"
enable_backup     = true
enable_monitoring = true
EOF

# Update backend configuration in main.tf
echo "Updating backend configuration..."
sed -i "s/terraform-state-document-generator/$STATE_BUCKET/g" main.tf

echo -e "${GREEN}✅ Terraform configuration ready${NC}"

echo ""
echo -e "${BLUE}🚀 Step 3: Terraform Deployment${NC}"
echo "==============================="

echo "Initializing Terraform..."
terraform init

echo ""
echo "Planning infrastructure deployment..."
terraform plan -var-file="terraform.tfvars" -out=tfplan

echo ""
echo -e "${YELLOW}⚠️  Ready to deploy infrastructure. This will create:${NC}"
echo "- Cloud SQL PostgreSQL database"
echo "- VPC network with private connectivity"
echo "- Storage buckets for documents/templates/backups"
echo "- Service accounts with proper IAM"
echo "- Monitoring and alerting"
echo "- Artifact Registry for Docker images"
echo ""
echo "Continue with deployment? (y/n)"
read -r response

if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo ""
    echo "Applying Terraform configuration..."
    terraform apply tfplan
    
    echo ""
    echo -e "${GREEN}🎉 Infrastructure deployment completed!${NC}"
    
    echo ""
    echo -e "${BLUE}📊 Deployment Outputs:${NC}"
    echo "===================="
    terraform output
    
    # Save outputs to file for GitHub Actions
    echo ""
    echo "Saving outputs for GitHub Actions..."
    terraform output -json > ../terraform-outputs.json
    
    echo ""
    echo -e "${GREEN}✅ Infrastructure ready for application deployment${NC}"
    
else
    echo ""
    echo -e "${YELLOW}⏸️  Deployment cancelled${NC}"
    exit 0
fi

echo ""
echo -e "${BLUE}🔧 Step 4: Post-Deployment Setup${NC}"
echo "==============================="

# Get important outputs
DB_CONNECTION=$(terraform output -raw database_connection_name)
VPC_CONNECTOR=$(terraform output -raw vpc_connector_name)
APP_SA_EMAIL=$(terraform output -raw app_service_account_email)

echo "Database Connection: $DB_CONNECTION"
echo "VPC Connector: $VPC_CONNECTOR"
echo "App Service Account: $APP_SA_EMAIL"

# Update GitHub secrets with new infrastructure info
echo ""
echo "Updating GitHub secrets with infrastructure info..."

# Create updated secrets template
cat > ../github-secrets-infrastructure.txt << EOF
# Updated GitHub Secrets with Terraform Infrastructure

GOOGLE_CLOUD_PROJECT=$PROJECT_ID
GOOGLE_CLOUD_REGION=$REGION
CLOUDSQL_INSTANCE=$DB_CONNECTION
VPC_CONNECTOR=$VPC_CONNECTOR
APP_SERVICE_ACCOUNT=$APP_SA_EMAIL

# Service Account Key (use existing deployment-sa key)
GOOGLE_CLOUD_SA_KEY=[Use existing base64 encoded key]
EOF

echo ""
echo -e "${GREEN}🎯 Next Steps:${NC}"
echo "============="
echo "1. Update GitHub repository secrets with new infrastructure values"
echo "2. Update GitHub Actions workflow to use VPC connector"
echo "3. Trigger new deployment"
echo ""
echo "Files created:"
echo "- terraform-outputs.json (for reference)"
echo "- github-secrets-infrastructure.txt (updated secrets)"

echo ""
echo -e "${BLUE}🔗 Useful Commands:${NC}"
echo "=================="
echo "# View infrastructure:"
echo "terraform show"
echo ""
echo "# Update infrastructure:"
echo "terraform plan -var-file=\"terraform.tfvars\""
echo "terraform apply"
echo ""
echo "# Destroy infrastructure (if needed):"
echo "terraform destroy -var-file=\"terraform.tfvars\""

echo ""
echo -e "${GREEN}🎉 Terraform infrastructure deployment completed successfully!${NC}"
echo "Your Document Generator app infrastructure is now ready for deployment."

