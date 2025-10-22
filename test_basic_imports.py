"""Test basic imports and configuration loading."""
import sys
print(f"Python version: {sys.version}")
print(f"Python path: {sys.executable}\n")

# Test basic imports
print("Testing basic imports...")
try:
    import fastapi
    print(f"✓ FastAPI: {fastapi.__version__}")
except ImportError as e:
    print(f"✗ FastAPI: {e}")

try:
    import pydantic
    print(f"✓ Pydantic: {pydantic.__version__}")
except ImportError as e:
    print(f"✗ Pydantic: {e}")

try:
    import sqlalchemy
    print(f"✓ SQLAlchemy: {sqlalchemy.__version__}")
except ImportError as e:
    print(f"✗ SQLAlchemy: {e}")

try:
    import uvicorn
    print(f"✓ Uvicorn: {uvicorn.__version__}")
except ImportError as e:
    print(f"✗ Uvicorn: {e}")

# Test src imports
print("\nTesting src module imports...")
try:
    from src.core import config
    print("✓ src.core.config")
except ImportError as e:
    print(f"✗ src.core.config: {e}")

try:
    from src.core import logging
    print("✓ src.core.logging")
except ImportError as e:
    print(f"✗ src.core.logging: {e}")

try:
    from src.models import user
    print("✓ src.models.user")
except ImportError as e:
    print(f"✗ src.models.user: {e}")

try:
    from src.services import embedding
    print("✓ src.services.embedding")
except ImportError as e:
    print(f"✗ src.services.embedding: {e}")

print("\n✅ All imports successful!")
