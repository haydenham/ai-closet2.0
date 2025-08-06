"""
Google Cloud Storage service for handling file uploads and image management
"""
import os
import uuid
from typing import Optional, List, BinaryIO
from google.cloud import storage
from google.cloud.exceptions import NotFound
from PIL import Image
import io

from app.core.config import settings


class GCPStorageService:
    """Service for managing files in Google Cloud Storage"""
    
    def __init__(self):
        self.client = storage.Client()
        self.images_bucket_name = settings.gcs_bucket_name or f"{settings.google_cloud_project}-fashion-ai-images"
        self.uploads_bucket_name = f"{settings.google_cloud_project}-fashion-ai-uploads"
        
        # Initialize buckets
        self.images_bucket = self.client.bucket(self.images_bucket_name)
        self.uploads_bucket = self.client.bucket(self.uploads_bucket_name)
    
    def upload_clothing_image(
        self, 
        file_data: BinaryIO, 
        filename: str,
        content_type: str = "image/jpeg"
    ) -> tuple[str, str]:
        """
        Upload a clothing image to GCS and return the public URL and filename
        
        Returns:
            tuple: (public_url, stored_filename)
        """
        # Generate unique filename
        file_extension = filename.split('.')[-1].lower()
        unique_filename = f"clothing/{uuid.uuid4()}.{file_extension}"
        
        # Optimize image before upload
        optimized_data = self._optimize_image(file_data, file_extension)
        
        # Upload to GCS
        blob = self.images_bucket.blob(unique_filename)
        blob.upload_from_string(
            optimized_data,
            content_type=content_type
        )
        
        # Make publicly accessible
        blob.make_public()
        
        return blob.public_url, unique_filename
    
    def upload_user_image(
        self, 
        file_data: BinaryIO, 
        user_id: str,
        filename: str,
        content_type: str = "image/jpeg"
    ) -> tuple[str, str]:
        """
        Upload a user's clothing item image
        
        Returns:
            tuple: (public_url, stored_filename)
        """
        # Generate unique filename with user folder
        file_extension = filename.split('.')[-1].lower()
        unique_filename = f"users/{user_id}/{uuid.uuid4()}.{file_extension}"
        
        # Optimize image before upload
        optimized_data = self._optimize_image(file_data, file_extension)
        
        # Upload to uploads bucket
        blob = self.uploads_bucket.blob(unique_filename)
        blob.upload_from_string(
            optimized_data,
            content_type=content_type
        )
        
        # Make publicly accessible
        blob.make_public()
        
        return blob.public_url, unique_filename
    
    def delete_image(self, filename: str, bucket_type: str = "images") -> bool:
        """
        Delete an image from GCS
        
        Args:
            filename: The filename/path in the bucket
            bucket_type: Either "images" or "uploads"
        """
        try:
            bucket = self.images_bucket if bucket_type == "images" else self.uploads_bucket
            blob = bucket.blob(filename)
            blob.delete()
            return True
        except NotFound:
            return False
        except Exception:
            return False
    
    def get_signed_url(
        self, 
        filename: str, 
        bucket_type: str = "images",
        expiration_minutes: int = 60
    ) -> Optional[str]:
        """
        Generate a signed URL for private access to a file
        """
        try:
            bucket = self.images_bucket if bucket_type == "images" else self.uploads_bucket
            blob = bucket.blob(filename)
            
            # Generate signed URL
            url = blob.generate_signed_url(
                expiration=expiration_minutes * 60,  # Convert to seconds
                method='GET'
            )
            return url
        except Exception:
            return None
    
    def list_user_images(self, user_id: str) -> List[dict]:
        """
        List all images for a specific user
        """
        prefix = f"users/{user_id}/"
        blobs = self.uploads_bucket.list_blobs(prefix=prefix)
        
        images = []
        for blob in blobs:
            images.append({
                "filename": blob.name,
                "public_url": blob.public_url,
                "size": blob.size,
                "created": blob.time_created,
                "updated": blob.updated
            })
        
        return images
    
    def _optimize_image(self, file_data: BinaryIO, file_extension: str) -> bytes:
        """
        Optimize image for web delivery
        """
        try:
            # Reset file pointer
            file_data.seek(0)
            
            # Open image with PIL
            image = Image.open(file_data)
            
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'LA', 'P'):
                image = image.convert('RGB')
            
            # Resize if too large (max 1200px on longest side)
            max_size = 1200
            if max(image.size) > max_size:
                image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # Save optimized image to bytes
            output = io.BytesIO()
            
            if file_extension.lower() in ['jpg', 'jpeg']:
                image.save(output, format='JPEG', quality=85, optimize=True)
            elif file_extension.lower() == 'png':
                image.save(output, format='PNG', optimize=True)
            elif file_extension.lower() == 'webp':
                image.save(output, format='WEBP', quality=85, optimize=True)
            else:
                # Default to JPEG
                image.save(output, format='JPEG', quality=85, optimize=True)
            
            return output.getvalue()
            
        except Exception:
            # If optimization fails, return original data
            file_data.seek(0)
            return file_data.read()
    
    def create_thumbnail(
        self, 
        source_filename: str, 
        size: tuple = (300, 300),
        bucket_type: str = "images"
    ) -> Optional[str]:
        """
        Create a thumbnail version of an image
        
        Returns:
            Optional[str]: Public URL of the thumbnail
        """
        try:
            bucket = self.images_bucket if bucket_type == "images" else self.uploads_bucket
            source_blob = bucket.blob(source_filename)
            
            # Download original image
            image_data = source_blob.download_as_bytes()
            image = Image.open(io.BytesIO(image_data))
            
            # Create thumbnail
            image.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Save thumbnail
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=85, optimize=True)
            
            # Upload thumbnail
            thumbnail_filename = source_filename.replace('.', f'_thumb_{size[0]}x{size[1]}.')
            thumbnail_blob = bucket.blob(thumbnail_filename)
            thumbnail_blob.upload_from_string(
                output.getvalue(),
                content_type='image/jpeg'
            )
            thumbnail_blob.make_public()
            
            return thumbnail_blob.public_url
            
        except Exception:
            return None
    
    def get_storage_stats(self) -> dict:
        """
        Get storage usage statistics
        """
        try:
            images_blobs = list(self.images_bucket.list_blobs())
            uploads_blobs = list(self.uploads_bucket.list_blobs())
            
            images_size = sum(blob.size or 0 for blob in images_blobs)
            uploads_size = sum(blob.size or 0 for blob in uploads_blobs)
            
            return {
                "images_bucket": {
                    "count": len(images_blobs),
                    "size_bytes": images_size,
                    "size_mb": round(images_size / (1024 * 1024), 2)
                },
                "uploads_bucket": {
                    "count": len(uploads_blobs),
                    "size_bytes": uploads_size,
                    "size_mb": round(uploads_size / (1024 * 1024), 2)
                },
                "total": {
                    "count": len(images_blobs) + len(uploads_blobs),
                    "size_bytes": images_size + uploads_size,
                    "size_mb": round((images_size + uploads_size) / (1024 * 1024), 2)
                }
            }
        except Exception:
            return {
                "error": "Unable to fetch storage statistics"
            }