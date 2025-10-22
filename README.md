# 🚀 Hybrid RAG AI Platform

A production-ready Retrieval-Augmented Generation (RAG) platform that combines document processing, vector search, and advanced AI capabilities. Built with FastAPI, Next.js, and modern AI technologies.

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14.0%2B-black.svg)](https://nextjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%2B-blue.svg)](https://postgresql.org/)

## 🎯 What This Platform Does

Transform your documents into an intelligent AI assistant:

- **📄 Document Processing**: Upload PDFs, Word docs, text files
- **🔍 Intelligent Search**: Vector-based semantic search across all documents
- **💬 AI Chat**: Ask questions about your documents in natural language
- **🎯 Multi-Model Support**: OpenAI GPT-4, Anthropic Claude, Google Gemini
- **👥 Multi-User**: Secure authentication and user management
- **📊 Analytics**: Track usage, costs, and performance
- **🔒 Enterprise Security**: GDPR/CCPA compliance, encryption, audit logs

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   AI Services   │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   (OpenAI/etc)  │
│                 │    │                 │    │                 │
│ • Chat UI       │    │ • RAG Engine    │    │ • GPT-4         │
│ • File Upload   │    │ • Vector Search │    │ • Embeddings    │
│ • Dashboard     │    │ • Auth System   │    │ • Claude        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                       ┌─────────────────┐
                       │   Data Layer    │
                       │                 │
                       │ • PostgreSQL    │
                       │ • Vector Store  │
                       │ • Redis Cache   │
                       └─────────────────┘
```

## 🚀 Quick Start Guide

### Prerequisites

- **Docker Desktop** (with WSL2 support on Windows)
- **OpenAI API Key** ([Get one here](https://platform.openai.com/api-keys))
- **Git** for cloning the repository

### 1. Clone & Setup

```bash
git clone <your-repository-url>
cd hybrid-rag-platform

# Copy environment template
cp .env.example .env
```

### 2. Configure Your API Keys

Edit `.env` file with your settings:

```env
# Required: Your OpenAI API Key
OPENAI_API_KEY="sk-your-actual-key-here"

# Required: Database Password (choose any secure password)
DATABASE_URL="postgresql+asyncpg://rag_user:YOUR_SECURE_PASSWORD@localhost:5432/rag_platform"

# Required: Security Keys (use the provided examples or generate new ones)
SECRET_KEY="rag_app_master_secret_x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6"
JWT_SECRET_KEY="rag_platform_jwt_secret_a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3"
JWT_REFRESH_SECRET_KEY="rag_refresh_token_p3o2n1m0l9k8j7i6h5g4f3e2d1c0b9a8"
```

### 3. Choose Your Setup

**Option A: Simple Setup (Recommended for testing)**
```bash
# Start with just PostgreSQL + Backend
docker-compose -f docker-compose.simple.yml up -d

# Check if it's working
curl http://localhost:8000/health
```

**Option B: Full Setup (All features)**
```bash
# Start all services (PostgreSQL, Redis, Qdrant, Elasticsearch, etc.)
docker-compose up -d

# Check if it's working
curl http://localhost:8000/health
```

**Option C: Minimal Setup (PostgreSQL only)**
```bash
# Start with absolute minimum
docker-compose -f docker-compose.minimal.yml up -d

# Check if it's working
curl http://localhost:8000/health
```

### 4. Start the Frontend

```bash
cd frontend
npm install --legacy-peer-deps
npm run dev
```

### 5. Access the Platform

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Default Login**: 
  - Email: `admin@example.com`
  - Password: `admin123!`

## 📖 Docker Configurations Explained

### 🟢 docker-compose.simple.yml (Recommended)
**Best for: Testing, development, getting started**
- PostgreSQL with pgvector
- FastAPI backend
- Minimal resource usage
- Quick startup time

### 🔵 docker-compose.yml (Full Featured)
**Best for: Production, advanced features, scaling**
- PostgreSQL + pgvector
- Redis (caching)
- Qdrant (vector database)
- Elasticsearch (advanced search)
- MinIO (object storage)
- Prometheus + Grafana (monitoring)
- Jaeger (tracing)
- Celery (background tasks)

### 🟡 docker-compose.minimal.yml (Bare Minimum)
**Best for: Resource-constrained environments**
- PostgreSQL only
- No external dependencies
- Fastest startup

## 📊 Key Features by Setup

| Feature | Minimal | Simple | Full |
|---------|---------|--------|------|
| Document Upload | ✅ | ✅ | ✅ |
| AI Chat | ✅ | ✅ | ✅ |
| Vector Search | ✅ | ✅ | ✅ |
| User Auth | ✅ | ✅ | ✅ |
| Caching | ❌ | ❌ | ✅ |
| Advanced Search | ❌ | ❌ | ✅ |
| Object Storage | ❌ | ❌ | ✅ |
| Monitoring | ❌ | ❌ | ✅ |
| Background Tasks | ❌ | ❌ | ✅ |

## 💻 Project Structure

```
hybrid-rag-platform/
├── src/                          # Backend Python code
│   ├── api/                      # FastAPI route handlers
│   │   ├── auth.py              # Authentication endpoints
│   │   ├── chat.py              # Chat/conversation endpoints
│   │   ├── documents.py         # Document management
│   │   └── search.py            # Search endpoints
│   ├── core/                     # Core configuration
│   │   ├── config.py            # Settings and configuration
│   │   ├── database.py          # Database setup
│   │   ├── security.py          # Security utilities
│   │   └── logging.py           # Logging configuration
│   ├── models/                   # SQLAlchemy database models
│   │   ├── user.py              # User model
│   │   ├── document.py          # Document model
│   │   ├── conversation.py      # Chat conversation model
│   │   └── chunk.py             # Document chunk model
│   ├── services/                 # Business logic services
│   │   ├── rag_engine.py        # Main RAG orchestration
│   │   ├── vector_store.py      # Vector database operations
│   │   ├── document_processor.py # File processing
│   │   ├── llm_router.py        # Multi-model AI routing
│   │   ├── search_service.py    # Semantic search
│   │   └── auth_service.py      # Authentication logic
│   ├── middleware/               # Custom middleware
│   │   ├── auth.py              # Authentication middleware
│   │   ├── rate_limit.py        # Rate limiting
│   │   └── error_handling.py    # Error handling
│   └── main.py                   # Application entry point
├── frontend/                     # Next.js frontend
│   ├── pages/                    # Next.js pages
│   │   ├── index.tsx            # Landing page
│   │   ├── chat.tsx             # Chat interface
│   │   ├── dashboard.tsx        # User dashboard
│   │   ├── login.tsx            # Login page
│   │   └── documents/           # Document management pages
│   ├── src/components/           # React components
│   │   ├── chat/                # Chat interface components
│   │   ├── documents/           # Document management UI
│   │   ├── dashboard/           # Dashboard components
│   │   ├── layouts/             # Page layouts
│   │   └── ui/                  # Reusable UI components
│   ├── src/hooks/                # Custom React hooks
│   │   ├── use-auth.ts          # Authentication hook
│   │   └── use-debounce.ts      # Debouncing utility
│   └── src/lib/                  # Utility libraries
│       ├── api.ts               # API client
│       └── utils.ts             # Helper functions
├── tests/                        # Test suites
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   └── e2e/                     # End-to-end tests
├── alembic/                      # Database migrations
├── monitoring/                   # Grafana dashboards, Prometheus config
├── docker-compose*.yml          # Docker configurations
├── .env.example                  # Environment template
├── pyproject.toml               # Python dependencies
└── README.md                    # This file
```

## 🔧 Environment Configuration

### 🔑 Required Settings
```env
# AI API Keys
OPENAI_API_KEY="sk-your-key-here"
ANTHROPIC_API_KEY="your-anthropic-key"    # Optional
GOOGLE_API_KEY="your-google-key"          # Optional

# Database
DATABASE_URL="postgresql+asyncpg://rag_user:password@localhost:5432/rag_platform"

# Security (generate strong random keys)
SECRET_KEY="your-secret-key"
JWT_SECRET_KEY="your-jwt-secret"
JWT_REFRESH_SECRET_KEY="your-jwt-refresh-secret"
ENCRYPTION_KEY="your-32-character-encryption-key"
```

### 🎛️ Optional Features
```env
# Model Configuration
DEFAULT_LLM_MODEL="gpt-4-turbo-preview"
EMBEDDING_MODEL="text-embedding-3-large"
MAX_TOKENS=4000
TEMPERATURE=0.1

# Document Processing
MAX_FILE_SIZE_MB=100
CHUNK_SIZE=600
CHUNK_OVERLAP=100
SUPPORTED_LANGUAGES="en,he,ar,es,fr,de"

# Features
ENABLE_REAL_TIME_UPDATES=true
ENABLE_ADVANCED_ANALYTICS=true
GDPR_COMPLIANCE_ENABLED=true
AUDIT_ENABLED=true

# Cost Management
MAX_COST_PER_QUERY_USD=0.10
DAILY_COST_LIMIT_USD=100.00
MONTHLY_COST_LIMIT_USD=3000.00
```

## 🔒 Security Features

### Authentication & Authorization
- JWT-based authentication
- Role-based access control (RBAC)
- Multi-factor authentication (optional)
- Session management

### Data Protection
- End-to-end encryption
- PII detection and anonymization
- GDPR/CCPA compliance
- Audit logging
- Data retention policies

### API Security
- Rate limiting
- Request validation
- CORS protection
- TLS/SSL support

## 📚 API Documentation

### Authentication Endpoints
```
POST /api/v1/auth/login        # User login
POST /api/v1/auth/register     # User registration
POST /api/v1/auth/refresh      # Refresh JWT token
POST /api/v1/auth/logout       # User logout
```

### Document Management
```
POST /api/v1/documents/upload  # Upload new document
GET /api/v1/documents/         # List user documents
GET /api/v1/documents/{id}     # Get document details
DELETE /api/v1/documents/{id}  # Delete document
```

### Chat & Search
```
POST /api/v1/chat/             # Send chat message
GET /api/v1/chat/history       # Get chat history
POST /api/v1/search/           # Semantic search
GET /api/v1/search/suggestions # Search suggestions
```

### Admin Operations
```
GET /api/v1/admin/users        # List all users
GET /api/v1/admin/statistics   # Platform statistics
GET /api/v1/admin/health       # System health check
```

**Full interactive API documentation**: http://localhost:8000/docs

## 🧪 Development & Testing

### Running Tests
```bash
# Backend tests
docker exec rag_backend pytest

# Frontend tests
cd frontend && npm test

# End-to-end tests
cd frontend && npm run e2e

# Test coverage
docker exec rag_backend pytest --cov=src
```

### Development Commands
```bash
# Backend development (without Docker)
cd src && python main.py

# Frontend development
cd frontend && npm run dev

# Type checking
cd frontend && npm run type-check

# Linting and formatting
cd frontend && npm run lint
cd frontend && npm run lint:fix
```

## 🚀 Production Deployment

### Environment Preparation
```env
# Production settings
ENVIRONMENT="production"
APP_DEBUG=false
SSL_ENABLED=true
DATABASE_POOL_SIZE=50
REDIS_POOL_MAX_CONNECTIONS=100

# Domain configuration
DOMAIN_NAME="yourdomain.com"
ALLOWED_HOSTS="yourdomain.com,api.yourdomain.com"
CORS_ORIGINS="https://yourdomain.com"
```

### Cloud Storage Setup
```env
# AWS S3
AWS_REGION="us-west-2"
AWS_ACCESS_KEY_ID="your-key"
AWS_SECRET_ACCESS_KEY="your-secret"
AWS_S3_BUCKET="your-bucket"

# Or Azure Blob Storage
AZURE_STORAGE_CONNECTION_STRING="your-connection-string"
AZURE_STORAGE_CONTAINER="your-container"

# Or Google Cloud Storage
GOOGLE_CLOUD_PROJECT="your-project"
GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
GCP_STORAGE_BUCKET="your-bucket"
```

## 📊 Monitoring & Observability

### Built-in Health Checks
- **Health endpoint**: http://localhost:8000/health
- **API docs**: http://localhost:8000/docs
- **Metrics**: http://localhost:8000/metrics (if Prometheus enabled)

### Full Monitoring Stack (with docker-compose.yml)
- **Prometheus**: http://localhost:9090 (metrics collection)
- **Grafana**: http://localhost:3000 (dashboards) - admin/admin123
- **Jaeger**: http://localhost:16686 (distributed tracing)

### Key Metrics Tracked
- Request/response times
- Token usage and costs
- Document processing statistics
- User activity patterns
- System resource utilization
- Error rates and types

## 🛠️ Troubleshooting

### Common Issues & Solutions

#### ❌ "Docker command not found"
```bash
# Restart terminal after Docker installation
# Verify Docker is running
docker --version
docker ps
```

#### ❌ "OpenAI API Error"
```bash
# Check API key format (should start with 'sk-')
# Verify account has credits: https://platform.openai.com/usage
# Check rate limits and quotas
```

#### ❌ "Database Connection Error"
```bash
# Check containers are running
docker ps

# Check PostgreSQL logs
docker-compose logs postgres

# Verify connection string in .env file
```

#### ❌ "Frontend Won't Start"
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
npm run dev
```

#### ❌ "Port Already in Use"
```bash
# Check what's using the port
lsof -i :8000
lsof -i :3000

# Kill processes or change ports in docker-compose
```

### Useful Debug Commands

```bash
# View all containers and their status
docker ps -a

# Check logs for specific services
docker-compose logs backend
docker-compose logs postgres
docker-compose logs frontend

# Restart specific service
docker-compose restart backend

# Enter container for debugging
docker exec -it rag_backend bash
docker exec -it rag_postgres psql -U rag_user -d rag_platform

# Monitor resource usage
docker stats

# Clean up everything
docker-compose down -v
docker system prune -a
```

## 💰 Cost Management

### Monitoring AI Costs
The platform includes built-in cost tracking:
- Per-query cost limits
- Daily/monthly spending caps
- Token usage analytics
- Model cost comparison

### Optimization Strategies
- Use cheaper models for simple queries
- Implement response caching
- Optimize chunk sizes and retrieval
- Set appropriate rate limits

### Example Cost Settings
```env
# Conservative limits for testing
MAX_COST_PER_QUERY_USD=0.05
DAILY_COST_LIMIT_USD=10.00
MONTHLY_COST_LIMIT_USD=100.00

# Production limits
MAX_COST_PER_QUERY_USD=0.25
DAILY_COST_LIMIT_USD=500.00
MONTHLY_COST_LIMIT_USD=10000.00
```

## 🌍 Multi-Language Support

### Supported Languages
- **English** (en) - Primary
- **Hebrew** (he) - RTL support
- **Arabic** (ar) - RTL support  
- **Spanish** (es)
- **French** (fr)
- **German** (de)

### Configuration
```env
SUPPORTED_LANGUAGES="en,he,ar,es,fr,de"
```

Frontend includes RTL support and language detection.

## 🎯 Roadmap

### ✅ Current Version (v1.0)
- Basic RAG functionality
- Document upload and processing
- AI chat interface
- User authentication
- Multi-language support
- Cost management
- Security features

### 🔄 Next Version (v1.1)
- [ ] Advanced analytics dashboard
- [ ] Multiple document collections
- [ ] Team collaboration features
- [ ] Enhanced search filters
- [ ] Mobile-responsive improvements
- [ ] Batch document processing

### 🚀 Future Plans (v2.0)
- [ ] Mobile applications
- [ ] Enterprise SSO integration
- [ ] Custom model fine-tuning
- [ ] Advanced AI agents
- [ ] Workflow automation
- [ ] API marketplace

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Add tests for new functionality
5. Commit using conventional commits: `git commit -m "feat: add amazing feature"`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

### Code Standards
- **Python**: Follow PEP 8, use Black formatter
- **TypeScript/JavaScript**: Use ESLint + Prettier
- **Commits**: Use conventional commit format
- **Testing**: Add tests for new features

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support & Community

- **📖 Documentation**: This README + API docs at `/docs`
- **🐛 Bug Reports**: Open a GitHub issue
- **💡 Feature Requests**: Use GitHub Discussions
- **❓ Questions**: Check existing issues or start a discussion

## 📞 Quick Reference

### Essential Commands
```bash
# Start simple setup
docker-compose -f docker-compose.simple.yml up -d

# Start frontend
cd frontend && npm run dev

# Check health
curl http://localhost:8000/health

# View logs
docker-compose logs backend

# Stop everything
docker-compose down
```

### Key URLs
- Frontend: http://localhost:3000
- Backend: http://localhost:8000  
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### Default Credentials
- Email: `admin@example.com`
- Password: `admin123!`

---

**🎉 Ready to build something amazing?**

*Transform your documents into intelligent conversations with the power of AI!*

**Built with ❤️ using FastAPI, Next.js, and cutting-edge AI technologies**