"""
Complete OpenAPI specification for the Hybrid RAG AI Platform
Provides comprehensive API documentation with all endpoints, models, and examples
"""

from fastapi import FastAPI, APIRouter
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.responses import HTMLResponse
from typing import Dict, Any, List, Optional
import json

from src.core.config import settings
from src.api.v1.auth import router as auth_router
from src.api.v1.documents import router as documents_router
from src.api.v1.collections import router as collections_router
from src.api.v1.search import router as search_router
from src.api.v1.rag import router as rag_router
from src.api.v1.chat import router as chat_router
from src.api.v1.users import router as users_router
from src.api.v1.tenants import router as tenants_router
from src.api.v1.analytics import router as analytics_router
from src.api.v1.feedback import router as feedback_router
from src.api.v1.admin import router as admin_router
from src.api.v1.integrations import router as integrations_router
from src.api.v1.ai import router as ai_router
from src.api.v1.workflows import router as workflows_router
from src.api.v1.notifications import router as notifications_router
from src.api.v1.compliance import router as compliance_router
from src.api.v1.insights import router as insights_router

def create_openapi_schema(app: FastAPI) -> Dict[str, Any]:
    """
    Create comprehensive OpenAPI schema with all endpoints, security, and examples
    """
    
    # Custom OpenAPI schema with enhanced metadata
    openapi_schema = get_openapi(
        title="Hybrid RAG AI Platform API",
        version="1.0.0",
        description="""
        # Hybrid RAG AI Platform API

        A comprehensive API for the Hybrid RAG (Retrieval-Augmented Generation) AI Platform that combines 
        vector search, traditional search, and advanced AI capabilities with enterprise features.

        ## Key Features

        - **Hybrid Search**: Combines vector similarity search with lexical search for optimal results
        - **RAG Engine**: Advanced retrieval-augmented generation with citations and confidence scoring
        - **Multi-tenancy**: Complete tenant isolation with role-based access control
        - **AI Integration**: Support for multiple LLM providers with intelligent routing
        - **Document Processing**: Advanced OCR, PII detection, and content extraction
        - **Personalization**: User-specific recommendations and adaptive learning
        - **Expert System**: Community-driven expertise and reputation management
        - **Compliance**: GDPR, CCPA, and HIPAA compliance features
        - **Real-time**: WebSocket support for live updates and streaming
        - **Analytics**: Comprehensive usage analytics and insights

        ## Authentication

        The API uses JWT-based authentication with support for:
        - OAuth 2.0 / OpenID Connect
        - API Keys for service-to-service communication
        - Role-based access control (RBAC)
        - Attribute-based access control (ABAC)

        ## Rate Limiting

        API endpoints are rate-limited based on user tier:
        - **Free Tier**: 100 requests/hour
        - **Pro Tier**: 1,000 requests/hour  
        - **Enterprise**: Custom limits

        ## Webhooks

        The platform supports webhooks for real-time event notifications:
        - Document processing completion
        - User activity events
        - System alerts and maintenance
        - Custom workflow triggers

        ## SDKs

        Official SDKs are available for:
        - Python
        - JavaScript/TypeScript
        - React/Next.js
        - Mobile (React Native)

        ## Support

        - **Documentation**: https://docs.myplatform.com
        - **Support**: support@myplatform.com
        - **Status Page**: https://status.myplatform.com
        - **Community**: https://community.myplatform.com
        """,
        routes=app.routes,
        servers=[
            {
                "url": "https://api.myplatform.com",
                "description": "Production API"
            },
            {
                "url": "https://staging-api.myplatform.com", 
                "description": "Staging API"
            },
            {
                "url": "http://localhost:8000",
                "description": "Development API"
            }
        ],
        contact={
            "name": "API Support",
            "url": "https://myplatform.com/support",
            "email": "api-support@myplatform.com"
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT"
        },
        terms_of_service="https://myplatform.com/terms"
    )

    # Enhanced security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token obtained from /auth/login"
        },
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API key for service-to-service communication"
        },
        "OAuth2": {
            "type": "oauth2",
            "description": "OAuth 2.0 with PKCE",
            "flows": {
                "authorizationCode": {
                    "authorizationUrl": "https://auth.myplatform.com/oauth/authorize",
                    "tokenUrl": "https://auth.myplatform.com/oauth/token",
                    "refreshUrl": "https://auth.myplatform.com/oauth/refresh",
                    "scopes": {
                        "read": "Read access to resources",
                        "write": "Write access to resources", 
                        "admin": "Administrative access",
                        "documents:read": "Read documents",
                        "documents:write": "Create and modify documents",
                        "search": "Perform searches",
                        "ai:query": "Use AI features",
                        "analytics:read": "View analytics",
                        "users:manage": "Manage users",
                        "tenants:manage": "Manage tenants"
                    }
                }
            }
        }
    }

    # Add global security requirement
    openapi_schema["security"] = [
        {"BearerAuth": []},
        {"ApiKeyAuth": []},
        {"OAuth2": ["read"]}
    ]

    # Enhanced error responses
    openapi_schema["components"]["responses"] = {
        "ValidationError": {
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "loc": {"type": "array", "items": {"type": "string"}},
                                        "msg": {"type": "string"},
                                        "type": {"type": "string"}
                                    }
                                }
                            },
                            "error_code": {"type": "string"},
                            "timestamp": {"type": "string", "format": "date-time"}
                        }
                    },
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "title"],
                                "msg": "field required",
                                "type": "value_error.missing"
                            }
                        ],
                        "error_code": "VALIDATION_ERROR",
                        "timestamp": "2024-01-15T10:30:00Z"
                    }
                }
            }
        },
        "Unauthorized": {
            "description": "Authentication required",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {"type": "string"},
                            "error_code": {"type": "string"},
                            "timestamp": {"type": "string", "format": "date-time"}
                        }
                    },
                    "example": {
                        "detail": "Invalid authentication credentials",
                        "error_code": "UNAUTHORIZED",
                        "timestamp": "2024-01-15T10:30:00Z"
                    }
                }
            }
        },
        "Forbidden": {
            "description": "Insufficient permissions",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {"type": "string"},
                            "error_code": {"type": "string"},
                            "required_permissions": {"type": "array", "items": {"type": "string"}},
                            "timestamp": {"type": "string", "format": "date-time"}
                        }
                    },
                    "example": {
                        "detail": "Insufficient permissions to access this resource",
                        "error_code": "FORBIDDEN",
                        "required_permissions": ["documents:write"],
                        "timestamp": "2024-01-15T10:30:00Z"
                    }
                }
            }
        },
        "NotFound": {
            "description": "Resource not found",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {"type": "string"},
                            "error_code": {"type": "string"},
                            "resource_type": {"type": "string"},
                            "resource_id": {"type": "string"},
                            "timestamp": {"type": "string", "format": "date-time"}
                        }
                    },
                    "example": {
                        "detail": "Document not found",
                        "error_code": "NOT_FOUND",
                        "resource_type": "document",
                        "resource_id": "doc_123",
                        "timestamp": "2024-01-15T10:30:00Z"
                    }
                }
            }
        },
        "RateLimitExceeded": {
            "description": "Rate limit exceeded",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {"type": "string"},
                            "error_code": {"type": "string"},
                            "retry_after": {"type": "integer"},
                            "limit": {"type": "integer"},
                            "remaining": {"type": "integer"},
                            "reset_time": {"type": "string", "format": "date-time"},
                            "timestamp": {"type": "string", "format": "date-time"}
                        }
                    },
                    "example": {
                        "detail": "Rate limit exceeded",
                        "error_code": "RATE_LIMIT_EXCEEDED", 
                        "retry_after": 3600,
                        "limit": 100,
                        "remaining": 0,
                        "reset_time": "2024-01-15T11:00:00Z",
                        "timestamp": "2024-01-15T10:30:00Z"
                    }
                }
            }
        },
        "InternalServerError": {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {"type": "string"},
                            "error_code": {"type": "string"},
                            "trace_id": {"type": "string"},
                            "timestamp": {"type": "string", "format": "date-time"}
                        }
                    },
                    "example": {
                        "detail": "An unexpected error occurred",
                        "error_code": "INTERNAL_SERVER_ERROR",
                        "trace_id": "trace_abc123",
                        "timestamp": "2024-01-15T10:30:00Z"
                    }
                }
            }
        }
    }

    # Common parameters
    openapi_schema["components"]["parameters"] = {
        "TenantId": {
            "name": "X-Tenant-ID",
            "in": "header",
            "required": True,
            "description": "Tenant identifier for multi-tenant isolation",
            "schema": {"type": "string", "format": "uuid"},
            "example": "550e8400-e29b-41d4-a716-446655440000"
        },
        "PaginationLimit": {
            "name": "limit",
            "in": "query",
            "required": False,
            "description": "Maximum number of items to return",
            "schema": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20},
            "example": 20
        },
        "PaginationOffset": {
            "name": "offset",
            "in": "query", 
            "required": False,
            "description": "Number of items to skip",
            "schema": {"type": "integer", "minimum": 0, "default": 0},
            "example": 0
        },
        "SearchQuery": {
            "name": "q",
            "in": "query",
            "required": True,
            "description": "Search query string",
            "schema": {"type": "string", "minLength": 1, "maxLength": 1000},
            "example": "artificial intelligence machine learning"
        },
        "DocumentId": {
            "name": "document_id",
            "in": "path",
            "required": True,
            "description": "Unique document identifier",
            "schema": {"type": "string", "format": "uuid"},
            "example": "doc_550e8400-e29b-41d4-a716-446655440000"
        }
    }

    # Add webhook information
    openapi_schema["webhooks"] = {
        "documentProcessed": {
            "post": {
                "requestBody": {
                    "description": "Document processing completion notification",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "event": {"type": "string", "enum": ["document.processed"]},
                                    "data": {
                                        "type": "object",
                                        "properties": {
                                            "document_id": {"type": "string"},
                                            "tenant_id": {"type": "string"},
                                            "status": {"type": "string", "enum": ["completed", "failed"]},
                                            "processing_time_ms": {"type": "integer"},
                                            "extracted_text_length": {"type": "integer"},
                                            "confidence_score": {"type": "number"},
                                            "error_message": {"type": "string"}
                                        }
                                    },
                                    "timestamp": {"type": "string", "format": "date-time"}
                                },
                                "required": ["event", "data", "timestamp"]
                            },
                            "example": {
                                "event": "document.processed",
                                "data": {
                                    "document_id": "doc_123",
                                    "tenant_id": "tenant_456", 
                                    "status": "completed",
                                    "processing_time_ms": 2500,
                                    "extracted_text_length": 15000,
                                    "confidence_score": 0.95
                                },
                                "timestamp": "2024-01-15T10:30:00Z"
                            }
                        }
                    }
                },
                "responses": {
                    "200": {"description": "Webhook received successfully"}
                }
            }
        },
        "userActivity": {
            "post": {
                "requestBody": {
                    "description": "User activity event notification",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "event": {"type": "string", "enum": ["user.login", "user.logout", "user.document_view", "user.search"]},
                                    "data": {
                                        "type": "object",
                                        "properties": {
                                            "user_id": {"type": "string"},
                                            "tenant_id": {"type": "string"},
                                            "activity_type": {"type": "string"},
                                            "resource_id": {"type": "string"},
                                            "metadata": {"type": "object"}
                                        }
                                    },
                                    "timestamp": {"type": "string", "format": "date-time"}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {"description": "Webhook received successfully"}
                }
            }
        }
    }

    # Add code examples
    openapi_schema["x-code-samples"] = {
        "python": """
# Python SDK Example
from myplatform_sdk import MyPlatformClient

client = MyPlatformClient(
    api_key="your_api_key",
    tenant_id="your_tenant_id"
)

# Upload and process document
document = client.documents.upload(
    file_path="./document.pdf",
    title="My Document"
)

# Perform RAG query
result = client.rag.query(
    question="What are the key findings?",
    document_ids=[document.id]
)

print(result.answer)
for citation in result.citations:
    print(f"Source: {citation.source} (confidence: {citation.confidence})")
        """,
        "javascript": """
// JavaScript SDK Example
import { MyPlatformClient } from '@myplatform/sdk';

const client = new MyPlatformClient({
  apiKey: 'your_api_key',
  tenantId: 'your_tenant_id'
});

// Upload and process document
const document = await client.documents.upload({
  file: fileInput.files[0],
  title: 'My Document'
});

// Perform RAG query
const result = await client.rag.query({
  question: 'What are the key findings?',
  documentIds: [document.id]
});

console.log(result.answer);
result.citations.forEach(citation => {
  console.log(`Source: ${citation.source} (confidence: ${citation.confidence})`);
});
        """,
        "curl": """
# cURL Examples

# Upload document
curl -X POST "https://api.myplatform.com/v1/documents/upload" \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
  -H "X-Tenant-ID: YOUR_TENANT_ID" \\
  -F "file=@document.pdf" \\
  -F "title=My Document"

# Perform RAG query
curl -X POST "https://api.myplatform.com/v1/rag/query" \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
  -H "X-Tenant-ID: YOUR_TENANT_ID" \\
  -H "Content-Type: application/json" \\
  -d '{
    "question": "What are the key findings?",
    "document_ids": ["doc_123"],
    "mode": "comprehensive"
  }'
        """
    }

    # Add API versioning information
    openapi_schema["x-api-version"] = {
        "current": "v1",
        "supported": ["v1"],
        "deprecated": [],
        "lifecycle": {
            "v1": {
                "status": "stable",
                "introduced": "2024-01-01",
                "sunset": None
            }
        }
    }

    # Add performance and reliability information
    openapi_schema["x-api-specs"] = {
        "performance": {
            "average_response_time": "< 100ms",
            "p95_response_time": "< 500ms", 
            "p99_response_time": "< 1000ms",
            "throughput": "10,000 requests/second",
            "availability": "99.9%"
        },
        "limits": {
            "max_request_size": "100MB",
            "max_response_size": "10MB",
            "rate_limits": {
                "free_tier": "100 requests/hour",
                "pro_tier": "1,000 requests/hour",
                "enterprise": "Custom"
            }
        }
    }

    return openapi_schema

def setup_docs_routes(app: FastAPI) -> None:
    """
    Setup custom documentation routes with enhanced UI
    """
    
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url="/openapi.json",
            title="Hybrid RAG AI Platform API Documentation",
            oauth2_redirect_url="/docs/oauth2-redirect",
            swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
            swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
            swagger_favicon_url="/favicon.ico",
            swagger_ui_parameters={
                "deepLinking": True,
                "displayRequestDuration": True,
                "docExpansion": "none",
                "operationsSorter": "alpha",
                "filter": True,
                "showExtensions": True,
                "showCommonExtensions": True,
                "tryItOutEnabled": True
            }
        )
    
    @app.get("/redoc", include_in_schema=False)
    async def redoc_html():
        return get_redoc_html(
            openapi_url="/openapi.json",
            title="Hybrid RAG AI Platform API Documentation",
            redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.1.3/bundles/redoc.standalone.js",
            redoc_favicon_url="/favicon.ico",
            with_google_fonts=True
        )
    
    @app.get("/docs/oauth2-redirect", include_in_schema=False)
    async def swagger_ui_redirect():
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>OAuth2 Redirect</title>
        </head>
        <body>
            <script>
                window.opener.swaggerUIRedirectOauth2({
                    auth: {
                        token: {
                            access_token: new URLSearchParams(window.location.search).get('access_token'),
                            token_type: 'Bearer'
                        }
                    }
                });
                window.close();
            </script>
        </body>
        </html>
        """)

    @app.get("/openapi.json", include_in_schema=False)
    async def get_openapi_endpoint():
        return app.openapi_schema

    @app.get("/api-spec.yaml", include_in_schema=False)
    async def get_openapi_yaml():
        import yaml
        from fastapi.responses import PlainTextResponse
        
        openapi_dict = app.openapi_schema
        yaml_str = yaml.dump(openapi_dict, default_flow_style=False, sort_keys=False)
        return PlainTextResponse(content=yaml_str, media_type="application/x-yaml")

def add_api_routes(app: FastAPI) -> None:
    """
    Add all API routes to the FastAPI application
    """
    
    # API v1 routes
    api_v1 = APIRouter(prefix="/api/v1")
    
    # Include all route modules
    api_v1.include_router(auth_router, prefix="/auth", tags=["Authentication"])
    api_v1.include_router(documents_router, prefix="/documents", tags=["Documents"])
    api_v1.include_router(collections_router, prefix="/collections", tags=["Collections"]) 
    api_v1.include_router(search_router, prefix="/search", tags=["Search"])
    api_v1.include_router(rag_router, prefix="/rag", tags=["RAG Engine"])
    api_v1.include_router(chat_router, prefix="/chat", tags=["AI Chat"])
    api_v1.include_router(users_router, prefix="/users", tags=["User Management"])
    api_v1.include_router(tenants_router, prefix="/tenants", tags=["Tenant Management"])
    api_v1.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])
    api_v1.include_router(feedback_router, prefix="/feedback", tags=["Feedback"])
    api_v1.include_router(admin_router, prefix="/admin", tags=["Administration"])
    api_v1.include_router(integrations_router, prefix="/integrations", tags=["Integrations"])
    api_v1.include_router(ai_router, prefix="/ai", tags=["AI Services"])
    api_v1.include_router(workflows_router, prefix="/workflows", tags=["Workflows"])
    api_v1.include_router(notifications_router, prefix="/notifications", tags=["Notifications"])
    api_v1.include_router(compliance_router, prefix="/compliance", tags=["Compliance"])
    api_v1.include_router(insights_router, prefix="/insights", tags=["Insights"])
    
    # Add v1 routes to app
    app.include_router(api_v1)
    
    # Health check endpoint
    @app.get("/health", tags=["Health"], include_in_schema=True)
    async def health_check():
        """
        Health check endpoint for monitoring and load balancers
        
        Returns:
            dict: Health status information including system metrics
        """
        import psutil
        import time
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT,
            "uptime": time.time() - app.extra.get("start_time", time.time()),
            "system": {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent
            },
            "services": {
                "database": "healthy",  # Would check actual DB connection
                "redis": "healthy",     # Would check actual Redis connection
                "vector_db": "healthy", # Would check actual Qdrant connection
                "llm_providers": "healthy"  # Would check LLM provider status
            }
        }

    # API information endpoint
    @app.get("/api/info", tags=["API Info"], include_in_schema=True)
    async def api_info():
        """
        Get API information and capabilities
        
        Returns:
            dict: API metadata, version information, and feature flags
        """
        return {
            "name": "Hybrid RAG AI Platform API",
            "version": "1.0.0",
            "description": "Enterprise-grade hybrid RAG platform with advanced AI capabilities",
            "features": {
                "hybrid_search": True,
                "rag_engine": True,
                "multi_tenancy": True,
                "real_time": True,
                "analytics": True,
                "compliance": True,
                "ai_routing": True,
                "personalization": True,
                "expert_system": True,
                "webhooks": True
            },
            "supported_languages": ["en", "he", "ar", "es", "fr", "de"],
            "supported_file_types": [
                "application/pdf",
                "application/msword", 
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/vnd.ms-powerpoint",
                "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                "application/vnd.ms-excel",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "text/plain",
                "text/html",
                "text/markdown",
                "image/jpeg",
                "image/png",
                "image/tiff"
            ],
            "limits": {
                "max_file_size": "100MB",
                "max_query_length": 1000,
                "max_documents_per_collection": 10000,
                "max_collections_per_tenant": 1000
            },
            "endpoints": {
                "total": len([route for route in app.routes if hasattr(route, 'methods')]),
                "documentation": "/docs",
                "redoc": "/redoc",
                "openapi_json": "/openapi.json",
                "openapi_yaml": "/api-spec.yaml"
            }
        }

def configure_openapi(app: FastAPI) -> None:
    """
    Configure OpenAPI schema and documentation for the FastAPI application
    """
    
    # Set the OpenAPI schema
    app.openapi_schema = create_openapi_schema(app)
    
    # Setup documentation routes
    setup_docs_routes(app)
    
    # Add API routes
    add_api_routes(app)
    
    # Store start time for uptime calculation
    import time
    app.extra = {"start_time": time.time()}