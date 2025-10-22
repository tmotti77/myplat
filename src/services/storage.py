"""Object storage service for documents and files using MinIO/S3."""
import asyncio
import hashlib
import mimetypes
from datetime import datetime, timedelta
from pathlib import Path
from typing import BinaryIO, Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse

import aiofiles
from minio import Minio
from minio.error import S3Error

from src.core.config import settings
from src.core.logging import get_logger, LoggerMixin

logger = get_logger(__name__)


class StorageService(LoggerMixin):
    """Object storage service with MinIO/S3 backend."""
    
    def __init__(self):
        self._client: Optional[Minio] = None
        self._bucket_name = settings.MINIO_BUCKET_NAME
    
    async def initialize(self):
        """Initialize MinIO client and ensure bucket exists."""
        try:
            # Create MinIO client
            self._client = Minio(
                endpoint=settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE,
                region="us-east-1"  # Default region
            )
            
            # Ensure bucket exists
            await self._ensure_bucket_exists()
            
            self.log_info("Storage service initialized", bucket=self._bucket_name)
            
        except Exception as e:
            self.log_error("Failed to initialize storage service", error=e)
            raise
    
    async def cleanup(self):
        """Clean up storage service."""
        try:
            # MinIO client doesn't need explicit cleanup
            self.log_info("Storage service cleaned up")
        except Exception as e:
            self.log_error("Error during storage cleanup", error=e)
    
    async def _ensure_bucket_exists(self):
        """Ensure the bucket exists, create if it doesn't."""
        try:
            # Run in thread pool since MinIO client is synchronous
            bucket_exists = await asyncio.get_event_loop().run_in_executor(
                None, self._client.bucket_exists, self._bucket_name
            )
            
            if not bucket_exists:
                await asyncio.get_event_loop().run_in_executor(
                    None, self._client.make_bucket, self._bucket_name
                )
                self.log_info("Created storage bucket", bucket=self._bucket_name)
            
        except Exception as e:
            self.log_error("Failed to ensure bucket exists", error=e)
            raise
    
    async def health_check(self) -> bool:
        """Check storage service health."""
        try:
            # Try to list objects in bucket
            await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: list(self._client.list_objects(self._bucket_name, max_keys=1))
            )
            return True
        except Exception as e:
            self.log_error("Storage health check failed", error=e)
            return False
    
    def _generate_object_key(self, tenant_id: str, document_id: str, 
                           filename: str, version: int = 1) -> str:
        """Generate unique object key for storage."""
        
        # Create hierarchical key: tenant/documents/doc_id/version/filename
        safe_filename = self._sanitize_filename(filename)
        return f"{tenant_id}/documents/{document_id}/v{version}/{safe_filename}"
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for storage."""
        
        # Remove or replace unsafe characters
        unsafe_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', ' ']
        safe_filename = filename
        
        for char in unsafe_chars:
            safe_filename = safe_filename.replace(char, '_')
        
        # Limit length
        if len(safe_filename) > 100:
            name, ext = Path(safe_filename).stem, Path(safe_filename).suffix
            safe_filename = name[:95-len(ext)] + ext
        
        return safe_filename
    
    async def upload_file(
        self,
        file_data: Union[bytes, BinaryIO, str],  # File path, bytes, or file object
        tenant_id: str,
        document_id: str,
        filename: str,
        content_type: Optional[str] = None,
        version: int = 1,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """Upload file to object storage."""
        
        try:
            # Generate object key
            object_key = self._generate_object_key(tenant_id, document_id, filename, version)
            
            # Determine content type
            if not content_type:
                content_type, _ = mimetypes.guess_type(filename)
                if not content_type:
                    content_type = "application/octet-stream"
            
            # Prepare metadata
            file_metadata = {
                "tenant_id": tenant_id,
                "document_id": document_id,
                "original_filename": filename,
                "version": str(version),
                "upload_time": datetime.utcnow().isoformat(),
            }
            
            if metadata:
                file_metadata.update(metadata)
            
            # Handle different input types
            if isinstance(file_data, str):
                # File path
                async with aiofiles.open(file_data, 'rb') as f:
                    content = await f.read()
            elif isinstance(file_data, bytes):
                content = file_data
            else:
                # File object
                content = file_data.read()
                if hasattr(file_data, 'seek'):
                    file_data.seek(0)  # Reset file pointer
            
            # Calculate file hash
            file_hash = hashlib.sha256(content).hexdigest()
            file_size = len(content)
            
            file_metadata["file_hash"] = file_hash
            file_metadata["file_size"] = str(file_size)
            
            # Upload to MinIO
            await asyncio.get_event_loop().run_in_executor(
                None,
                self._client.put_object,
                self._bucket_name,
                object_key,
                content,
                file_size,
                content_type,
                file_metadata
            )
            
            self.log_info(
                "File uploaded successfully",
                object_key=object_key,
                size_bytes=file_size,
                content_type=content_type
            )
            
            return {
                "object_key": object_key,
                "bucket": self._bucket_name,
                "file_hash": file_hash,
                "file_size": file_size,
                "content_type": content_type,
                "url": self._get_object_url(object_key)
            }
            
        except Exception as e:
            self.log_error(
                "File upload failed",
                tenant_id=tenant_id,
                document_id=document_id,
                filename=filename,
                error=e
            )
            raise
    
    async def download_file(self, object_key: str) -> bytes:
        """Download file from object storage."""
        
        try:
            # Download from MinIO
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                self._client.get_object,
                self._bucket_name,
                object_key
            )
            
            content = response.read()
            response.close()
            response.release_conn()
            
            self.log_info("File downloaded successfully", object_key=object_key)
            return content
            
        except S3Error as e:
            if e.code == "NoSuchKey":
                self.log_warning("File not found", object_key=object_key)
                raise FileNotFoundError(f"File not found: {object_key}")
            else:
                self.log_error("File download failed", object_key=object_key, error=e)
                raise
        except Exception as e:
            self.log_error("File download failed", object_key=object_key, error=e)
            raise
    
    async def delete_file(self, object_key: str) -> bool:
        """Delete file from object storage."""
        
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                self._client.remove_object,
                self._bucket_name,
                object_key
            )
            
            self.log_info("File deleted successfully", object_key=object_key)
            return True
            
        except S3Error as e:
            if e.code == "NoSuchKey":
                self.log_warning("File not found for deletion", object_key=object_key)
                return False
            else:
                self.log_error("File deletion failed", object_key=object_key, error=e)
                raise
        except Exception as e:
            self.log_error("File deletion failed", object_key=object_key, error=e)
            raise
    
    async def file_exists(self, object_key: str) -> bool:
        """Check if file exists in storage."""
        
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                self._client.stat_object,
                self._bucket_name,
                object_key
            )
            return True
            
        except S3Error as e:
            if e.code == "NoSuchKey":
                return False
            else:
                self.log_error("File existence check failed", object_key=object_key, error=e)
                raise
        except Exception as e:
            self.log_error("File existence check failed", object_key=object_key, error=e)
            raise
    
    async def get_file_info(self, object_key: str) -> Dict[str, any]:
        """Get file metadata and information."""
        
        try:
            stat = await asyncio.get_event_loop().run_in_executor(
                None,
                self._client.stat_object,
                self._bucket_name,
                object_key
            )
            
            return {
                "object_key": object_key,
                "size": stat.size,
                "content_type": stat.content_type,
                "etag": stat.etag,
                "last_modified": stat.last_modified,
                "metadata": stat.metadata,
                "version_id": stat.version_id,
            }
            
        except S3Error as e:
            if e.code == "NoSuchKey":
                raise FileNotFoundError(f"File not found: {object_key}")
            else:
                self.log_error("Get file info failed", object_key=object_key, error=e)
                raise
        except Exception as e:
            self.log_error("Get file info failed", object_key=object_key, error=e)
            raise
    
    async def list_files(
        self,
        prefix: str = "",
        max_keys: int = 1000,
        tenant_id: Optional[str] = None
    ) -> List[Dict[str, any]]:
        """List files in storage with optional filtering."""
        
        try:
            # Add tenant prefix if specified
            if tenant_id:
                prefix = f"{tenant_id}/{prefix}" if prefix else tenant_id
            
            objects = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: list(self._client.list_objects(
                    self._bucket_name,
                    prefix=prefix,
                    max_keys=max_keys
                ))
            )
            
            files = []
            for obj in objects:
                files.append({
                    "object_key": obj.object_name,
                    "size": obj.size,
                    "last_modified": obj.last_modified,
                    "etag": obj.etag,
                    "is_dir": obj.is_dir,
                })
            
            return files
            
        except Exception as e:
            self.log_error("List files failed", prefix=prefix, error=e)
            raise
    
    async def generate_presigned_url(
        self,
        object_key: str,
        expiry: timedelta = timedelta(hours=1),
        method: str = "GET"
    ) -> str:
        """Generate presigned URL for file access."""
        
        try:
            url = await asyncio.get_event_loop().run_in_executor(
                None,
                self._client.presigned_get_object,
                self._bucket_name,
                object_key,
                expiry
            )
            
            self.log_info(
                "Presigned URL generated",
                object_key=object_key,
                expiry_hours=expiry.total_seconds() / 3600
            )
            
            return url
            
        except Exception as e:
            self.log_error("Presigned URL generation failed", object_key=object_key, error=e)
            raise
    
    async def copy_file(self, source_key: str, dest_key: str) -> bool:
        """Copy file within storage."""
        
        try:
            copy_source = f"{self._bucket_name}/{source_key}"
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                self._client.copy_object,
                self._bucket_name,
                dest_key,
                copy_source
            )
            
            self.log_info("File copied successfully", source=source_key, dest=dest_key)
            return True
            
        except Exception as e:
            self.log_error("File copy failed", source=source_key, dest=dest_key, error=e)
            raise
    
    async def get_storage_usage(self, tenant_id: Optional[str] = None) -> Dict[str, any]:
        """Get storage usage statistics."""
        
        try:
            prefix = tenant_id if tenant_id else ""
            
            objects = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: list(self._client.list_objects(
                    self._bucket_name,
                    prefix=prefix,
                    recursive=True
                ))
            )
            
            total_size = 0
            file_count = 0
            file_types = {}
            
            for obj in objects:
                if not obj.is_dir:
                    file_count += 1
                    total_size += obj.size
                    
                    # Count by file extension
                    ext = Path(obj.object_name).suffix.lower()
                    if ext:
                        file_types[ext] = file_types.get(ext, 0) + 1
            
            return {
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "file_count": file_count,
                "file_types": file_types,
                "tenant_id": tenant_id,
            }
            
        except Exception as e:
            self.log_error("Storage usage calculation failed", tenant_id=tenant_id, error=e)
            raise
    
    def _get_object_url(self, object_key: str) -> str:
        """Get public URL for object (if bucket is public)."""
        
        # Construct URL based on MinIO endpoint
        if settings.MINIO_SECURE:
            protocol = "https"
        else:
            protocol = "http"
        
        return f"{protocol}://{settings.MINIO_ENDPOINT}/{self._bucket_name}/{object_key}"
    
    async def cleanup_old_files(
        self,
        tenant_id: str,
        older_than: timedelta = timedelta(days=90)
    ) -> int:
        """Clean up old files for a tenant."""
        
        try:
            cutoff_date = datetime.utcnow() - older_than
            
            objects = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: list(self._client.list_objects(
                    self._bucket_name,
                    prefix=tenant_id,
                    recursive=True
                ))
            )
            
            deleted_count = 0
            for obj in objects:
                if obj.last_modified < cutoff_date:
                    try:
                        await self.delete_file(obj.object_name)
                        deleted_count += 1
                    except Exception as e:
                        self.log_error("Failed to delete old file", object_key=obj.object_name, error=e)
            
            self.log_info(
                "Old files cleanup completed",
                tenant_id=tenant_id,
                deleted_count=deleted_count,
                cutoff_date=cutoff_date.isoformat()
            )
            
            return deleted_count
            
        except Exception as e:
            self.log_error("Old files cleanup failed", tenant_id=tenant_id, error=e)
            raise


# Global storage service instance
storage_service = StorageService()