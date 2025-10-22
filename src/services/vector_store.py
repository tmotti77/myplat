"""Vector store service using Qdrant for high-performance vector search."""
import asyncio
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models as qdrant_models
    from qdrant_client.http.exceptions import ResponseHandlingException, UnexpectedResponse
except ImportError:
    QdrantClient = None
    qdrant_models = None
    ResponseHandlingException = Exception
    UnexpectedResponse = Exception
    print("Warning: qdrant_client not available, vector store functionality will be disabled")

from src.core.config import settings
from src.core.logging import get_logger, LoggerMixin

logger = get_logger(__name__)


class VectorStoreService(LoggerMixin):
    """Vector store service using Qdrant for semantic search."""
    
    def __init__(self):
        self._client: Optional[QdrantClient] = None
        self._collections = {}  # Cache collection info
    
    async def initialize(self):
        """Initialize Qdrant client and collections."""
        try:
            if QdrantClient is None:
                self.log_warning("QdrantClient not available, vector store will be disabled")
                return
                
            # Initialize Qdrant client
            self._client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY,
                timeout=settings.QDRANT_TIMEOUT,
                prefer_grpc=False,  # Use HTTP for better compatibility
            )
            
            # Test connection
            await asyncio.get_event_loop().run_in_executor(
                None, self._client.get_collections
            )
            
            self.log_info("Qdrant vector store initialized", url=settings.QDRANT_URL)
            
        except Exception as e:
            self.log_error("Failed to initialize Qdrant vector store", error=e)
            # Don't raise error, continue without vector store
            self._client = None
    
    async def cleanup(self):
        """Clean up vector store connections."""
        try:
            if self._client:
                # Qdrant client doesn't need explicit cleanup
                self._client = None
            
            self.log_info("Vector store cleaned up")
            
        except Exception as e:
            self.log_error("Error during vector store cleanup", error=e)
    
    async def health_check(self) -> bool:
        """Check vector store health."""
        try:
            if not self._client:
                return False
            
            # Try to get collections
            await asyncio.get_event_loop().run_in_executor(
                None, self._client.get_collections
            )
            return True
            
        except Exception as e:
            self.log_error("Vector store health check failed", error=e)
            return False
    
    def _get_collection_name(self, tenant_id: str, embedding_model: str) -> str:
        """Get collection name for tenant and embedding model."""
        
        # Replace special characters in model name
        safe_model = embedding_model.replace("/", "_").replace("-", "_")
        return f"tenant_{tenant_id}_{safe_model}"
    
    async def create_collection(
        self,
        tenant_id: str,
        embedding_model: str,
        vector_size: int,
        distance: str = "Cosine"
    ) -> bool:
        """Create a new collection for vectors."""
        
        collection_name = self._get_collection_name(tenant_id, embedding_model)
        
        try:
            # Check if collection already exists
            collections = await asyncio.get_event_loop().run_in_executor(
                None, self._client.get_collections
            )
            
            existing_names = [col.name for col in collections.collections]
            if collection_name in existing_names:
                self.log_info("Collection already exists", collection=collection_name)
                return True
            
            # Create collection
            await asyncio.get_event_loop().run_in_executor(
                None,
                self._client.create_collection,
                collection_name,
                qdrant_models.VectorParams(
                    size=vector_size,
                    distance=getattr(qdrant_models.Distance, distance.upper())
                )
            )
            
            # Cache collection info
            self._collections[collection_name] = {
                "tenant_id": tenant_id,
                "embedding_model": embedding_model,
                "vector_size": vector_size,
                "distance": distance
            }
            
            self.log_info(
                "Collection created successfully",
                collection=collection_name,
                vector_size=vector_size,
                distance=distance
            )
            
            return True
            
        except Exception as e:
            self.log_error(
                "Failed to create collection",
                collection=collection_name,
                error=e
            )
            return False
    
    async def delete_collection(self, tenant_id: str, embedding_model: str) -> bool:
        """Delete a collection."""
        
        collection_name = self._get_collection_name(tenant_id, embedding_model)
        
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                self._client.delete_collection,
                collection_name
            )
            
            # Remove from cache
            self._collections.pop(collection_name, None)
            
            self.log_info("Collection deleted", collection=collection_name)
            return True
            
        except Exception as e:
            self.log_error("Failed to delete collection", collection=collection_name, error=e)
            return False
    
    async def upsert_vectors(
        self,
        tenant_id: str,
        embedding_model: str,
        vectors: List[Dict[str, Any]]
    ) -> bool:
        """Upsert vectors into collection."""
        
        collection_name = self._get_collection_name(tenant_id, embedding_model)
        
        try:
            # Prepare points for Qdrant
            points = []
            for vector_data in vectors:
                point = qdrant_models.PointStruct(
                    id=vector_data["id"],
                    vector=vector_data["vector"],
                    payload=vector_data.get("payload", {})
                )
                points.append(point)
            
            # Upsert in batches
            batch_size = 100
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    self._client.upsert,
                    collection_name,
                    batch
                )
            
            self.log_info(
                "Vectors upserted successfully",
                collection=collection_name,
                count=len(vectors)
            )
            
            return True
            
        except Exception as e:
            self.log_error(
                "Failed to upsert vectors",
                collection=collection_name,
                count=len(vectors),
                error=e
            )
            return False
    
    async def search_vectors(
        self,
        tenant_id: str,
        embedding_model: str,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors."""
        
        collection_name = self._get_collection_name(tenant_id, embedding_model)
        
        try:
            # Prepare filter conditions
            filter_conditions = None
            if filters:
                filter_conditions = self._build_filter_conditions(filters)
            
            # Perform search
            search_result = await asyncio.get_event_loop().run_in_executor(
                None,
                self._client.search,
                collection_name,
                query_vector,
                filter_conditions,
                limit,
                score_threshold
            )
            
            # Format results
            results = []
            for scored_point in search_result:
                result = {
                    "id": scored_point.id,
                    "score": scored_point.score,
                    "payload": scored_point.payload
                }
                results.append(result)
            
            self.log_info(
                "Vector search completed",
                collection=collection_name,
                results_count=len(results),
                limit=limit
            )
            
            return results
            
        except Exception as e:
            self.log_error(
                "Vector search failed",
                collection=collection_name,
                error=e
            )
            return []
    
    async def search_batch(
        self,
        tenant_id: str,
        embedding_model: str,
        query_vectors: List[List[float]],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[List[Dict[str, Any]]]:
        """Batch search for multiple query vectors."""
        
        collection_name = self._get_collection_name(tenant_id, embedding_model)
        
        try:
            # Prepare search requests
            search_requests = []
            filter_conditions = None
            if filters:
                filter_conditions = self._build_filter_conditions(filters)
            
            for query_vector in query_vectors:
                request = qdrant_models.SearchRequest(
                    vector=query_vector,
                    filter=filter_conditions,
                    limit=limit,
                    score_threshold=score_threshold,
                    with_payload=True,
                    with_vector=False
                )
                search_requests.append(request)
            
            # Perform batch search
            batch_results = await asyncio.get_event_loop().run_in_executor(
                None,
                self._client.search_batch,
                collection_name,
                search_requests
            )
            
            # Format results
            all_results = []
            for search_result in batch_results:
                results = []
                for scored_point in search_result:
                    result = {
                        "id": scored_point.id,
                        "score": scored_point.score,
                        "payload": scored_point.payload
                    }
                    results.append(result)
                all_results.append(results)
            
            self.log_info(
                "Batch vector search completed",
                collection=collection_name,
                query_count=len(query_vectors),
                total_results=sum(len(results) for results in all_results)
            )
            
            return all_results
            
        except Exception as e:
            self.log_error(
                "Batch vector search failed",
                collection=collection_name,
                query_count=len(query_vectors),
                error=e
            )
            return [[] for _ in query_vectors]
    
    async def delete_vectors(
        self,
        tenant_id: str,
        embedding_model: str,
        vector_ids: Union[List[str], List[int]]
    ) -> bool:
        """Delete vectors by IDs."""
        
        collection_name = self._get_collection_name(tenant_id, embedding_model)
        
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                self._client.delete,
                collection_name,
                points_selector=qdrant_models.PointIdsList(
                    points=vector_ids
                )
            )
            
            self.log_info(
                "Vectors deleted successfully",
                collection=collection_name,
                count=len(vector_ids)
            )
            
            return True
            
        except Exception as e:
            self.log_error(
                "Failed to delete vectors",
                collection=collection_name,
                count=len(vector_ids),
                error=e
            )
            return False
    
    async def delete_vectors_by_filter(
        self,
        tenant_id: str,
        embedding_model: str,
        filters: Dict[str, Any]
    ) -> bool:
        """Delete vectors matching filter conditions."""
        
        collection_name = self._get_collection_name(tenant_id, embedding_model)
        
        try:
            filter_conditions = self._build_filter_conditions(filters)
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                self._client.delete,
                collection_name,
                points_selector=qdrant_models.FilterSelector(
                    filter=filter_conditions
                )
            )
            
            self.log_info(
                "Vectors deleted by filter",
                collection=collection_name,
                filters=filters
            )
            
            return True
            
        except Exception as e:
            self.log_error(
                "Failed to delete vectors by filter",
                collection=collection_name,
                filters=filters,
                error=e
            )
            return False
    
    def _build_filter_conditions(self, filters: Dict[str, Any]) -> Any:
        """Build Qdrant filter conditions from dictionary."""
        
        if qdrant_models is None:
            return None
            
        conditions = []
        
        for field, value in filters.items():
            if isinstance(value, dict):
                # Handle range conditions
                if "gte" in value:
                    condition = qdrant_models.FieldCondition(
                        key=field,
                        range=qdrant_models.Range(gte=value["gte"])
                    )
                    conditions.append(condition)
                elif "lte" in value:
                    condition = qdrant_models.FieldCondition(
                        key=field,
                        range=qdrant_models.Range(lte=value["lte"])
                    )
                    conditions.append(condition)
                elif "gt" in value:
                    condition = qdrant_models.FieldCondition(
                        key=field,
                        range=qdrant_models.Range(gt=value["gt"])
                    )
                    conditions.append(condition)
                elif "lt" in value:
                    condition = qdrant_models.FieldCondition(
                        key=field,
                        range=qdrant_models.Range(lt=value["lt"])
                    )
                    conditions.append(condition)
                elif "in" in value:
                    condition = qdrant_models.FieldCondition(
                        key=field,
                        match=qdrant_models.MatchAny(any=value["in"])
                    )
                    conditions.append(condition)
            elif isinstance(value, list):
                # Match any value in list
                condition = qdrant_models.FieldCondition(
                    key=field,
                    match=qdrant_models.MatchAny(any=value)
                )
                conditions.append(condition)
            else:
                # Exact match
                condition = qdrant_models.FieldCondition(
                    key=field,
                    match=qdrant_models.MatchValue(value=value)
                )
                conditions.append(condition)
        
        return qdrant_models.Filter(must=conditions)
    
    async def get_collection_info(
        self,
        tenant_id: str,
        embedding_model: str
    ) -> Optional[Dict[str, Any]]:
        """Get collection information."""
        
        collection_name = self._get_collection_name(tenant_id, embedding_model)
        
        try:
            info = await asyncio.get_event_loop().run_in_executor(
                None,
                self._client.get_collection,
                collection_name
            )
            
            return {
                "name": collection_name,
                "status": info.status,
                "vectors_count": info.vectors_count,
                "indexed_vectors_count": info.indexed_vectors_count,
                "points_count": info.points_count,
                "segments_count": info.segments_count,
                "config": {
                    "vector_size": info.config.params.vectors.size,
                    "distance": info.config.params.vectors.distance.name
                }
            }
            
        except Exception as e:
            self.log_error(
                "Failed to get collection info",
                collection=collection_name,
                error=e
            )
            return None
    
    async def get_vector(
        self,
        tenant_id: str,
        embedding_model: str,
        vector_id: Union[str, int],
        with_vector: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Get a specific vector by ID."""
        
        collection_name = self._get_collection_name(tenant_id, embedding_model)
        
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                self._client.retrieve,
                collection_name,
                [vector_id],
                with_vector
            )
            
            if result:
                point = result[0]
                return {
                    "id": point.id,
                    "payload": point.payload,
                    "vector": point.vector if with_vector else None
                }
            
            return None
            
        except Exception as e:
            self.log_error(
                "Failed to get vector",
                collection=collection_name,
                vector_id=vector_id,
                error=e
            )
            return None
    
    async def count_vectors(
        self,
        tenant_id: str,
        embedding_model: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """Count vectors in collection with optional filters."""
        
        collection_name = self._get_collection_name(tenant_id, embedding_model)
        
        try:
            filter_conditions = None
            if filters:
                filter_conditions = self._build_filter_conditions(filters)
            
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                self._client.count,
                collection_name,
                count_filter=filter_conditions,
                exact=True
            )
            
            return result.count
            
        except Exception as e:
            self.log_error(
                "Failed to count vectors",
                collection=collection_name,
                error=e
            )
            return 0
    
    async def create_index(
        self,
        tenant_id: str,
        embedding_model: str,
        field_name: str,
        field_type: str = "keyword"
    ) -> bool:
        """Create an index on a payload field."""
        
        collection_name = self._get_collection_name(tenant_id, embedding_model)
        
        try:
            # Map field types to Qdrant types
            type_mapping = {
                "keyword": qdrant_models.PayloadSchemaType.KEYWORD,
                "integer": qdrant_models.PayloadSchemaType.INTEGER,
                "float": qdrant_models.PayloadSchemaType.FLOAT,
                "bool": qdrant_models.PayloadSchemaType.BOOL,
                "geo": qdrant_models.PayloadSchemaType.GEO,
            }
            
            schema_type = type_mapping.get(field_type, qdrant_models.PayloadSchemaType.KEYWORD)
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                self._client.create_payload_index,
                collection_name,
                field_name,
                field_schema=schema_type
            )
            
            self.log_info(
                "Index created successfully",
                collection=collection_name,
                field=field_name,
                type=field_type
            )
            
            return True
            
        except Exception as e:
            self.log_error(
                "Failed to create index",
                collection=collection_name,
                field=field_name,
                error=e
            )
            return False


# Global vector store service instance
vector_store_service = VectorStoreService()