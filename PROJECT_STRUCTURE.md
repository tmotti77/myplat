# 📁 Project Structure & Architecture

This document explains the complete structure of the Hybrid RAG Platform and how all components work together.

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Hybrid RAG Platform                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │  Frontend   │    │   Backend   │    │ AI Services │         │
│  │  (Next.js)  │◄──►│  (FastAPI)  │◄──►│ (OpenAI etc)│         │
│  │             │    │             │    │             │         │
│  │ • Chat UI   │    │ • RAG Core  │    │ • GPT-4     │         │
│  │ • File Mgmt │    │ • Vector DB │    │ • Embeddings│         │
│  │ • Dashboard │    │ • Auth      │    │ • Claude    │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│                             │                                  │
│                   ┌─────────────────┐                          │
│                   │   Data Layer    │                          │
│                   │                 │                          │
│                   │ • PostgreSQL    │                          │
│                   │ • Vector Store  │                          │
│                   │ • Redis Cache   │                          │
│                   │ • File Storage  │                          │
│                   └─────────────────┘                          │
└─────────────────────────────────────────────────────────────────┘
```

## 📂 Directory Structure

```
hybrid-rag-platform/
│
├── 🐍 BACKEND (Python/FastAPI)
│   ├── src/                               # Main backend source code
│   │   ├── api/                          # API route handlers
│   │   │   ├── __init__.py              # API router setup
│   │   │   ├── auth.py                  # Authentication endpoints
│   │   │   ├── chat.py                  # Chat/conversation API
│   │   │   ├── documents.py             # Document management API
│   │   │   ├── search.py                # Search endpoints
│   │   │   ├── admin.py                 # Admin operations
│   │   │   ├── health.py                # Health check endpoints
│   │   │   └── openapi.py               # OpenAPI documentation
│   │   │
│   │   ├── core/                         # Core system components
│   │   │   ├── __init__.py
│   │   │   ├── config.py                # Configuration management
│   │   │   ├── database.py              # Database setup & connections
│   │   │   ├── security.py              # Security utilities
│   │   │   ├── logging.py               # Logging configuration
│   │   │   ├── observability.py         # Monitoring setup
│   │   │   └── data_protection.py       # GDPR/privacy features
│   │   │
│   │   ├── models/                       # Database models (SQLAlchemy)
│   │   │   ├── __init__.py
│   │   │   ├── base.py                  # Base model class
│   │   │   ├── user.py                  # User accounts
│   │   │   ├── tenant.py                # Multi-tenant support
│   │   │   ├── document.py              # Document metadata
│   │   │   ├── chunk.py                 # Document chunks
│   │   │   ├── conversation.py          # Chat conversations
│   │   │   ├── message.py               # Chat messages
│   │   │   ├── embedding.py             # Vector embeddings
│   │   │   ├── retrieval.py             # Search results
│   │   │   ├── feedback.py              # User feedback
│   │   │   ├── audit_log.py             # Audit trails
│   │   │   ├── source.py                # Document sources
│   │   │   ├── citation.py              # Answer citations
│   │   │   ├── experiment.py            # A/B testing
│   │   │   ├── expert.py                # Expert system
│   │   │   ├── profile.py               # User profiles
│   │   │   ├── preference.py            # User preferences
│   │   │   ├── interaction.py           # User interactions
│   │   │   ├── reputation.py            # Reputation system
│   │   │   ├── badge.py                 # Achievement badges
│   │   │   ├── contribution.py          # User contributions
│   │   │   ├── peer_review.py           # Peer review system
│   │   │   ├── model_training.py        # ML model training
│   │   │   ├── preference_pair.py       # Learning preferences
│   │   │   ├── feedback_comparison.py   # Feedback analysis
│   │   │   ├── rag_event.py             # System events
│   │   │   ├── user_consent.py          # Privacy consents
│   │   │   ├── data_subject_request.py  # GDPR requests
│   │   │   ├── user_embedding.py        # User embeddings
│   │   │   └── answer.py                # Generated answers
│   │   │
│   │   ├── services/                     # Business logic services
│   │   │   ├── __init__.py
│   │   │   ├── rag_engine.py            # 🎯 Main RAG orchestration
│   │   │   ├── rag_service.py           # RAG workflow management
│   │   │   ├── vector_store.py          # Vector database operations
│   │   │   ├── document_processor.py    # File processing pipeline
│   │   │   ├── embedding_service.py     # Text embedding generation
│   │   │   ├── llm_router.py            # Multi-model AI routing
│   │   │   ├── search_service.py        # Semantic search engine
│   │   │   ├── chat_service.py          # Conversation management
│   │   │   ├── auth_service.py          # Authentication logic
│   │   │   ├── storage_service.py       # File storage management
│   │   │   ├── cache.py                 # Caching layer (Redis)
│   │   │   ├── storage.py               # Object storage (MinIO/S3)
│   │   │   ├── ingestion.py             # Data ingestion pipeline
│   │   │   ├── search.py                # Advanced search
│   │   │   ├── embedding.py             # Embedding utilities
│   │   │   ├── personalization.py       # User personalization
│   │   │   ├── expert_system.py         # Expert knowledge system
│   │   │   └── feedback_system.py       # Learning from feedback
│   │   │
│   │   ├── middleware/                   # Custom middleware
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                  # Authentication middleware
│   │   │   ├── rate_limit.py            # Rate limiting
│   │   │   ├── error_handling.py        # Global error handling
│   │   │   ├── request_id.py            # Request tracking
│   │   │   ├── tenant.py                # Multi-tenant routing
│   │   │   └── dependencies.py          # Dependency injection
│   │   │
│   │   ├── schemas/                      # Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                  # Authentication schemas
│   │   │   ├── document.py              # Document schemas
│   │   │   ├── chat.py                  # Chat schemas
│   │   │   ├── search.py                # Search schemas
│   │   │   └── admin.py                 # Admin schemas
│   │   │
│   │   ├── security/                     # Security components
│   │   │   ├── __init__.py
│   │   │   ├── encryption.py            # Data encryption
│   │   │   ├── access_control.py        # Access management
│   │   │   └── audit.py                 # Security auditing
│   │   │
│   │   ├── monitoring/                   # Observability
│   │   │   ├── __init__.py
│   │   │   ├── health.py                # Health checks
│   │   │   ├── metrics.py               # Custom metrics
│   │   │   └── tracing.py               # Distributed tracing
│   │   │
│   │   ├── utils/                        # Utility functions
│   │   │   ├── __init__.py
│   │   │   ├── text_processing.py       # Text utilities
│   │   │   ├── file_utils.py            # File operations
│   │   │   ├── validators.py            # Input validation
│   │   │   └── helpers.py               # Helper functions
│   │   │
│   │   └── main.py                       # 🚀 Application entry point
│   │
│   ├── alembic/                         # Database migrations
│   │   ├── env.py                       # Migration environment
│   │   ├── script.py.mako              # Migration template
│   │   └── versions/                    # Migration files
│   │       └── 001_initial_migration.py
│   │
│   ├── tests/                           # Test suite
│   │   ├── conftest.py                 # Test configuration
│   │   ├── unit/                       # Unit tests
│   │   │   ├── test_auth_service.py
│   │   │   ├── test_rag_engine.py
│   │   │   └── test_search_service.py
│   │   ├── integration/                # Integration tests
│   │   │   └── test_document_workflow.py
│   │   ├── e2e/                        # End-to-end tests
│   │   │   └── test_complete_user_journey.py
│   │   ├── run_tests.py               # Test runner
│   │   └── test_requirements.txt      # Test dependencies
│   │
│   ├── scripts/                         # Utility scripts
│   │   └── seed_data.py               # Database seeding
│   │
│   ├── config/                          # Configuration files
│   │   └── (environment-specific configs)
│   │
│   ├── pyproject.toml                  # Python project config
│   ├── pytest.ini                     # Test configuration
│   ├── alembic.ini                    # Database migration config
│   └── test_dependencies.py          # Dependency testing
│
├── 🎨 FRONTEND (Next.js/React/TypeScript)
│   ├── pages/                           # Next.js pages (App Router)
│   │   ├── _app.tsx                    # App configuration
│   │   ├── _document.tsx              # Document structure
│   │   ├── index.tsx                  # 🏠 Landing page
│   │   ├── login.tsx                  # 🔐 Login page
│   │   ├── dashboard.tsx              # 📊 User dashboard
│   │   ├── chat.tsx                   # 💬 Chat interface
│   │   └── documents/                 # Document management
│   │       ├── index.tsx              # Document list
│   │       └── upload.tsx             # Document upload
│   │
│   ├── src/                            # Source code
│   │   ├── components/                 # React components
│   │   │   ├── layouts/               # Page layouts
│   │   │   │   ├── main-layout.tsx    # Main app layout
│   │   │   │   ├── header.tsx         # Navigation header
│   │   │   │   ├── sidebar.tsx        # Sidebar navigation
│   │   │   │   ├── footer.tsx         # Page footer
│   │   │   │   └── mobile-navigation.tsx # Mobile menu
│   │   │   │
│   │   │   ├── dashboard/             # Dashboard components
│   │   │   │   ├── welcome-banner.tsx # Welcome message
│   │   │   │   ├── statistics-cards.tsx # Metrics cards
│   │   │   │   ├── activity-feed.tsx  # Recent activity
│   │   │   │   └── quick-actions.tsx  # Action buttons
│   │   │   │
│   │   │   ├── documents/             # Document management
│   │   │   │   └── recent-documents.tsx # Recent docs
│   │   │   │
│   │   │   ├── search/                # Search interface
│   │   │   │   └── search-interface.tsx
│   │   │   │
│   │   │   ├── notifications/         # Notification system
│   │   │   │   └── notification-center.tsx
│   │   │   │
│   │   │   ├── accessibility/         # Accessibility features
│   │   │   │   ├── accessibility-menu.tsx
│   │   │   │   └── accessibility-menu-simple.tsx
│   │   │   │
│   │   │   ├── providers/             # Context providers
│   │   │   │   ├── theme-provider.tsx # Theme management
│   │   │   │   ├── loading-provider.tsx # Loading states
│   │   │   │   ├── rtl-provider.tsx   # RTL language support
│   │   │   │   └── accessibility-provider.tsx
│   │   │   │
│   │   │   ├── ui/                    # Reusable UI components
│   │   │   │   └── progress-bar.tsx   # Progress indicators
│   │   │   │
│   │   │   ├── command-palette.tsx    # Quick actions
│   │   │   └── error-boundary.tsx     # Error handling
│   │   │
│   │   ├── hooks/                      # Custom React hooks
│   │   │   ├── use-auth.ts            # Authentication hook
│   │   │   ├── use-debounce.ts        # Debouncing utility
│   │   │   ├── use-direction.ts       # RTL direction hook
│   │   │   └── use-keyboard-shortcuts.ts # Keyboard shortcuts
│   │   │
│   │   ├── lib/                        # Utility libraries
│   │   │   ├── api.ts                 # API client
│   │   │   └── utils.ts               # Helper functions
│   │   │
│   │   └── styles/                     # Global styles
│   │       └── globals.css            # Global CSS
│   │
│   ├── public/                         # Static assets
│   │   └── locales/                   # Internationalization
│   │       └── en/
│   │           └── common.json        # English translations
│   │
│   ├── package.json                   # Dependencies & scripts
│   ├── package-lock.json             # Dependency lock file
│   ├── next.config.js                # Next.js configuration
│   ├── next-i18next.config.js        # i18n configuration
│   ├── tailwind.config.js            # Tailwind CSS config
│   ├── tsconfig.json                 # TypeScript configuration
│   ├── tsconfig.tsbuildinfo          # TypeScript build cache
│   └── next-env.d.ts                 # Next.js TypeScript declarations
│
├── 🐳 INFRASTRUCTURE & DEPLOYMENT
│   ├── docker-compose.yml             # 🟢 Default setup (Simple)
│   ├── docker-compose.simple.yml     # 🟢 Simple setup (PostgreSQL + Backend)
│   ├── docker-compose.full.yml       # 🔵 Full setup (All services)
│   ├── docker-compose.minimal.yml    # 🟡 Minimal setup (PostgreSQL only)
│   ├── Dockerfile                    # Backend container definition
│   │
│   ├── monitoring/                    # Observability configuration
│   │   ├── prometheus.yml            # Prometheus config
│   │   ├── prometheus/               # Prometheus data
│   │   └── grafana/                  # Grafana configuration
│   │       ├── dashboards/           # Custom dashboards
│   │       └── datasources/          # Data source configs
│   │           └── prometheus.yml
│   │
│   └── database/                     # Database initialization
│       └── init.sql                  # Initial DB setup
│
├── 📊 DATA & STORAGE
│   ├── uploads/                      # Uploaded documents
│   ├── logs/                         # Application logs
│   └── migrations/                   # Additional migrations
│       ├── env.py
│       ├── script.py.mako
│       └── versions/
│
├── 📝 DOCUMENTATION & CONFIGURATION
│   ├── README.md                     # 📖 Main documentation
│   ├── PROJECT_STRUCTURE.md         # 📁 This file
│   ├── SETUP_GUIDE.md              # 🔧 Detailed setup guide
│   ├── .env.example                 # Environment template
│   ├── .env                         # Your environment config
│   ├── LICENSE                      # MIT License
│   │
│   ├── start.sh                     # 🚀 Quick start script
│   ├── start.ps1                    # Windows PowerShell script
│   ├── start-simple.ps1            # Simple Windows setup
│   └── update-env.ps1               # Environment update script
│
└── 🧪 TESTING & DEVELOPMENT
    ├── test_imports.py              # Import testing
    └── test_dependencies.py         # Dependency verification
```

## 🔄 Data Flow Architecture

### 1. 📄 Document Processing Pipeline

```
User Upload → File Validation → Text Extraction → Chunking → Embedding Generation → Vector Storage
     ↓              ↓                ↓            ↓              ↓                  ↓
   Web UI    →  FastAPI API  →  Unstructured  → Custom     →   OpenAI API    →  PostgreSQL
                                                 Logic                           (pgvector)
```

### 2. 💬 Chat/Query Pipeline

```
User Question → Intent Analysis → Vector Search → Context Retrieval → LLM Generation → Response
      ↓              ↓               ↓              ↓                ↓              ↓
    Web UI    →   FastAPI API  →  pgvector    →  Ranking       →  OpenAI API  →  User
                                   Search       Algorithm         (GPT-4)
```

### 3. 🔍 Search Pipeline

```
Search Query → Query Enhancement → Hybrid Search → Result Ranking → Response Formatting
     ↓               ↓                 ↓              ↓                    ↓
   Web UI     →  Search Service → Vector + Text  → ML Ranking    →    JSON API
                                   Search            Algorithm
```

## 🧩 Component Interactions

### Core Services Communication

```
┌─────────────────────────────────────────────────────────────────┐
│                     Service Layer                               │
├─────────────────┬─────────────────┬─────────────────┬──────────┤
│   RAG Engine   │  Vector Store   │  LLM Router     │  Cache   │
│                 │                 │                 │          │
│ • Orchestrates │ • Stores        │ • Routes to     │ • Redis  │
│   workflows    │   embeddings    │   AI models     │   cache  │
│ • Coordinates  │ • Similarity    │ • Load balance  │ • Session│
│   services     │   search        │ • Fallbacks    │   storage│
│ • Manages      │ • Vector ops    │ • Cost optimize │          │
│   context      │                 │                 │          │
└─────────────────┴─────────────────┴─────────────────┴──────────┘
                               │
                    ┌─────────────────┐
                    │   Data Layer    │
                    │                 │
                    │ • PostgreSQL    │
                    │ • Vector Index  │
                    │ • File Storage  │
                    │ • Audit Logs    │
                    └─────────────────┘
```

## 🔧 Configuration Management

### Environment Configuration Hierarchy

1. **Base Config** (`.env.example`)
   - Default values and documentation
   - All available options

2. **Local Config** (`.env`)
   - Your specific settings
   - Override defaults
   - Not tracked in git

3. **Runtime Config** (`src/core/config.py`)
   - Validates environment variables
   - Type conversion and validation
   - Default value handling

### Key Configuration Sections

- **🔑 Security**: API keys, secrets, encryption
- **🗄️ Database**: Connection strings, pool settings
- **🤖 AI Models**: Model selection, parameters
- **📊 Features**: Enable/disable functionality
- **🔍 Search**: Vector database, indexing
- **💰 Cost Control**: Spending limits, monitoring
- **📈 Monitoring**: Metrics, logging, tracing
- **🌍 Localization**: Languages, regions

## 🗄️ Database Schema Overview

### Core Tables

```sql
-- User Management
users                 -- User accounts and profiles
tenants              -- Multi-tenant organization
user_preferences     -- User settings and preferences

-- Document Management  
documents            -- Document metadata
chunks               -- Text chunks from documents
embeddings           -- Vector embeddings
sources              -- Document sources/references

-- Conversation System
conversations        -- Chat sessions
messages             -- Individual messages
retrievals           -- Retrieved context for answers

-- AI & Learning
experiments          -- A/B testing experiments
feedback             -- User feedback on responses
model_training       -- ML model training data
user_embeddings      -- User behavior embeddings

-- Analytics & Audit
interactions         -- User interaction tracking
audit_logs           -- Security and compliance logs
rag_events           -- System events and metrics

-- Expert System
experts              -- Expert knowledge profiles
citations            -- Answer citations and sources
peer_reviews         -- Expert review system
contributions        -- User contributions
reputation           -- User reputation scores
badges               -- Achievement system

-- Compliance & Privacy
user_consent         -- GDPR consent tracking
data_subject_requests -- Privacy requests (GDPR)
```

### Vector Storage

- **pgvector Extension**: Stores document embeddings
- **Similarity Search**: Fast vector similarity queries
- **Indexing**: HNSW and IVFFlat indexes for performance
- **Hybrid Search**: Combines vector and full-text search

## 🚀 Deployment Configurations

### 🟡 Minimal Setup (`docker-compose.minimal.yml`)
**Use for**: Absolute minimum testing
- ✅ PostgreSQL with pgvector
- ✅ Basic RAG functionality  
- ❌ No caching or advanced features
- 💾 ~200MB RAM usage

### 🟢 Simple Setup (`docker-compose.simple.yml`)
**Use for**: Development and testing  
- ✅ PostgreSQL with pgvector
- ✅ FastAPI backend
- ✅ Complete RAG pipeline
- ✅ All core features
- ❌ No advanced services
- 💾 ~500MB RAM usage

### 🔵 Full Setup (`docker-compose.full.yml`)
**Use for**: Production and advanced features
- ✅ All simple setup features
- ✅ Redis (caching, sessions)
- ✅ Qdrant (advanced vector DB)
- ✅ Elasticsearch (full-text search)
- ✅ MinIO (object storage)
- ✅ Prometheus + Grafana (monitoring)
- ✅ Jaeger (distributed tracing)
- ✅ Celery (background tasks)
- 💾 ~2GB RAM usage

## 🔄 Development Workflow

### 1. Local Development Setup
```bash
# 1. Clone and configure
git clone <repo>
cp .env.example .env
# Edit .env with your settings

# 2. Start backend
./start.sh simple

# 3. Start frontend
cd frontend
npm install --legacy-peer-deps
npm run dev
```

### 2. Backend Development
```bash
# Direct Python development
cd src
python main.py

# Or with Docker for consistency
docker-compose up backend

# Run tests
pytest
pytest --cov=src
```

### 3. Frontend Development
```bash
cd frontend

# Development server
npm run dev

# Type checking
npm run type-check

# Linting and formatting
npm run lint
npm run lint:fix

# Testing
npm test
npm run e2e
```

### 4. Database Development
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Reset database
docker-compose down -v
docker-compose up postgres
```

## 🧪 Testing Strategy

### Test Pyramid

```
                    ┌─────────────┐
                    │     E2E     │  ← Full user journeys
                    │    Tests    │
                ┌───┴─────────────┴───┐
                │   Integration Tests │  ← API endpoints, services
            ┌───┴─────────────────────┴───┐
            │       Unit Tests            │  ← Individual functions
        ┌───┴─────────────────────────────┴───┐
        │         Static Analysis           │  ← Linting, type checking
        └───────────────────────────────────────┘
```

### Test Categories

1. **Unit Tests** (`tests/unit/`)
   - Individual function testing
   - Service logic validation
   - Model behavior testing

2. **Integration Tests** (`tests/integration/`)
   - API endpoint testing
   - Database interaction testing
   - Service integration validation

3. **End-to-End Tests** (`tests/e2e/`)
   - Complete user workflow testing
   - Cross-service functionality
   - UI interaction testing

## 📊 Monitoring & Observability

### Metrics Collection

```
Application Metrics → Prometheus → Grafana Dashboards
         ↓
OpenTelemetry Traces → Jaeger → Distributed Tracing
         ↓
Application Logs → Structured Logging → Log Aggregation
         ↓
Health Checks → Status Endpoints → Uptime Monitoring
```

### Key Metrics

- **Performance**: Response times, throughput
- **Usage**: Active users, queries per day
- **Costs**: Token usage, API costs
- **Quality**: User satisfaction, accuracy
- **System**: Resource usage, error rates

## 🔒 Security Architecture

### Authentication Flow

```
User Request → JWT Validation → Permission Check → Resource Access
     ↓              ↓                 ↓               ↓
  Frontend  →  Auth Middleware → RBAC Check →  API Endpoint
```

### Security Layers

1. **Network Security**: HTTPS, CORS, rate limiting
2. **Authentication**: JWT tokens, secure sessions
3. **Authorization**: Role-based access control (RBAC)
4. **Data Protection**: Encryption at rest and in transit
5. **Privacy Compliance**: GDPR, CCPA features
6. **Audit Trail**: Comprehensive logging

## 🌍 Internationalization

### Supported Features

- **Multi-language UI**: English, Hebrew, Arabic, Spanish, French, German
- **RTL Support**: Right-to-left languages (Hebrew, Arabic)
- **Document Processing**: Multi-language text extraction
- **AI Models**: Language-specific embeddings and LLMs

### Implementation

- **Frontend**: next-i18next for React components
- **Backend**: Language detection and routing
- **Database**: Unicode support, collation settings

## 📈 Scalability Considerations

### Horizontal Scaling Options

1. **API Layer**: Multiple FastAPI instances behind load balancer
2. **Database**: Read replicas, connection pooling
3. **Vector Store**: Distributed vector databases
4. **Caching**: Redis clustering
5. **File Storage**: CDN integration, object storage

### Performance Optimization

- **Caching Strategy**: Multi-level caching (Redis, application, CDN)
- **Database Optimization**: Indexing, query optimization, connection pooling
- **Vector Search**: Optimized indexing, similarity thresholds
- **AI Cost Management**: Model routing, response caching

---

This structure provides a solid foundation for a production-ready RAG platform while maintaining flexibility for future enhancements and scalability requirements.