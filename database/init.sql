-- Initialize PostgreSQL with pgvector extension and basic setup
-- This script runs automatically when the PostgreSQL container starts

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create application database if it doesn't exist
-- (This will be handled by docker-compose environment variables)

-- Set default configuration for full-text search
SET default_text_search_config = 'simple';

-- Create custom text search configuration for Hebrew
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_ts_config WHERE cfgname = 'hebrew'
    ) THEN
        CREATE TEXT SEARCH CONFIGURATION hebrew (COPY = simple);
    END IF;
END $$;

-- Create custom text search configuration for Arabic  
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_ts_config WHERE cfgname = 'arabic'
    ) THEN
        CREATE TEXT SEARCH CONFIGURATION arabic (COPY = simple);
    END IF;
END $$;

-- Create custom functions for vector operations
CREATE OR REPLACE FUNCTION vector_norm(vector)
RETURNS float8 AS $$
BEGIN
    RETURN sqrt((SELECT sum(val * val) FROM unnest($1) AS val));
END;
$$ LANGUAGE plpgsql IMMUTABLE STRICT;

-- Create function for cosine similarity (if not available)
CREATE OR REPLACE FUNCTION cosine_similarity(a vector, b vector)
RETURNS float8 AS $$
BEGIN
    RETURN (a <#> b) / (vector_norm(a) * vector_norm(b));
END;
$$ LANGUAGE plpgsql IMMUTABLE STRICT;

-- Create function for computing document freshness score
CREATE OR REPLACE FUNCTION freshness_score(created_at timestamptz, ttl interval)
RETURNS float8 AS $$
BEGIN
    IF ttl IS NULL THEN
        RETURN 1.0; -- No TTL means always fresh
    END IF;
    
    IF created_at + ttl < NOW() THEN
        RETURN 0.0; -- Expired
    END IF;
    
    -- Linear decay from 1.0 to 0.1 over the TTL period
    RETURN GREATEST(0.1, 1.0 - (EXTRACT(EPOCH FROM (NOW() - created_at)) / EXTRACT(EPOCH FROM ttl)) * 0.9);
END;
$$ LANGUAGE plpgsql IMMUTABLE STRICT;

-- Create function for hybrid search scoring
CREATE OR REPLACE FUNCTION hybrid_search_score(
    vector_score float8,
    fts_rank float4,
    freshness float8,
    trust_score float8,
    vector_weight float8 DEFAULT 0.7,
    fts_weight float8 DEFAULT 0.2,
    freshness_weight float8 DEFAULT 0.05,
    trust_weight float8 DEFAULT 0.05
)
RETURNS float8 AS $$
BEGIN
    RETURN (
        vector_score * vector_weight +
        fts_rank * fts_weight +
        freshness * freshness_weight +
        trust_score * trust_weight
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE STRICT;

-- Grant permissions to application user
GRANT ALL PRIVILEGES ON DATABASE rag_platform TO rag_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO rag_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO rag_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO rag_user;

-- Set up row level security preparation
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO rag_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO rag_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO rag_user;