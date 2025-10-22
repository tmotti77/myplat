"""Test application structure and imports."""
import sys
print("Testing application structure...\n")

# Test main app import
print("1. Testing main app import...")
try:
    from src.main import app
    print(f"   ✓ Main app imported successfully")
    print(f"   App title: {app.title}")
    print(f"   App version: {app.version}")
except Exception as e:
    print(f"   ✗ Failed to import main app: {e}")
    print(f"   This is expected if database is required during import")

# Test minimal app
print("\n2. Testing minimal app import...")
try:
    from src.main_minimal import app as minimal_app
    print(f"   ✓ Minimal app imported successfully")
    print(f"   App title: {minimal_app.title}")
    print(f"   App version: {minimal_app.version}")
except Exception as e:
    print(f"   ✗ Failed to import minimal app: {e}")

# Test API routers
print("\n3. Testing API router imports...")
routers_to_test = [
    "src.api.auth",
    "src.api.documents",
    "src.api.search",
    "src.api.chat",
    "src.api.admin"
]

for router_module in routers_to_test:
    try:
        __import__(router_module)
        print(f"   ✓ {router_module}")
    except Exception as e:
        print(f"   ✗ {router_module}: {e}")

# Test services
print("\n4. Testing service imports...")
services_to_test = [
    "src.services.embedding",
    "src.services.rag",
    "src.services.chat",
    "src.services.search"
]

for service_module in services_to_test:
    try:
        __import__(service_module)
        print(f"   ✓ {service_module}")
    except Exception as e:
        print(f"   ✗ {service_module}: {e}")

# Test models
print("\n5. Testing model imports...")
models_to_test = [
    "src.models.user",
    "src.models.document",
    "src.models.chat",
    "src.models.audit"
]

for model_module in models_to_test:
    try:
        __import__(model_module)
        print(f"   ✓ {model_module}")
    except Exception as e:
        print(f"   ✗ {model_module}: {e}")

print("\n✅ Application structure tests completed!")
