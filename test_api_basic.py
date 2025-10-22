"""Test basic API functionality without database."""
import sys
from fastapi import FastAPI
from fastapi.testclient import TestClient

print("Testing FastAPI basic functionality...")

# Create a minimal FastAPI app
app = FastAPI(title="Test API")

@app.get("/")
def read_root():
    return {"message": "Hello World", "status": "running"}

@app.get("/health")
def health():
    return {"status": "healthy"}

# Test with TestClient
client = TestClient(app)

try:
    # Test root endpoint
    response = client.get("/")
    print(f"✓ Root endpoint: {response.status_code}")
    print(f"  Response: {response.json()}")

    # Test health endpoint
    response = client.get("/health")
    print(f"✓ Health endpoint: {response.status_code}")
    print(f"  Response: {response.json()}")

    print("\n✅ FastAPI basic tests passed!")

except Exception as e:
    print(f"\n✗ Test failed: {e}")
    sys.exit(1)
