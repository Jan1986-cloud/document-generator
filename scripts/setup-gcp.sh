#!/bin/bash

# Document Generator - Google Cloud Setup Script
# This script sets up the initial Google Cloud configuration and secrets

set -e

# Configuration
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-your-project-id}"
REGION="${GOOGLE_CLOUD_REGION:-europe-west4}"
SERVICE_ACCOUNT_NAME="document-generator"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "🔧 Setting up Google Cloud configuration..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"

# Check if gcloud is installed and authenticated
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Not authenticated with gcloud. Please run 'gcloud auth login' first."
    exit 1
fi

# Set the project
echo "📋 Setting project to $PROJECT_ID..."
gcloud config set project $PROJECT_ID
gcloud config set compute/region $REGION

# Enable required APIs
echo "🔧 Enabling required Google Cloud APIs..."
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    sqladmin.googleapis.com \
    secretmanager.googleapis.com \
    drive.googleapis.com \
    docs.googleapis.com \
    iam.googleapis.com \
    cloudresourcemanager.googleapis.com \
    compute.googleapis.com

# Create credentials directory
mkdir -p ./credentials

# Create service account if it doesn't exist
echo "👤 Creating service account..."
if ! gcloud iam service-accounts describe $SERVICE_ACCOUNT_EMAIL &> /dev/null; then
    gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
        --display-name="Document Generator Service Account" \
        --description="Service account for Document Generator application"
    
    echo "✅ Service account created"
else
    echo "✅ Service account already exists"
fi

# Grant necessary permissions
echo "🔐 Granting IAM permissions..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/cloudsql.client"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/storage.objectViewer"

# Create service account key
echo "🔑 Creating service account key..."
if [ ! -f "./credentials/service-account.json" ]; then
    gcloud iam service-accounts keys create ./credentials/service-account.json \
        --iam-account=$SERVICE_ACCOUNT_EMAIL
    echo "✅ Service account key created"
else
    echo "✅ Service account key already exists"
fi

# Create secrets for different environments
echo "🔒 Creating secrets..."

# Production secrets
if ! gcloud secrets describe jwt-secret-key &> /dev/null; then
    JWT_SECRET=$(openssl rand -base64 64)
    echo -n "$JWT_SECRET" | gcloud secrets create jwt-secret-key --data-file=-
    echo "✅ JWT secret created"
fi

# Staging secrets
if ! gcloud secrets describe jwt-secret-key-staging &> /dev/null; then
    JWT_SECRET_STAGING=$(openssl rand -base64 64)
    echo -n "$JWT_SECRET_STAGING" | gcloud secrets create jwt-secret-key-staging --data-file=-
    echo "✅ JWT staging secret created"
fi

# Google API credentials (placeholder - user needs to add actual credentials)
if ! gcloud secrets describe google-api-credentials &> /dev/null; then
    echo '{"type": "service_account", "project_id": "placeholder"}' | gcloud secrets create google-api-credentials --data-file=-
    echo "⚠️  Google API credentials secret created with placeholder - UPDATE THIS WITH REAL CREDENTIALS"
fi

# Create Cloud SQL instance configuration
echo "🗄️ Preparing Cloud SQL configuration..."
DB_INSTANCE_NAME="document-generator-db"
DB_NAME="document_generator"
DB_USER="postgres"

# Generate database password
DB_PASSWORD=$(openssl rand -base64 32)

# Store database secrets
if ! gcloud secrets describe db-password &> /dev/null; then
    echo -n "$DB_PASSWORD" | gcloud secrets create db-password --data-file=-
    echo "✅ Database password secret created"
fi

if ! gcloud secrets describe db-password-staging &> /dev/null; then
    DB_PASSWORD_STAGING=$(openssl rand -base64 32)
    echo -n "$DB_PASSWORD_STAGING" | gcloud secrets create db-password-staging --data-file=-
    echo "✅ Database staging password secret created"
fi

# Create database connection strings
DB_CONNECTION_STRING="postgresql://$DB_USER:$DB_PASSWORD@/cloudsql/$PROJECT_ID:$REGION:$DB_INSTANCE_NAME/$DB_NAME"
DB_CONNECTION_STRING_STAGING="postgresql://$DB_USER:$DB_PASSWORD_STAGING@/cloudsql/$PROJECT_ID:$REGION:$DB_INSTANCE_NAME-staging/$DB_NAME"

if ! gcloud secrets describe database-url &> /dev/null; then
    echo -n "$DB_CONNECTION_STRING" | gcloud secrets create database-url --data-file=-
    echo "✅ Database URL secret created"
fi

if ! gcloud secrets describe database-url-staging &> /dev/null; then
    echo -n "$DB_CONNECTION_STRING_STAGING" | gcloud secrets create database-url-staging --data-file=-
    echo "✅ Database staging URL secret created"
fi

# Create environment configuration files
echo "📝 Creating environment configuration files..."

# Production environment
cat > .env.production << EOF
# Document Generator - Production Environment
GOOGLE_CLOUD_PROJECT=$PROJECT_ID
GOOGLE_CLOUD_REGION=$REGION
SERVICE_ACCOUNT_EMAIL=$SERVICE_ACCOUNT_EMAIL
CLOUDSQL_INSTANCE=$PROJECT_ID:$REGION:$DB_INSTANCE_NAME
CLOUDSQL_INSTANCE_STAGING=$PROJECT_ID:$REGION:$DB_INSTANCE_NAME-staging

# Google Docs Template IDs
TEMPLATE_OFFERTE=1rOGgVCxwBTkJoA7fxNJm4TTdF5gt_322EO3vjQh9z1w
TEMPLATE_FACTUUR=1C4g3E4JYEYAPydKtQVzswZe-Unpzp18bsTAtZ4JKuhs
TEMPLATE_FACTUUR_GECOMBINEERD=1zU9w9q7MB4KgrBh4-ETrYqm9qqfjltrZaNI98onlyOw
TEMPLATE_WERKBON=1ZEX2wr7ROj69yq78fPTOQ0Gljx4S-Y2BpbuNIoa1iBc

# Google Drive Output Folder
OUTPUT_FOLDER_ID=1Ug14PibLMQKU8IIoUGTGaLw-ZzvJRhQX
EOF

# GitHub Secrets template
cat > github-secrets-template.txt << EOF
# GitHub Secrets Configuration
# Add these secrets to your GitHub repository settings

GOOGLE_CLOUD_PROJECT=$PROJECT_ID
GOOGLE_CLOUD_SA_KEY=$(base64 -w 0 ./credentials/service-account.json)
SERVICE_ACCOUNT_EMAIL=$SERVICE_ACCOUNT_EMAIL
CLOUDSQL_INSTANCE=$PROJECT_ID:$REGION:$DB_INSTANCE_NAME
CLOUDSQL_INSTANCE_STAGING=$PROJECT_ID:$REGION:$DB_INSTANCE_NAME-staging
EOF

echo ""
echo "✅ Google Cloud setup completed!"
echo ""
echo "📋 Setup Summary:"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Service Account: $SERVICE_ACCOUNT_EMAIL"
echo "  Service Account Key: ./credentials/service-account.json"
echo ""
echo "🔧 Next Steps:"
echo "  1. Update Google API credentials secret with real credentials:"
echo "     gcloud secrets versions add google-api-credentials --data-file=path/to/real-credentials.json"
echo ""
echo "  2. Configure GitHub repository secrets using the template:"
echo "     cat github-secrets-template.txt"
echo ""
echo "  3. Set up Google Docs templates with proper sharing permissions"
echo ""
echo "  4. Run the deployment script:"
echo "     ./deploy-to-gcp.sh"
echo ""
echo "📚 Configuration files created:"
echo "  - .env.production"
echo "  - github-secrets-template.txt"

