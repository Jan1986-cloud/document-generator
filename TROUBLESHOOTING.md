# 🔧 Troubleshooting Guide

## Veelvoorkomende Problemen en Oplossingen

### 🚨 Terraform Problemen

#### "Project not found" of "Permission denied"
```bash
# Controleer authenticatie
gcloud auth list
gcloud config set project YOUR_PROJECT_ID

# Controleer project permissions
gcloud projects get-iam-policy YOUR_PROJECT_ID
```

#### "API not enabled"
```bash
# Enable required APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

#### "State bucket already exists"
```bash
# Reset Terraform state
cd terraform
rm -rf .terraform terraform.tfstate*
terraform init
```

### 🐳 Docker/Container Problemen

#### "PYTHONPATH not found" in logs
✅ Opgelost in dit package: Dockerfile heeft correcte PYTHONPATH

#### "Module not found" errors
✅ Opgelost in dit package: Directory structuur gecorrigeerd

#### Container start failures
```bash
# Test lokaal
cd application/document-generator-backend
docker build -t test-backend .
docker run -p 8080:8080 test-backend

# Check logs
docker logs CONTAINER_ID
```

### 🔄 GitHub Actions Problemen

#### "Secret not found"
```bash
# Controleer GitHub secrets
gh secret list --repo YOUR_USERNAME/document-generator

# Voeg ontbrekende secrets toe
gh secret set SECRET_NAME --body "SECRET_VALUE"
```

#### "Service account key invalid"
```bash
# Maak nieuwe service account key
gcloud iam service-accounts keys create new-key.json \
    --iam-account=SERVICE_ACCOUNT_EMAIL

# Convert to base64
base64 -w 0 new-key.json
```

#### "VPC connector not found"
```bash
# Check Terraform outputs
cd terraform
terraform output vpc_connector_name

# Update GitHub secret
gh secret set VPC_CONNECTOR --body "CONNECTOR_NAME"
```

### 🗄️ Database Problemen

#### "Connection refused" to database
```bash
# Check Cloud SQL instance
gcloud sql instances list

# Check VPC connector
gcloud compute networks vpc-access connectors list --region=REGION

# Test connection
gcloud sql connect INSTANCE_NAME --user=postgres
```

#### "Database does not exist"
```bash
# Create database manually
gcloud sql databases create document_generator --instance=INSTANCE_NAME

# Run migrations manually
gcloud run jobs execute migrate-database --region=REGION
```

### 🌐 Networking Problemen

#### "VPC connector creation failed"
```bash
# Check quotas
gcloud compute project-info describe --project=PROJECT_ID

# Check VPC network
gcloud compute networks list

# Recreate VPC connector
gcloud compute networks vpc-access connectors create CONNECTOR_NAME \
    --region=REGION \
    --subnet=SUBNET_NAME \
    --subnet-project=PROJECT_ID
```

#### "Cloud Run service unreachable"
```bash
# Check service status
gcloud run services list --region=REGION

# Check service logs
gcloud logging read "resource.type=cloud_run_revision" --limit=50

# Test health endpoint
curl https://SERVICE_URL/health
```

### 🔐 Authentication Problemen

#### "Service account permissions denied"
```bash
# Check service account roles
gcloud projects get-iam-policy PROJECT_ID \
    --flatten="bindings[].members" \
    --filter="bindings.members:SERVICE_ACCOUNT_EMAIL"

# Add missing roles
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
    --role="roles/cloudsql.client"
```

#### "Secret Manager access denied"
```bash
# Grant Secret Manager access
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
    --role="roles/secretmanager.secretAccessor"
```

### 🔄 Reset Procedures

#### Complete Reset (Nuclear Option)
```bash
# 1. Destroy all infrastructure
cd terraform
terraform destroy -auto-approve

# 2. Clean up Docker images
gcloud artifacts repositories delete document-generator \
    --location=REGION --quiet

# 3. Delete Cloud Run services
gcloud run services delete document-generator-backend --region=REGION --quiet
gcloud run services delete document-generator-frontend --region=REGION --quiet

# 4. Start fresh
cd ..
./deploy.sh
```

#### Partial Reset (Infrastructure Only)
```bash
# Keep application, reset infrastructure
cd terraform
terraform destroy -auto-approve
terraform apply -auto-approve
```

#### Application Reset (Code Only)
```bash
# Keep infrastructure, redeploy application
git add .
git commit -m "Redeploy application"
git push origin main
```

### 📊 Monitoring & Debugging

#### Check Deployment Status
```bash
# Terraform status
cd terraform && terraform show

# GitHub Actions status
gh run list --repo YOUR_USERNAME/document-generator

# Cloud Run services
gcloud run services list --region=REGION

# Database status
gcloud sql instances list
```

#### View Logs
```bash
# Cloud Run logs
gcloud logging read "resource.type=cloud_run_revision" --limit=50

# Cloud SQL logs
gcloud logging read "resource.type=cloudsql_database" --limit=50

# GitHub Actions logs
gh run view RUN_ID --log
```

#### Performance Monitoring
```bash
# Service metrics
gcloud monitoring metrics list --filter="resource.type=cloud_run_revision"

# Database metrics
gcloud monitoring metrics list --filter="resource.type=cloudsql_database"
```

### 🆘 Emergency Contacts
**When All Else Fails**
- Check this troubleshooting guide first
- Review deployment logs: deployment.log
- Check GitHub Actions logs: Repository → Actions tab
- Review Terraform state: terraform/terraform.tfstate
- Google Cloud Console: Check all resources manually

#### Useful Commands for Support
```bash
# Generate support bundle
./generate-support-bundle.sh

# This creates:
# - deployment.log
# - terraform-state.json
# - github-actions-logs.txt
# - cloud-resources-status.txt
```

Remember: Dit deployment package heeft alle bekende problemen opgelost. Als je nog steeds issues hebt, is het waarschijnlijk een configuratie- of permissie-probleem dat met bovenstaande stappen opgelost kan worden.
