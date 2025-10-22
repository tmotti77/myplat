"""Storage service for file management."""

import os
import shutil
import uuid
from pathlib import Path
from typing import Dict, Optional, Any, Union, List
from datetime import datetime

from ..core.config import settings
from ..core.logging import get_logger, LoggerMixin

logger = get_logger(__name__)


class StorageService(LoggerMixin):
    """Service for file storage operations."""
    
    def __init__(self):
        self.base_path = Path(settings.UPLOAD_DIR)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
    async def store_file(
        self, 
        file_path: str, 
        content: bytes, 
        content_type: Optional[str] = None
    ) -> str:
        """Store file content and return storage URL."""
        
        try:
            # Create full path
            full_path = self.base_path / file_path
            
            # Create directory structure
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            with open(full_path, 'wb') as f:
                f.write(content)
            
            # Generate storage URL (simplified)
            storage_url = f"file://{full_path.absolute()}"
            
            self.log_info(
                "File stored successfully",
                file_path=file_path,
                size_bytes=len(content),
                content_type=content_type
            )
            
            return storage_url
            
        except Exception as e:
            self.log_error("File storage failed", file_path=file_path, error=e)
            raise
    
    async def get_file(self, file_path: str) -> Optional[bytes]:
        """Retrieve file content."""
        
        try:
            full_path = self.base_path / file_path
            
            if not full_path.exists():
                self.log_warning("File not found", file_path=file_path)
                return None
            
            with open(full_path, 'rb') as f:
                content = f.read()
            
            self.log_info("File retrieved", file_path=file_path, size_bytes=len(content))
            return content
            
        except Exception as e:
            self.log_error("File retrieval failed", file_path=file_path, error=e)
            return None
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete file."""
        
        try:
            full_path = self.base_path / file_path
            
            if full_path.exists():
                if full_path.is_file():
                    full_path.unlink()
                elif full_path.is_dir():
                    shutil.rmtree(full_path)
                
                self.log_info("File deleted", file_path=file_path)
                return True
            else:
                self.log_warning("File not found for deletion", file_path=file_path)
                return False
                
        except Exception as e:
            self.log_error("File deletion failed", file_path=file_path, error=e)
            return False
    
    async def file_exists(self, file_path: str) -> bool:
        """Check if file exists."""
        
        try:
            full_path = self.base_path / file_path
            return full_path.exists()
            
        except Exception as e:
            self.log_error("File existence check failed", file_path=file_path, error=e)
            return False
    
    async def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get file information."""
        
        try:
            full_path = self.base_path / file_path
            
            if not full_path.exists():
                return None
            
            stat = full_path.stat()
            
            return {
                "path": file_path,
                "size": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_ctime),
                "modified_at": datetime.fromtimestamp(stat.st_mtime),
                "is_file": full_path.is_file(),
                "is_directory": full_path.is_dir()
            }
            
        except Exception as e:
            self.log_error("File info retrieval failed", file_path=file_path, error=e)
            return None
    
    async def list_files(self, directory_path: str = "") -> List[Dict[str, Any]]:
        """List files in directory."""
        
        try:
            full_path = self.base_path / directory_path
            
            if not full_path.exists() or not full_path.is_dir():
                return []
            
            files = []
            for item in full_path.iterdir():
                stat = item.stat()
                files.append({
                    "name": item.name,
                    "path": str(item.relative_to(self.base_path)),
                    "size": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime),
                    "modified_at": datetime.fromtimestamp(stat.st_mtime),
                    "is_file": item.is_file(),
                    "is_directory": item.is_dir()
                })
            
            return files
            
        except Exception as e:
            self.log_error("Directory listing failed", directory_path=directory_path, error=e)
            return []
    
    async def cleanup_old_files(self, days: int = 30) -> Dict[str, int]:
        """Clean up old temporary files."""
        
        try:
            cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
            deleted_count = 0
            freed_bytes = 0
            
            for root, dirs, files in os.walk(self.base_path):
                for file in files:
                    file_path = Path(root) / file
                    if file_path.stat().st_mtime < cutoff_time:
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        deleted_count += 1
                        freed_bytes += file_size
            
            self.log_info(
                "Cleanup completed",
                deleted_files=deleted_count,
                freed_bytes=freed_bytes
            )
            
            return {
                "deleted_files": deleted_count,
                "freed_bytes": freed_bytes
            }
            
        except Exception as e:
            self.log_error("Cleanup failed", error=e)
            raise
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage usage statistics."""
        
        try:
            total_size = 0
            file_count = 0
            dir_count = 0
            
            for root, dirs, files in os.walk(self.base_path):
                dir_count += len(dirs)
                for file in files:
                    file_path = Path(root) / file
                    total_size += file_path.stat().st_size
                    file_count += 1
            
            # Get disk usage
            disk_usage = shutil.disk_usage(self.base_path)
            
            return {
                "total_files": file_count,
                "total_directories": dir_count,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "disk_total_bytes": disk_usage.total,
                "disk_used_bytes": disk_usage.used,
                "disk_free_bytes": disk_usage.free,
                "disk_usage_percent": round((disk_usage.used / disk_usage.total) * 100, 2)
            }
            
        except Exception as e:
            self.log_error("Storage stats failed", error=e)
            return {}
    
    async def health_check(self) -> Dict[str, Any]:
        """Check storage service health."""
        
        health = {
            "status": "healthy",
            "base_path": str(self.base_path),
            "writable": False,
            "readable": False
        }
        
        try:
            # Test write
            test_file = self.base_path / f"health_check_{uuid.uuid4()}.tmp"
            test_content = b"health check"
            
            with open(test_file, 'wb') as f:
                f.write(test_content)
            health["writable"] = True
            
            # Test read
            with open(test_file, 'rb') as f:
                read_content = f.read()
            health["readable"] = read_content == test_content
            
            # Cleanup test file
            test_file.unlink()
            
            # Get storage stats
            stats = await self.get_storage_stats()
            health.update(stats)
            
        except Exception as e:
            health["status"] = "unhealthy"
            health["error"] = str(e)
        
        return health


# Global storage service instance
storage_service = StorageService()