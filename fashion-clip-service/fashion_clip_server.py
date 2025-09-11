#!/usr/bin/env python3
"""
Standalone Fashion-CLIP server for Cloud Run deployment.
Provides REST API for fashion image analysis and embedding generation.
"""
import os
import logging
import asyncio
import json
import base64
import io
from typing import Dict, Any, List
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import torch
import numpy as np
from transformers import AutoModel, AutoProcessor, CLIPModel, CLIPProcessor
from PIL import Image

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Request/Response models
class EmbeddingRequest(BaseModel):
    image: str  # Base64 encoded image
    return_features: bool = False

class EmbeddingResponse(BaseModel):
    success: bool
    embedding: List[float]
    category: str = None
    style: List[str] = None
    features: List[str] = None
    processing_time_ms: int
    model_name: str
    error: str = None

class BatchEmbeddingRequest(BaseModel):
    images: List[str]  # List of base64 encoded images
    return_features: bool = False

class BatchEmbeddingResponse(BaseModel):
    success: bool
    results: List[EmbeddingResponse]
    total_processing_time_ms: int
    batch_size: int

# Global model instance
fashion_clip_model = None
model_processor = None
device = "cpu"

# Fashion vocabulary
CLOTHING_CATEGORIES = [
    "t-shirt", "dress shirt", "blouse", "tank top", "crop top",
    "hoodie", "sweater", "cardigan", "blazer", "jacket",
    "jeans", "trousers", "shorts", "skirt", "dress", 
    "sneakers", "boots", "heels", "sandals", "flats",
    "coat", "vest", "jumpsuit", "swimwear", "activewear"
]

STYLE_DESCRIPTORS = [
    "casual", "formal", "business", "sporty", "elegant",
    "vintage", "modern", "bohemian", "edgy", "minimalist",
    "preppy", "streetwear", "romantic", "professional", "trendy"
]

FABRIC_FEATURES = [
    "cotton", "denim", "silk", "wool", "leather",
    "linen", "polyester", "cashmere", "velvet", "lace",
    "knit", "woven", "mesh", "sequined", "embroidered"
]

def load_fashion_clip_model():
    """Load the Fashion-CLIP model with memory optimization."""
    global fashion_clip_model, model_processor
    
    try:
        model_name = "patrickjohncyh/fashion-clip"
        logger.info(f"Loading Fashion-CLIP model: {model_name}")
        
        # Try to load Fashion-CLIP first with memory optimizations
        try:
            fashion_clip_model = AutoModel.from_pretrained(
                model_name, 
                trust_remote_code=True,
                torch_dtype=torch.float16,  # Use half precision to save memory
                low_cpu_mem_usage=True      # Optimize CPU memory usage
            )
            model_processor = AutoProcessor.from_pretrained(model_name, trust_remote_code=True)
            logger.info("Fashion-CLIP model loaded successfully with memory optimization")
        except Exception as e:
            logger.warning(f"Fashion-CLIP failed to load: {e}, falling back to standard CLIP")
            # Fallback to standard CLIP with memory optimization
            model_name = "openai/clip-vit-base-patch32"
            fashion_clip_model = CLIPModel.from_pretrained(
                model_name,
                torch_dtype=torch.float16,
                low_cpu_mem_usage=True
            )
            model_processor = CLIPProcessor.from_pretrained(model_name)
            logger.info("Standard CLIP model loaded as fallback with memory optimization")
        
        # Set to evaluation mode
        fashion_clip_model.eval()
        fashion_clip_model.to(device)
        
        # Force garbage collection to free memory
        import gc
        gc.collect()
        
        # Warm up model
        dummy_image = Image.new('RGB', (224, 224), color='white')
        with torch.no_grad():
            if hasattr(model_processor, 'process'):
                inputs = model_processor.process(images=dummy_image, return_tensors="pt")
            else:
                inputs = model_processor(images=dummy_image, return_tensors="pt")
            
            inputs = {k: v.to(device) for k, v in inputs.items() if isinstance(v, torch.Tensor)}
            
            if hasattr(fashion_clip_model, 'encode_images'):
                _ = fashion_clip_model.encode_images(dummy_image)
            else:
                _ = fashion_clip_model.get_image_features(**inputs)
        
        logger.info("Fashion-CLIP model warmed up successfully")
        
    except Exception as e:
        logger.error(f"Failed to load Fashion-CLIP model: {e}")
        raise e

def generate_embedding(image: Image.Image) -> np.ndarray:
    """Generate embedding for an image."""
    with torch.no_grad():
        try:
            if hasattr(fashion_clip_model, 'encode_images'):
                # Fashion-CLIP method
                embedding = fashion_clip_model.encode_images([image])
                if isinstance(embedding, torch.Tensor):
                    embedding = embedding.cpu().numpy().flatten()
                else:
                    embedding = np.array(embedding).flatten()
            else:
                # Standard CLIP method
                inputs = model_processor(images=image, return_tensors="pt")
                inputs = {k: v.to(device) for k, v in inputs.items()}
                
                image_features = fashion_clip_model.get_image_features(**inputs)
                image_features = torch.nn.functional.normalize(image_features, dim=-1)
                embedding = image_features.cpu().numpy().flatten()
            
            return embedding
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return np.zeros(512)  # Return zero embedding as fallback

def classify_category(image: Image.Image) -> str:
    """Classify clothing category."""
    with torch.no_grad():
        try:
            if hasattr(fashion_clip_model, 'encode_images') and hasattr(fashion_clip_model, 'encode_text'):
                # Fashion-CLIP method
                image_features = fashion_clip_model.encode_images([image])
                text_features = fashion_clip_model.encode_text(CLOTHING_CATEGORIES)
                
                similarities = torch.cosine_similarity(
                    torch.tensor(image_features).unsqueeze(0), 
                    torch.tensor(text_features).unsqueeze(0), 
                    dim=-1
                )
                best_idx = similarities.argmax().item()
                return CLOTHING_CATEGORIES[best_idx]
            else:
                # Standard CLIP method
                inputs = model_processor(
                    images=image,
                    text=CLOTHING_CATEGORIES,
                    return_tensors="pt",
                    padding=True
                )
                inputs = {k: v.to(device) for k, v in inputs.items()}
                
                outputs = fashion_clip_model(**inputs)
                logits = outputs.logits_per_image
                best_idx = logits.argmax().item()
                return CLOTHING_CATEGORIES[best_idx]
                
        except Exception as e:
            logger.error(f"Category classification failed: {e}")
            return 'unknown'

def analyze_style(image: Image.Image) -> List[str]:
    """Analyze style characteristics."""
    with torch.no_grad():
        try:
            if hasattr(fashion_clip_model, 'encode_images'):
                # Fashion-CLIP method
                image_features = fashion_clip_model.encode_images([image])
                text_features = fashion_clip_model.encode_text(STYLE_DESCRIPTORS)
                
                similarities = torch.cosine_similarity(
                    torch.tensor(image_features).unsqueeze(0), 
                    torch.tensor(text_features).unsqueeze(0), 
                    dim=-1
                )
                top_indices = similarities.argsort(descending=True)[:3]
                return [STYLE_DESCRIPTORS[idx] for idx in top_indices]
            else:
                # Standard CLIP method
                inputs = model_processor(
                    images=image,
                    text=STYLE_DESCRIPTORS,
                    return_tensors="pt",
                    padding=True
                )
                inputs = {k: v.to(device) for k, v in inputs.items()}
                
                outputs = fashion_clip_model(**inputs)
                logits = outputs.logits_per_image
                top_indices = logits.argsort(descending=True)[0][:3]
                return [STYLE_DESCRIPTORS[idx] for idx in top_indices]
                
        except Exception as e:
            logger.error(f"Style analysis failed: {e}")
            return []

def detect_features(image: Image.Image) -> List[str]:
    """Detect fabric and texture features."""
    with torch.no_grad():
        try:
            if hasattr(fashion_clip_model, 'encode_images'):
                # Fashion-CLIP method
                image_features = fashion_clip_model.encode_images([image])
                text_features = fashion_clip_model.encode_text(FABRIC_FEATURES)
                
                similarities = torch.cosine_similarity(
                    torch.tensor(image_features).unsqueeze(0), 
                    torch.tensor(text_features).unsqueeze(0), 
                    dim=-1
                )
                
                threshold = 0.3
                high_confidence = similarities > threshold
                return [FABRIC_FEATURES[i] for i, conf in enumerate(high_confidence) if conf]
            else:
                # Standard CLIP method
                inputs = model_processor(
                    images=image,
                    text=FABRIC_FEATURES,
                    return_tensors="pt",
                    padding=True
                )
                inputs = {k: v.to(device) for k, v in inputs.items()}
                
                outputs = fashion_clip_model(**inputs)
                probs = torch.nn.functional.softmax(outputs.logits_per_image, dim=-1)
                
                threshold = 0.1
                high_prob = probs[0] > threshold
                return [FABRIC_FEATURES[i] for i, prob in enumerate(high_prob) if prob]
                
        except Exception as e:
            logger.error(f"Feature detection failed: {e}")
            return []

# Initialize FastAPI app
app = FastAPI(
    title="Fashion-CLIP Service",
    description="Production Fashion-CLIP service for clothing image analysis",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    """Load model on startup."""
    load_fashion_clip_model()

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "model_loaded": fashion_clip_model is not None,
        "device": device
    }

@app.post("/embed", response_model=EmbeddingResponse)
async def generate_embedding_endpoint(request: EmbeddingRequest):
    """Generate embedding for a single image."""
    import time
    start_time = time.time()
    
    try:
        # Decode base64 image
        image_data = base64.b64decode(request.image)
        image = Image.open(io.BytesIO(image_data))
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Generate embedding
        embedding = generate_embedding(image)
        
        # Optional feature analysis
        category = None
        style = None
        features = None
        
        if request.return_features:
            category = classify_category(image)
            style = analyze_style(image)
            features = detect_features(image)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return EmbeddingResponse(
            success=True,
            embedding=embedding.tolist(),
            category=category,
            style=style,
            features=features,
            processing_time_ms=processing_time,
            model_name="fashion-clip-cloud"
        )
        
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        processing_time = int((time.time() - start_time) * 1000)
        
        return EmbeddingResponse(
            success=False,
            embedding=[],
            processing_time_ms=processing_time,
            model_name="fashion-clip-cloud",
            error=str(e)
        )

@app.post("/embed/batch", response_model=BatchEmbeddingResponse)
async def generate_batch_embeddings_endpoint(request: BatchEmbeddingRequest):
    """Generate embeddings for multiple images."""
    import time
    start_time = time.time()
    
    try:
        results = []
        
        for i, image_b64 in enumerate(request.images):
            try:
                # Process individual image
                image_data = base64.b64decode(image_b64)
                image = Image.open(io.BytesIO(image_data))
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                
                embedding = generate_embedding(image)
                
                # Optional features
                category = None
                style = None
                features = None
                
                if request.return_features:
                    category = classify_category(image)
                    style = analyze_style(image)
                    features = detect_features(image)
                
                results.append(EmbeddingResponse(
                    success=True,
                    embedding=embedding.tolist(),
                    category=category,
                    style=style,
                    features=features,
                    processing_time_ms=0,  # Will be set for batch
                    model_name="fashion-clip-cloud"
                ))
                
            except Exception as e:
                logger.error(f"Batch item {i} failed: {e}")
                results.append(EmbeddingResponse(
                    success=False,
                    embedding=[],
                    processing_time_ms=0,
                    model_name="fashion-clip-cloud",
                    error=str(e)
                ))
        
        total_processing_time = int((time.time() - start_time) * 1000)
        
        return BatchEmbeddingResponse(
            success=True,
            results=results,
            total_processing_time_ms=total_processing_time,
            batch_size=len(request.images)
        )
        
    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        total_processing_time = int((time.time() - start_time) * 1000)
        
        return BatchEmbeddingResponse(
            success=False,
            results=[],
            total_processing_time_ms=total_processing_time,
            batch_size=len(request.images)
        )

@app.get("/model/info")
async def get_model_info():
    """Get model information."""
    return {
        "model_loaded": fashion_clip_model is not None,
        "device": device,
        "categories_count": len(CLOTHING_CATEGORIES),
        "styles_count": len(STYLE_DESCRIPTORS),
        "features_count": len(FABRIC_FEATURES),
        "embedding_dim": 512
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
