#!/bin/bash

# Document Generator - Google Cloud Deployment Script
# This script deploys the complete application to Google Cloud

set -e

# Configuration
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-your-project-id}"
REGION="${GOOGLE_CLOUD_REGION:-europe-west4}"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_EMAIL:-document-generator@${PROJECT_ID}.iam.gserviceaccount.com}"
ARTIFACT_REPO="${ARTIFACT_REPO:-document-generator}"

# Service names
BACKEND_SERVICE="document-generator-backend"
FRONTEND_SERVICE="document-generator-frontend"

# Database configuration
DB_INSTANCE_NAME="document-generator-db"
DB_NAME="document_generator"
DB_USER="postgres"

echo "🚀 Starting deployment to Google Cloud..."
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
    cloudresourcemanager.googleapis.com

# Create service account if it doesn't exist
echo "👤 Creating service account..."
if ! gcloud iam service-accounts describe $SERVICE_ACCOUNT_EMAIL &> /dev/null; then
    gcloud iam service-accounts create document-generator \
        --display-name="Document Generator Service Account" \
        --description="Service account for Document Generator application"
    
    # Grant necessary permissions
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
        --role="roles/cloudsql.client"
    
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
        --role="roles/secretmanager.secretAccessor"
    
    # Create and download service account key
    gcloud iam service-accounts keys create ./credentials/service-account.json \
        --iam-account=$SERVICE_ACCOUNT_EMAIL
    
    echo "✅ Service account created and key saved to ./credentials/service-account.json"
else
    echo "✅ Service account already exists"
fi

# Create Cloud SQL instance
echo "🗄️ Setting up Cloud SQL instance..."
if ! gcloud sql instances describe $DB_INSTANCE_NAME &> /dev/null; then
    gcloud sql instances create $DB_INSTANCE_NAME \
        --database-version=POSTGRES_15 \
        --tier=db-f1-micro \
        --region=$REGION \
        --storage-type=SSD \
        --storage-size=10GB \
        --storage-auto-increase \
        --backup-start-time=03:00 \
        --maintenance-window-day=SUN \
        --maintenance-window-hour=04 \
        --deletion-protection
    
    echo "✅ Cloud SQL instance created"
else
    echo "✅ Cloud SQL instance already exists"
fi

# Create database
echo "📊 Creating database..."
if ! gcloud sql databases describe $DB_NAME --instance=$DB_INSTANCE_NAME &> /dev/null; then
    gcloud sql databases create $DB_NAME --instance=$DB_INSTANCE_NAME
    echo "✅ Database created"
else
    echo "✅ Database already exists"
fi

# Set database password
echo "🔐 Setting database password..."
DB_PASSWORD=$(openssl rand -base64 32)
gcloud sql users set-password $DB_USER \
    --instance=$DB_INSTANCE_NAME \
    --password=$DB_PASSWORD

# Store database password in Secret Manager
echo "🔒 Storing database password in Secret Manager..."
echo -n "$DB_PASSWORD" | gcloud secrets create db-password --data-file=-

# Create database connection string secret
DB_CONNECTION_STRING="postgresql://$DB_USER:$DB_PASSWORD@/cloudsql/$PROJECT_ID:$REGION:$DB_INSTANCE_NAME/$DB_NAME"
echo -n "$DB_CONNECTION_STRING" | gcloud secrets create database-url --data-file=-

# Store JWT secret
echo "🔑 Creating JWT secret..."
JWT_SECRET=$(openssl rand -base64 64)
echo -n "$JWT_SECRET" | gcloud secrets create jwt-secret-key --data-file=-

# Build and deploy backend
echo "🏗️ Building and deploying backend..."
cd document-generator-backend

# Build the container image
IMAGE_URL="$REGION-docker.pkg.dev/$PROJECT_ID/$ARTIFACT_REPO/$BACKEND_SERVICE"
gcloud builds submit --tag $IMAGE_URL

# Deploy to Cloud Run
gcloud run deploy $BACKEND_SERVICE \
    --image $IMAGE_URL \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --service-account $SERVICE_ACCOUNT_EMAIL \
    --add-cloudsql-instances $PROJECT_ID:$REGION:$DB_INSTANCE_NAME \
    --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID" \
    --set-secrets "DATABASE_URL=database-url:latest,JWT_SECRET_KEY=jwt-secret-key:latest" \
    --memory 1Gi \
    --cpu 1 \
    --concurrency 80 \
    --timeout 300 \
    --max-instances 10 \
    --port 8080

# Get backend URL
BACKEND_URL=$(gcloud run services describe $BACKEND_SERVICE --region=$REGION --format="value(status.url)")
echo "✅ Backend deployed at: $BACKEND_URL"

cd ..

# Build and deploy frontend
echo "🎨 Building and deploying frontend..."
cd document-generator-frontend

# Update environment variables for production
cat > .env.production << EOF
VITE_API_BASE_URL=${BACKEND_URL}/api
VITE_APP_NAME=Document Generator
VITE_APP_VERSION=1.0.0
VITE_GOOGLE_CLOUD_PROJECT=$PROJECT_ID
VITE_ENABLE_REGISTRATION=true
VITE_ENABLE_DARK_MODE=true
VITE_ENABLE_NOTIFICATIONS=true
VITE_DEBUG_MODE=false
EOF

# Build the container image
IMAGE_URL_FRONTEND="$REGION-docker.pkg.dev/$PROJECT_ID/$ARTIFACT_REPO/$FRONTEND_SERVICE"
gcloud builds submit --tag $IMAGE_URL_FRONTEND

# Deploy to Cloud Run
gcloud run deploy $FRONTEND_SERVICE \
    --image $IMAGE_URL_FRONTEND \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --concurrency 80 \
    --timeout 60 \
    --max-instances 5 \
    --port 8080

# Get frontend URL
FRONTEND_URL=$(gcloud run services describe $FRONTEND_SERVICE --region=$REGION --format="value(status.url)")
echo "✅ Frontend deployed at: $FRONTEND_URL"

cd ..

# Run database migrations
echo "🔄 Running database migrations..."
gcloud run jobs deploy migrate-database \
    --image $IMAGE_URL \
    --region $REGION \
    --service-account $SERVICE_ACCOUNT_EMAIL \
    --set-cloudsql-instances $PROJECT_ID:$REGION:$DB_INSTANCE_NAME \
    --set-secrets "DATABASE_URL=database-url:latest" \
    --command "python" \
    --args "-c,\"from src.models.database import db; db.create_all(); print('Database tables created successfully')\""

gcloud run jobs execute migrate-database --region $REGION --wait

echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "📋 Deployment Summary:"
echo "  Frontend URL: $FRONTEND_URL"
echo "  Backend URL:  $BACKEND_URL"
echo "  Database:     $PROJECT_ID:$REGION:$DB_INSTANCE_NAME"
echo ""
echo "🔧 Next Steps:"
echo "  1. Update your Google Docs templates with the correct sharing permissions"
echo "  2. Configure Google Drive API credentials"
echo "  3. Set up Google Sheets synchronization"
echo "  4. Create your first organization and user account"
echo ""
echo "📚 Access the application at: $FRONTEND_URL"

