# Fashion AI Platform - GCP Deployment Guide

## 🎯 Overview

This guide provides step-by-step instructions for deploying the Fashion AI Platform on Google Cloud Platform with a focus on scalability, reliability, and maintainability.

## 📋 Prerequisites

### Required Tools
- Google Cloud SDK (`gcloud`)
- Terraform >= 1.0
- Docker
- Python 3.9+
- Node.js 18+ (for frontend)

### GCP Setup
```bash
# Install Google Cloud SDK
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Authenticate
gcloud auth login
gcloud auth application-default login

# Create project (replace with your project ID)
export PROJECT_ID="fashion-ai-production"
gcloud projects create $PROJECT_ID
gcloud config set project $PROJECT_ID

# Enable billing (required for most services)
# This must be done through the GCP Console
```

## 🏗️ Infrastructure Deployment

### Step 1: Enable Required APIs
```bash
# Enable all required Google Cloud APIs
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  sqladmin.googleapis.com \
  storage.googleapis.com \
  secretmanager.googleapis.com \
  vision.googleapis.com \
  redis.googleapis.com \
  monitoring.googleapis.com \
  logging.googleapis.com \
  cloudtrace.googleapis.com \
  cloudfunctions.googleapis.com \
  pubsub.googleapis.com \
  scheduler.googleapis.com \
  dns.googleapis.com \
  servicenetworking.googleapis.com
```

### Step 2: Deploy Infrastructure with Terraform
```bash
# Navigate to terraform directory
cd terraform

# Initialize Terraform
terraform init

# Create terraform.tfvars file
cat > terraform.tfvars << EOF
project_id  = "$PROJECT_ID"
region      = "us-central1"
environment = "prod"
app_name    = "fashion-ai"
EOF

# Plan deployment
terraform plan

# Deploy infrastructure
terraform apply
```

### Step 3: Configure Secrets
```bash
# Create secrets in Secret Manager
gcloud secrets create jwt-secret-key --data-file=<(openssl rand -base64 64)
gcloud secrets create db-password --data-file=<(openssl rand -base64 32)

# Grant access to Cloud Run service account
SERVICE_ACCOUNT=$(terraform output -raw service_account_email)
gcloud secrets add-iam-policy-binding jwt-secret-key \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding db-password \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor"
```

## 🚀 Application Deployment

### Step 1: Build and Deploy Backend
```bash
# Navigate to backend directory
cd backend

# Build Docker image
gcloud builds submit --tag gcr.io/$PROJECT_ID/fashion-ai-backend:latest

# Deploy to Cloud Run
gcloud run deploy fashion-ai-backend \
  --image gcr.io/$PROJECT_ID/fashion-ai-backend:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --service-account $SERVICE_ACCOUNT \
  --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID \
  --set-env-vars ENVIRONMENT=production \
  --set-env-vars CLOUD_SQL_CONNECTION_NAME=$(terraform output -raw database_connection_name) \
  --add-cloudsql-instances $(terraform output -raw database_connection_name) \
  --memory 2Gi \
  --cpu 2 \
  --concurrency 80 \
  --max-instances 1000 \
  --min-instances 2
```

### Step 2: Run Database Migrations
```bash
# Create a Cloud Run job for migrations
gcloud run jobs create migrate-db \
  --image gcr.io/$PROJECT_ID/fashion-ai-backend:latest \
  --region us-central1 \
  --service-account $SERVICE_ACCOUNT \
  --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID \
  --set-env-vars CLOUD_SQL_CONNECTION_NAME=$(terraform output -raw database_connection_name) \
  --add-cloudsql-instances $(terraform output -raw database_connection_name) \
  --command "python" \
  --args "-m,alembic,upgrade,head"

# Execute migration
gcloud run jobs execute migrate-db --region us-central1 --wait
```

### Step 3: Seed Initial Data
```bash
# Create seeding job
gcloud run jobs create seed-data \
  --image gcr.io/$PROJECT_ID/fashion-ai-backend:latest \
  --region us-central1 \
  --service-account $SERVICE_ACCOUNT \
  --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID \
  --set-env-vars CLOUD_SQL_CONNECTION_NAME=$(terraform output -raw database_connection_name) \
  --add-cloudsql-instances $(terraform output -raw database_connection_name) \
  --command "python" \
  --args "app/scripts/seed_quiz_data.py"

# Execute seeding
gcloud run jobs execute seed-data --region us-central1 --wait
```

## 📊 Monitoring Setup

### Step 1: Configure Monitoring Dashboards
```bash
# Create custom dashboard for application metrics
gcloud monitoring dashboards create --config-from-file=monitoring/dashboard-config.json
```

### Step 2: Set Up Alerting Policies
```bash
# Create alerting policies
gcloud alpha monitoring policies create --policy-from-file=monitoring/alert-policies.yaml
```

### Step 3: Configure Log-based Metrics
```bash
# Create log-based metrics for application insights
gcloud logging metrics create quiz_completion_rate \
  --description="Rate of quiz completions" \
  --log-filter='resource.type="cloud_run_revision" AND jsonPayload.event="quiz_completed"'

gcloud logging metrics create error_rate \
  --description="Application error rate" \
  --log-filter='resource.type="cloud_run_revision" AND severity>=ERROR'
```

## 🔧 Performance Optimization

### Database Optimization
```sql
-- Connect to Cloud SQL instance
gcloud sql connect fashion-ai-prod --user=postgres

-- Create performance indexes
CREATE INDEX CONCURRENTLY idx_quiz_responses_user_created 
ON quiz_responses(user_id, completed_at DESC);

CREATE INDEX CONCURRENTLY idx_clothing_items_gender_category_active 
ON quiz_clothing_items(gender, category, is_active) 
WHERE is_active = true;

CREATE INDEX CONCURRENTLY idx_clothing_items_features_gin 
ON quiz_clothing_items USING GIN(features);

-- Analyze tables for query optimization
ANALYZE quiz_clothing_items;
ANALYZE quiz_responses;
ANALYZE style_categories;
```

### Cloud Run Optimization
```bash
# Update Cloud Run service with optimized settings
gcloud run services update fashion-ai-backend \
  --region us-central1 \
  --cpu-throttling \
  --execution-environment gen2 \
  --memory 4Gi \
  --cpu 2 \
  --concurrency 100 \
  --max-instances 1000 \
  --min-instances 5
```

## 🔐 Security Configuration

### Step 1: Configure IAM Policies
```bash
# Create custom role for application
gcloud iam roles create fashionAiBackendRole \
  --project=$PROJECT_ID \
  --title="Fashion AI Backend Role" \
  --description="Custom role for Fashion AI backend services" \
  --permissions="cloudsql.instances.connect,storage.objects.create,storage.objects.get,secretmanager.versions.access"

# Assign role to service account
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="projects/$PROJECT_ID/roles/fashionAiBackendRole"
```

### Step 2: Configure Cloud Armor
```bash
# Create security policy
gcloud compute security-policies create fashion-ai-security-policy \
  --description "Security policy for Fashion AI Platform"

# Add rate limiting rule
gcloud compute security-policies rules create 1000 \
  --security-policy fashion-ai-security-policy \
  --expression "true" \
  --action "rate-based-ban" \
  --rate-limit-threshold-count 100 \
  --rate-limit-threshold-interval-sec 60 \
  --ban-duration-sec 600
```

### Step 3: Configure SSL and Domain
```bash
# Create managed SSL certificate
gcloud compute ssl-certificates create fashion-ai-ssl-cert \
  --domains=api.yourdomain.com

# Create load balancer (if using custom domain)
gcloud compute url-maps create fashion-ai-lb \
  --default-service=fashion-ai-backend

gcloud compute target-https-proxies create fashion-ai-https-proxy \
  --url-map=fashion-ai-lb \
  --ssl-certificates=fashion-ai-ssl-cert
```

## 📈 Scaling Configuration

### Auto-scaling Policies
```yaml
# cloud-run-scaling.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: fashion-ai-backend
  annotations:
    autoscaling.knative.dev/minScale: "5"
    autoscaling.knative.dev/maxScale: "1000"
    autoscaling.knative.dev/target: "70"
    run.googleapis.com/cpu-throttling: "false"
    run.googleapis.com/execution-environment: "gen2"
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/maxScale: "1000"
        run.googleapis.com/execution-environment: "gen2"
    spec:
      containerConcurrency: 100
      timeoutSeconds: 300
      containers:
      - image: gcr.io/PROJECT_ID/fashion-ai-backend:latest
        resources:
          limits:
            cpu: "4"
            memory: "8Gi"
          requests:
            cpu: "2"
            memory: "4Gi"
        env:
        - name: GOOGLE_CLOUD_PROJECT
          value: PROJECT_ID
        - name: ENVIRONMENT
          value: "production"
```

### Database Scaling
```bash
# Create read replicas for production
gcloud sql instances create fashion-ai-read-replica-1 \
  --master-instance-name=fashion-ai-prod \
  --region=us-east1 \
  --tier=db-standard-2

gcloud sql instances create fashion-ai-read-replica-2 \
  --master-instance-name=fashion-ai-prod \
  --region=us-west1 \
  --tier=db-standard-2
```

## 🧪 Testing Deployment

### Health Checks
```bash
# Get Cloud Run service URL
SERVICE_URL=$(gcloud run services describe fashion-ai-backend \
  --region us-central1 --format 'value(status.url)')

# Test health endpoint
curl $SERVICE_URL/health

# Test API endpoints
curl $SERVICE_URL/quiz/categories
```

### Load Testing
```bash
# Install Artillery for load testing
npm install -g artillery

# Create load test configuration
cat > load-test.yml << EOF
config:
  target: '$SERVICE_URL'
  phases:
    - duration: 60
      arrivalRate: 10
    - duration: 120
      arrivalRate: 50
    - duration: 60
      arrivalRate: 100

scenarios:
  - name: "Quiz API Load Test"
    requests:
      - get:
          url: "/health"
      - get:
          url: "/quiz/categories"
      - get:
          url: "/quiz/clothing-items/male/top"
EOF

# Run load test
artillery run load-test.yml
```

## 🔄 CI/CD Pipeline

### Cloud Build Configuration
```yaml
# cloudbuild.yaml
steps:
  # Run tests
  - name: 'python:3.9'
    entrypoint: 'bash'
    args:
      - '-c'
      - |
        pip install -r requirements.txt
        python -m pytest tests/ -v --cov=app --cov-report=xml

  # Build Docker image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/fashion-ai-backend:$COMMIT_SHA', '.']

  # Push to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/fashion-ai-backend:$COMMIT_SHA']

  # Deploy to Cloud Run
  - name: 'gcr.io/cloud-builders/gcloud'
    args:
      - 'run'
      - 'deploy'
      - 'fashion-ai-backend'
      - '--image'
      - 'gcr.io/$PROJECT_ID/fashion-ai-backend:$COMMIT_SHA'
      - '--region'
      - 'us-central1'
      - '--platform'
      - 'managed'

options:
  logging: CLOUD_LOGGING_ONLY
  machineType: 'E2_HIGHCPU_8'

timeout: '1200s'
```

### Set Up Automated Deployment
```bash
# Connect repository to Cloud Build
gcloud builds triggers create github \
  --repo-name=fashion-ai-platform \
  --repo-owner=your-github-username \
  --branch-pattern="^main$" \
  --build-config=cloudbuild.yaml
```

## 📋 Maintenance Tasks

### Regular Maintenance
```bash
# Weekly database maintenance
gcloud sql operations list --instance=fashion-ai-prod
gcloud sql instances patch fashion-ai-prod --maintenance-window-day=SUN --maintenance-window-hour=3

# Monthly cost optimization review
gcloud billing budgets list
gcloud compute instances list --filter="status:RUNNING"

# Quarterly security review
gcloud iam policies list
gcloud compute ssl-certificates list
```

### Backup and Recovery
```bash
# Manual database backup
gcloud sql backups create --instance=fashion-ai-prod

# List available backups
gcloud sql backups list --instance=fashion-ai-prod

# Restore from backup (if needed)
gcloud sql backups restore BACKUP_ID --restore-instance=fashion-ai-prod
```

## 🚨 Troubleshooting

### Common Issues

#### Cloud Run Cold Starts
```bash
# Increase minimum instances
gcloud run services update fashion-ai-backend \
  --region us-central1 \
  --min-instances 10
```

#### Database Connection Issues
```bash
# Check Cloud SQL instance status
gcloud sql instances describe fashion-ai-prod

# Test connection from Cloud Shell
gcloud sql connect fashion-ai-prod --user=postgres
```

#### High Memory Usage
```bash
# Increase memory allocation
gcloud run services update fashion-ai-backend \
  --region us-central1 \
  --memory 8Gi
```

### Monitoring and Debugging
```bash
# View Cloud Run logs
gcloud logs read "resource.type=cloud_run_revision" --limit=50

# View database logs
gcloud sql instances describe fashion-ai-prod --format="value(settings.databaseFlags)"

# Check performance metrics
gcloud monitoring metrics list --filter="metric.type:custom.googleapis.com"
```

## 📊 Cost Optimization

### Cost Monitoring
```bash
# Set up billing alerts
gcloud alpha billing budgets create \
  --billing-account=BILLING_ACCOUNT_ID \
  --display-name="Fashion AI Budget" \
  --budget-amount=1000USD \
  --threshold-rule=percent=0.8,basis=CURRENT_SPEND
```

### Resource Optimization
- Use preemptible instances for batch processing
- Implement intelligent caching strategies
- Optimize database queries and indexes
- Use Cloud Storage lifecycle policies
- Monitor and right-size Cloud Run instances

## 🎯 Production Checklist

- [ ] Infrastructure deployed via Terraform
- [ ] Database migrations completed
- [ ] Initial data seeded
- [ ] SSL certificates configured
- [ ] Monitoring and alerting set up
- [ ] Load testing completed
- [ ] Security policies configured
- [ ] Backup strategy implemented
- [ ] CI/CD pipeline configured
- [ ] Documentation updated
- [ ] Team access configured
- [ ] Cost monitoring enabled

## 📞 Support and Maintenance

### Emergency Contacts
- Platform Team: platform-team@company.com
- On-call Engineer: +1-XXX-XXX-XXXX
- GCP Support: Enterprise Support Plan

### Escalation Procedures
1. Check monitoring dashboards
2. Review recent deployments
3. Check Cloud Status page
4. Contact on-call engineer
5. Escalate to GCP support if needed