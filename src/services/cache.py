"""Redis cache service for caching and session management."""
import json
import pickle
from typing import Any, Optional, Union, List, Dict
from datetime import timedelta

import redis.asyncio as redis
from redis.asyncio import Redis

from src.core.config import settings
from src.core.logging import get_logger, LoggerMixin

logger = get_logger(__name__)


class CacheService(LoggerMixin):
    """Redis-based caching service with connection pooling."""
    
    def __init__(self):
        self._client: Optional[Redis] = None
        self._pool = None
    
    async def initialize(self):
        """Initialize Redis connection pool."""
        try:
            # Create connection pool
            self._pool = redis.ConnectionPool.from_url(
                str(settings.REDIS_URL),
                max_connections=settings.REDIS_POOL_MAX_CONNECTIONS,
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30,
            )
            
            # Create Redis client
            self._client = Redis(connection_pool=self._pool, decode_responses=False)
            
            # Test connection
            await self._client.ping()
            
            self.log_info("Redis cache service initialized")
            
        except Exception as e:
            self.log_error("Failed to initialize Redis cache service", error=e)
            raise
    
    async def cleanup(self):
        """Clean up Redis connections."""
        try:
            if self._client:
                await self._client.close()
            if self._pool:
                await self._pool.disconnect()
            
            self.log_info("Redis cache service cleaned up")
            
        except Exception as e:
            self.log_error("Error during Redis cleanup", error=e)
    
    async def get_client(self) -> Redis:
        """Get Redis client instance."""
        if not self._client:
            await self.initialize()
        return self._client
    
    async def health_check(self) -> bool:
        """Check Redis health."""
        try:
            client = await self.get_client()
            await client.ping()
            return True
        except Exception as e:
            self.log_error("Redis health check failed", error=e)
            return False
    
    # Basic cache operations
    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache."""
        try:
            client = await self.get_client()
            value = await client.get(key)
            
            if value is None:
                return default
            
            # Try to deserialize as JSON first, then pickle
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                try:
                    return pickle.loads(value)
                except (pickle.PickleError, TypeError):
                    # Return as bytes if deserialization fails
                    return value
                    
        except Exception as e:
            self.log_error("Cache get failed", key=key, error=e)
            return default
    
    async def set(self, key: str, value: Any, ttl: Optional[Union[int, timedelta]] = None) -> bool:
        """Set value in cache with optional TTL."""
        try:
            client = await self.get_client()
            
            # Serialize value
            if isinstance(value, (dict, list, tuple)):
                serialized_value = json.dumps(value)
            elif isinstance(value, (str, int, float, bool)):
                serialized_value = json.dumps(value)
            else:
                # Use pickle for complex objects
                serialized_value = pickle.dumps(value)
            
            # Set with TTL
            if ttl:
                if isinstance(ttl, timedelta):
                    ttl = int(ttl.total_seconds())
                await client.setex(key, ttl, serialized_value)
            else:
                await client.set(key, serialized_value)
            
            return True
            
        except Exception as e:
            self.log_error("Cache set failed", key=key, error=e)
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            client = await self.get_client()
            result = await client.delete(key)
            return result > 0
            
        except Exception as e:
            self.log_error("Cache delete failed", key=key, error=e)
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            client = await self.get_client()
            result = await client.exists(key)
            return result > 0
            
        except Exception as e:
            self.log_error("Cache exists check failed", key=key, error=e)
            return False
    
    async def expire(self, key: str, ttl: Union[int, timedelta]) -> bool:
        """Set expiration time for key."""
        try:
            client = await self.get_client()
            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())
            result = await client.expire(key, ttl)
            return result
            
        except Exception as e:
            self.log_error("Cache expire failed", key=key, error=e)
            return False
    
    # Advanced operations
    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values from cache."""
        try:
            client = await self.get_client()
            values = await client.mget(keys)
            
            result = {}
            for key, value in zip(keys, values):
                if value is not None:
                    try:
                        result[key] = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        try:
                            result[key] = pickle.loads(value)
                        except (pickle.PickleError, TypeError):
                            result[key] = value
                else:
                    result[key] = None
            
            return result
            
        except Exception as e:
            self.log_error("Cache get_many failed", keys=keys, error=e)
            return {key: None for key in keys}
    
    async def set_many(self, mapping: Dict[str, Any], ttl: Optional[Union[int, timedelta]] = None) -> bool:
        """Set multiple values in cache."""
        try:
            client = await self.get_client()
            
            # Serialize all values
            serialized_mapping = {}
            for key, value in mapping.items():
                if isinstance(value, (dict, list, tuple)):
                    serialized_mapping[key] = json.dumps(value)
                elif isinstance(value, (str, int, float, bool)):
                    serialized_mapping[key] = json.dumps(value)
                else:
                    serialized_mapping[key] = pickle.dumps(value)
            
            # Use pipeline for atomic operation
            pipe = client.pipeline()
            pipe.mset(serialized_mapping)
            
            if ttl:
                if isinstance(ttl, timedelta):
                    ttl = int(ttl.total_seconds())
                for key in mapping.keys():
                    pipe.expire(key, ttl)
            
            await pipe.execute()
            return True
            
        except Exception as e:
            self.log_error("Cache set_many failed", error=e)
            return False
    
    async def delete_many(self, keys: List[str]) -> int:
        """Delete multiple keys from cache."""
        try:
            client = await self.get_client()
            result = await client.delete(*keys)
            return result
            
        except Exception as e:
            self.log_error("Cache delete_many failed", keys=keys, error=e)
            return 0
    
    # List operations
    async def list_push(self, key: str, value: Any, left: bool = True) -> bool:
        """Push value to list (left or right)."""
        try:
            client = await self.get_client()
            serialized_value = json.dumps(value)
            
            if left:
                await client.lpush(key, serialized_value)
            else:
                await client.rpush(key, serialized_value)
            
            return True
            
        except Exception as e:
            self.log_error("Cache list_push failed", key=key, error=e)
            return False
    
    async def list_pop(self, key: str, left: bool = True) -> Any:
        """Pop value from list (left or right)."""
        try:
            client = await self.get_client()
            
            if left:
                value = await client.lpop(key)
            else:
                value = await client.rpop(key)
            
            if value is None:
                return None
            
            return json.loads(value)
            
        except Exception as e:
            self.log_error("Cache list_pop failed", key=key, error=e)
            return None
    
    async def list_length(self, key: str) -> int:
        """Get length of list."""
        try:
            client = await self.get_client()
            return await client.llen(key)
            
        except Exception as e:
            self.log_error("Cache list_length failed", key=key, error=e)
            return 0
    
    # Set operations
    async def set_add(self, key: str, *values: Any) -> bool:
        """Add values to set."""
        try:
            client = await self.get_client()
            serialized_values = [json.dumps(v) for v in values]
            await client.sadd(key, *serialized_values)
            return True
            
        except Exception as e:
            self.log_error("Cache set_add failed", key=key, error=e)
            return False
    
    async def set_remove(self, key: str, *values: Any) -> bool:
        """Remove values from set."""
        try:
            client = await self.get_client()
            serialized_values = [json.dumps(v) for v in values]
            result = await client.srem(key, *serialized_values)
            return result > 0
            
        except Exception as e:
            self.log_error("Cache set_remove failed", key=key, error=e)
            return False
    
    async def set_is_member(self, key: str, value: Any) -> bool:
        """Check if value is member of set."""
        try:
            client = await self.get_client()
            serialized_value = json.dumps(value)
            result = await client.sismember(key, serialized_value)
            return result
            
        except Exception as e:
            self.log_error("Cache set_is_member failed", key=key, error=e)
            return False
    
    # Hash operations
    async def hash_get(self, key: str, field: str, default: Any = None) -> Any:
        """Get field from hash."""
        try:
            client = await self.get_client()
            value = await client.hget(key, field)
            
            if value is None:
                return default
            
            return json.loads(value)
            
        except Exception as e:
            self.log_error("Cache hash_get failed", key=key, field=field, error=e)
            return default
    
    async def hash_set(self, key: str, field: str, value: Any) -> bool:
        """Set field in hash."""
        try:
            client = await self.get_client()
            serialized_value = json.dumps(value)
            await client.hset(key, field, serialized_value)
            return True
            
        except Exception as e:
            self.log_error("Cache hash_set failed", key=key, field=field, error=e)
            return False
    
    async def hash_get_all(self, key: str) -> Dict[str, Any]:
        """Get all fields from hash."""
        try:
            client = await self.get_client()
            hash_data = await client.hgetall(key)
            
            result = {}
            for field, value in hash_data.items():
                try:
                    result[field.decode()] = json.loads(value)
                except (json.JSONDecodeError, AttributeError):
                    result[field.decode() if isinstance(field, bytes) else field] = value
            
            return result
            
        except Exception as e:
            self.log_error("Cache hash_get_all failed", key=key, error=e)
            return {}
    
    # Utility methods
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter."""
        try:
            client = await self.get_client()
            result = await client.incrby(key, amount)
            return result
            
        except Exception as e:
            self.log_error("Cache increment failed", key=key, error=e)
            return 0
    
    async def decrement(self, key: str, amount: int = 1) -> int:
        """Decrement counter."""
        try:
            client = await self.get_client()
            result = await client.decrby(key, amount)
            return result
            
        except Exception as e:
            self.log_error("Cache decrement failed", key=key, error=e)
            return 0
    
    async def keys_pattern(self, pattern: str) -> List[str]:
        """Get keys matching pattern."""
        try:
            client = await self.get_client()
            keys = await client.keys(pattern)
            return [key.decode() if isinstance(key, bytes) else key for key in keys]
            
        except Exception as e:
            self.log_error("Cache keys_pattern failed", pattern=pattern, error=e)
            return []
    
    async def flush_db(self) -> bool:
        """Flush current database (use with caution!)."""
        try:
            client = await self.get_client()
            await client.flushdb()
            self.log_warning("Cache database flushed")
            return True
            
        except Exception as e:
            self.log_error("Cache flush_db failed", error=e)
            return False


# Global cache service instance
cache_service = CacheService()