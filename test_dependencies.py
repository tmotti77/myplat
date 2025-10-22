#!/usr/bin/env python3
"""Test script to verify all dependencies are working in the Docker container."""

import sys
import traceback

def test_import(module_name, package_name=None):
    """Test importing a module and return status."""
    try:
        __import__(module_name)
        print(f"✓ {package_name or module_name}")
        return True
    except Exception as e:
        print(f"✗ {package_name or module_name}: {e}")
        return False

def main():
    print("Testing dependency imports in Docker container...")
    print("=" * 60)
    
    success_count = 0
    total_count = 0
    
    # Core dependencies
    dependencies = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("pydantic", "Pydantic"),
        ("sqlalchemy", "SQLAlchemy"),
        ("asyncpg", "AsyncPG"),
        ("redis", "Redis"),
        ("httpx", "HTTPX"),
        ("aiofiles", "AIOFiles"),
        ("minio", "MinIO"),
        ("prometheus_fastapi_instrumentator", "Prometheus FastAPI Instrumentator"),
        
        # ML Dependencies
        ("numpy", "NumPy"),
        ("pandas", "Pandas"),
        ("scikit-learn", "Scikit-learn"),
        ("torch", "PyTorch"),
        ("transformers", "Transformers"),
        ("sentence_transformers", "Sentence Transformers"),
        ("langchain", "LangChain"),
        ("unstructured", "Unstructured"),
        
        # AI/LLM Dependencies
        ("openai", "OpenAI"),
        ("anthropic", "Anthropic"),
        ("google.generativeai", "Google Generative AI"),
        ("litellm", "LiteLLM"),
        
        # Data Processing
        ("presidio_analyzer", "Presidio Analyzer"),
        ("presidio_anonymizer", "Presidio Anonymizer"),
        
        # Vector/Search
        ("pgvector", "PGVector"),
        ("elasticsearch", "Elasticsearch"),
        ("qdrant_client", "Qdrant Client"),
        
        # Task Queue
        ("celery", "Celery"),
        
        # Missing packages that need to be added
        ("email_validator", "Email Validator"),
    ]
    
    for module_name, display_name in dependencies:
        if test_import(module_name, display_name):
            success_count += 1
        total_count += 1
    
    print("=" * 60)
    print(f"Import Test Results: {success_count}/{total_count} successful")
    
    if success_count == total_count:
        print("🎉 All dependencies imported successfully!")
    else:
        print(f"⚠️  {total_count - success_count} dependencies need attention")
    
    # Test ML functionality specifically
    print("\nTesting ML Library Compatibility...")
    print("-" * 40)
    
    try:
        import torch
        print(f"PyTorch version: {torch.__version__}")
        print(f"CUDA available: {torch.cuda.is_available()}")
    except:
        pass
    
    try:
        import transformers
        print(f"Transformers version: {transformers.__version__}")
    except:
        pass
    
    try:
        import sentence_transformers
        print("Sentence Transformers: Available")
    except Exception as e:
        print(f"Sentence Transformers: Not available - {e}")

if __name__ == "__main__":
    main()