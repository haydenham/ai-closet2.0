# Deployment Guide - AI Closet 2.0

This guide covers deploying AI Closet 2.0 to production environments.

## Prerequisites

- Google Cloud Platform account with billing enabled
- Docker installed locally
- Google Cloud CLI (`gcloud`) installed and authenticated
- Domain name for production deployment (optional)

## Environment Setup

### 1. Google Cloud Project Setup

```bash
# Create a new project (or use existing)
gcloud projects create ai-closet-prod --name="AI Closet Production"

# Set the project
gcloud config set project ai-closet-prod

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable vision.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable storage.googleapis.com
```

### 2. Service Account Creation

```bash
# Create service account for backend
gcloud iam service-accounts create ai-closet-backend \
    --description="AI Closet Backend Service Account" \
    --display-name="AI Closet Backend"

# Grant necessary permissions
gcloud projects add-iam-policy-binding ai-closet-prod \
    --member="serviceAccount:ai-closet-backend@ai-closet-prod.iam.gserviceaccount.com" \
    --role="roles/run.invoker"

gcloud projects add-iam-policy-binding ai-closet-prod \
    --member="serviceAccount:ai-closet-backend@ai-closet-prod.iam.gserviceaccount.com" \
    --role="roles/vision.imageAnnotator"

# Download service account key
gcloud iam service-accounts keys create credentials.json \
    --iam-account=ai-closet-backend@ai-closet-prod.iam.gserviceaccount.com
```

## Database Setup

### 1. Cloud SQL PostgreSQL

```bash
# Create Cloud SQL instance
gcloud sql instances create ai-closet-db \
    --database-version=POSTGRES_14 \
    --tier=db-f1-micro \
    --region=us-central1

# Create database
gcloud sql databases create ai_closet --instance=ai-closet-db

# Create user
gcloud sql users create ai_closet_user \
    --instance=ai-closet-db \
    --password=SECURE_PASSWORD_HERE
```

### 2. Redis (Cloud Memorystore)

```bash
# Create Redis instance
gcloud redis instances create ai-closet-cache \
    --size=1 \
    --region=us-central1 \
    --redis-version=redis_6_x
```

## Fashion-CLIP Service Deployment

### 1. Deploy Fashion-CLIP to Cloud Run

```bash
cd fashion-clip-service

# Build and deploy
gcloud run deploy fashion-clip-service \
    --source . \
    --platform managed \
    --region us-central1 \
    --memory 8Gi \
    --cpu 4 \
    --concurrency 1 \
    --timeout 300 \
    --max-instances 10 \
    --allow-unauthenticated
```

### 2. Get Service URL

```bash
# Get the deployed service URL
gcloud run services describe fashion-clip-service \
    --region us-central1 \
    --format 'value(status.url)'
```

## Backend Deployment

### 1. Prepare Environment Variables

Create `backend/.env.production`:

```bash
# Database
DATABASE_URL=postgresql://ai_closet_user:SECURE_PASSWORD@/ai_closet?host=/cloudsql/ai-closet-prod:us-central1:ai-closet-db

# Redis
REDIS_URL=redis://REDIS_INTERNAL_IP:6379

# Security
SECRET_KEY=your-super-secure-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Google Cloud
GOOGLE_CLOUD_PROJECT=ai-closet-prod
GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json

# Fashion-CLIP Service
FASHION_CLIP_SERVICE_URL=https://fashion-clip-service-hash-uc.a.run.app

# File uploads
MAX_FILE_SIZE=10485760
UPLOAD_DIR=/app/uploads
```

### 2. Deploy Backend to Cloud Run

```bash
cd backend

# Create Cloud Run service with SQL connection
gcloud run deploy ai-closet-backend \
    --source . \
    --platform managed \
    --region us-central1 \
    --memory 2Gi \
    --cpu 2 \
    --concurrency 80 \
    --timeout 60 \
    --max-instances 20 \
    --add-cloudsql-instances ai-closet-prod:us-central1:ai-closet-db \
    --set-env-vars-file .env.production \
    --allow-unauthenticated
```

### 3. Run Database Migrations

```bash
# Connect to Cloud Run service for migration
gcloud run jobs create migrate-db \
    --image gcr.io/ai-closet-prod/ai-closet-backend \
    --region us-central1 \
    --task-timeout 300 \
    --command "alembic upgrade head"

# Execute the migration
gcloud run jobs execute migrate-db --region us-central1
```

## Frontend Deployment

### 1. Build for Production

```bash
cd frontend

# Install dependencies
npm ci --production

# Set environment variables
echo "VITE_API_URL=https://ai-closet-backend-hash-uc.a.run.app" > .env.production

# Build
npm run build
```

### 2. Deploy to Cloud Storage + CDN

```bash
# Create storage bucket
gsutil mb gs://ai-closet-frontend-prod

# Enable website hosting
gsutil web set -m index.html -e 404.html gs://ai-closet-frontend-prod

# Upload build files
gsutil -m cp -r dist/* gs://ai-closet-frontend-prod

# Make bucket public
gsutil iam ch allUsers:objectViewer gs://ai-closet-frontend-prod
```

### 3. Optional: Custom Domain with Load Balancer

```bash
# Reserve static IP
gcloud compute addresses create ai-closet-ip --global

# Create HTTPS load balancer (follow GCP console for SSL certificate setup)
# Point your domain to the reserved IP address
```

## Monitoring and Logging

### 1. Enable Cloud Monitoring

```bash
# Cloud Monitoring is enabled by default for Cloud Run
# View logs and metrics in the GCP Console

# Set up alerting for high error rates
gcloud alpha monitoring policies create --policy-from-file=monitoring-policy.yaml
```

### 2. Health Checks

The backend includes health check endpoints:
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed system status

## Security Configuration

### 1. API Security

```bash
# Create API Gateway for rate limiting (optional)
gcloud api-gateway gateways create ai-closet-gateway \
    --api=ai-closet-api \
    --api-config=ai-closet-config \
    --location=us-central1
```

### 2. CORS Configuration

Update `backend/app/core/config.py` for production:

```python
CORS_ORIGINS = [
    "https://yourdomain.com",
    "https://www.yourdomain.com",
]
```

## Backup Strategy

### 1. Database Backups

```bash
# Enable automated backups
gcloud sql instances patch ai-closet-db \
    --backup-start-time=03:00 \
    --retained-backups-count=7
```

### 2. File Storage Backups

```bash
# Create backup bucket
gsutil mb gs://ai-closet-backups-prod

# Set up lifecycle management for cost optimization
gsutil lifecycle set backup-lifecycle.json gs://ai-closet-backups-prod
```

## Cost Optimization

### 1. Cloud Run Optimization

- Set minimum instances to 0 for cost savings
- Use request-based billing
- Monitor and adjust memory/CPU based on usage

### 2. Database Optimization

- Use Cloud SQL proxy for connection pooling
- Consider read replicas for high-read workloads
- Monitor query performance

### 3. Storage Optimization

- Use Cloud Storage lifecycle policies
- Compress images before upload
- Consider CDN caching for static assets

## Troubleshooting

### Common Issues

1. **Fashion-CLIP Service Timeout**
   - Increase timeout to 300s
   - Check memory allocation (8GB recommended)
   - Monitor cold start times

2. **Database Connection Issues**
   - Verify Cloud SQL proxy configuration
   - Check connection limits
   - Review VPC network settings

3. **CORS Errors**
   - Update CORS_ORIGINS in backend configuration
   - Verify frontend API URL configuration

### Monitoring Commands

```bash
# View logs
gcloud logs read "resource.type=cloud_run_revision" --limit 50

# Monitor service metrics
gcloud run services describe ai-closet-backend --region us-central1

# Check deployment status
gcloud run revisions list --service ai-closet-backend --region us-central1
```

## Rollback Procedures

### Backend Rollback

```bash
# List revisions
gcloud run revisions list --service ai-closet-backend --region us-central1

# Route traffic to previous revision
gcloud run services update-traffic ai-closet-backend \
    --to-revisions REVISION_NAME=100 \
    --region us-central1
```

### Database Rollback

```bash
# Restore from backup
gcloud sql backups restore BACKUP_ID \
    --restore-instance=ai-closet-db
```

---

For additional support, refer to the Google Cloud documentation or create an issue in the project repository.
