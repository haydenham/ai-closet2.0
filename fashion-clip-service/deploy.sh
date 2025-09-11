#!/bin/bash
"""
Deploy Fashion-CLIP service to Google Cloud Run
Run this from the fashion-clip-service directory
"""

# Configuration
PROJECT_ID="heroic-alpha-468018-r7"  # Update this to your actual GCP project ID
SERVICE_NAME="fashion-clip-service"
REGION="us-central1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Ensure we're in the fashion-clip-service directory
if [ ! -f "fashion_clip_server.py" ]; then
    echo "❌ Error: Please run this script from the fashion-clip-service directory"
    echo "Expected: fashion-clip-service/fashion_clip_server.py should exist"
    exit 1
fi

# Build and push Docker image
echo "🔨 Building Docker image for AMD64 (Cloud Run)..."
docker build --platform linux/amd64 -t ${IMAGE_NAME} .

echo "📤 Pushing to Google Container Registry..."
docker push ${IMAGE_NAME}

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run with optimized memory settings..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --memory 8Gi \
  --cpu 2 \
  --max-instances 10 \
  --concurrency 1 \
  --timeout 600 \
  --project ${PROJECT_ID}

# Get service URL
echo "✅ Deployment complete!"
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format='value(status.url)')
echo "📍 Service URL: ${SERVICE_URL}"

# Test deployment
echo "🧪 Testing deployment..."
curl "${SERVICE_URL}/health"

echo ""
echo "🎉 Fashion-CLIP service deployed successfully!"
echo ""
echo "📝 Add this to your backend/.env file:"
echo "FASHION_CLIP_URL=${SERVICE_URL}"
echo ""
echo "🔧 Update your backend service to use the Cloud Run endpoint!"
