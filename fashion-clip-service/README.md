# Fashion-CLIP Microservice

A specialized computer vision microservice for fashion image analysis, deployed independently on Google Cloud Run.

## 🏗️ Architecture

This is a **standalone microservice** that provides fashion-specific image analysis capabilities:

- **Independent Deployment**: Separate from main backend for optimal scaling
- **Specialized Dependencies**: PyTorch + Fashion-CLIP model isolated from main app
- **Cloud Run Optimized**: CPU-only inference, cost-effective auto-scaling
- **RESTful API**: Simple HTTP interface for integration

## 🚀 Quick Deployment

### Prerequisites
- Google Cloud Project with Cloud Run API enabled
- Docker installed locally
- `gcloud` CLI configured

### Deploy to Cloud Run

```bash
# Navigate to service directory
cd fashion-clip-service

# Configure your project
export PROJECT_ID="your-gcp-project-id"

# Deploy
chmod +x deploy.sh
./deploy.sh
```

### Configure Backend Integration

After deployment, add the service URL to your backend environment:

```bash
# backend/.env
FASHION_CLIP_URL="https://fashion-clip-service-xxxxx-uc.a.run.app"
```

## 📡 API Endpoints

### Health Check
```bash
GET /health
```

### Single Image Analysis
```bash
POST /embed
{
  "image": "base64-encoded-image-data",
  "return_features": true
}
```

### Batch Processing
```bash
POST /embed/batch
{
  "images": ["base64-image-1", "base64-image-2"],
  "return_features": true
}
```

### Model Information
```bash
GET /model/info
```

## 🎯 Features

### Fashion-Specialized Analysis
- **Categories**: 25 clothing types (t-shirt, dress, jeans, etc.)
- **Styles**: 15 style descriptors (casual, formal, vintage, etc.)
- **Features**: 15 fabric/texture types (cotton, denim, silk, etc.)

### Advanced Capabilities
- **512-dimensional embeddings** for semantic similarity
- **Confidence scoring** for classification results
- **Batch processing** for efficiency
- **Fallback handling** to standard CLIP if Fashion-CLIP unavailable

## 💰 Cost Optimization

### Cloud Run Configuration
- **Memory**: 2GB (optimized for model loading)
- **CPU**: 2 vCPU (sufficient for inference)
- **Concurrency**: 4 requests per instance
- **Auto-scaling**: 0-10 instances

### Estimated Costs
- **Processing**: ~$100-200/month for production workloads
- **Cold starts**: ~3-5 seconds (model loading)
- **Warm requests**: ~200-500ms per image

## 🔧 Integration

The Fashion-CLIP service integrates with your main backend through the `FashionCLIPService` class:

```python
# backend/app/services/fashion_clip_service.py
service = get_fashion_clip_service()
result = await service.analyze_fashion_item(image_data)
```

### Hybrid Deployment
- **Cloud Run**: Primary production deployment
- **Local Fallback**: Automatic fallback if Cloud Run unavailable
- **Development**: Can run locally during development

## 📊 Performance

### Processing Times
- **Single image**: 200-500ms
- **Batch (4 images)**: 800-1200ms
- **Model loading**: 3-5 seconds (cold start)

### Accuracy Improvements
- ✅ **Eliminates hallucinations** (no more "striped velvet" on plain items)
- ✅ **Fashion-specific vocabulary** understanding
- ✅ **Consistent categorization** across clothing types
- ✅ **Reliable similarity scoring** for outfit matching

## 🧪 Testing

Test the service locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python fashion_clip_server.py

# Test endpoint
curl -X POST "http://localhost:8080/embed" \
  -H "Content-Type: application/json" \
  -d '{"image": "base64-encoded-image"}'
```

## 🔄 Development Workflow

1. **Local Development**: Test changes locally first
2. **Build Image**: `docker build -t fashion-clip-service .`
3. **Deploy**: Run `./deploy.sh` to deploy to Cloud Run
4. **Update Backend**: Update `FASHION_CLIP_URL` in backend config
5. **Test Integration**: Verify backend can communicate with new service

## 🎉 Benefits Over Integrated Approach

| Aspect | Integrated | Microservice |
|--------|------------|--------------|
| **Scaling** | Coupled with backend | Independent scaling |
| **Dependencies** | Mixed with backend deps | Isolated ML dependencies |
| **Deployment** | Monolithic updates | Independent deployments |
| **Resource Usage** | Shared resources | Optimized for ML workloads |
| **Development** | Tightly coupled | Loose coupling |
| **Cost Control** | Hard to optimize | ML-specific optimization |

This microservice architecture provides the flexibility and optimization needed for production ML workloads while maintaining clean separation from your main application logic.
