import pytest
import asyncio
from typing import Dict, Any
from pymongo import MongoClient
import uuid
from datetime import datetime, timezone
import requests

from app.auth import create_access_token

import time
import os

# Configuration from environment variables
FASTAPI_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
TEST_MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://root:root_password@localhost:27017/?authSource=admin")
BASE_DB_NAME = os.getenv("TEST_DB_NAME", "test_oms_db")

@pytest.fixture(scope="session")
def api_client():
    """
    Creates a requests.Session client pointing to the FastAPI service
    running in Docker Compose.
    """
    session = requests.Session()

    # Wait for FastAPI to be ready
    timeout = 30  # seconds - longer for Docker startup
    start = time.time()
    while True:
        try:
            r = session.get(f"{FASTAPI_BASE_URL}/health")  # Use health endpoint
            if r.status_code == 200:
                break
        except requests.exceptions.ConnectionError:
            pass
        if time.time() - start > timeout:
            raise RuntimeError(f"FastAPI service at {FASTAPI_BASE_URL} did not become available in time")
        time.sleep(1)

    yield session

    session.close()


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def worker_id(request):
    """Get worker ID for parallel test execution."""
    if hasattr(request.config, 'workerinput'):
        return request.config.workerinput['workerid']
    return 'master'


@pytest.fixture(scope="function")
def unique_db_name(worker_id: str) -> str:
    """Generate unique database name per test to prevent race conditions."""
    unique_id = str(uuid.uuid4())[:8]
    return f"{BASE_DB_NAME}_{worker_id}_{unique_id}"


@pytest.fixture(scope="function")
def test_db(unique_db_name: str):
    """
    Provide isolated MongoDB database for each test.
    Automatically cleans up after test completion.
    """
    client = MongoClient(TEST_MONGODB_URL)
    db = client[unique_db_name]
    
    # Create indexes for better query performance
    db.orders.create_index("user_id")
    db.orders.create_index("status")
    db.users.create_index("email", unique=True)
    
    yield db
    
    # Cleanup: Drop database after test
    client.drop_database(unique_db_name)
    client.close()


# @pytest.fixture(scope="function")
# def app_client(test_db):
#     """
#     Provide HTTP client with database dependency override.
#     Uses AsyncClient with ASGITransport for proper async support.
#     """
#     def override_get_database():
#         return test_db
    
#     app.dependency_overrides[get_database] = override_get_database
    
#     transport = ASGITransport(app=app)
#     async with AsyncClient(transport=transport, base_url="http://test") as client:
#         yield client
    
#     app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(test_db) -> Dict[str, Any]:
    """Create a test user and return user data with auth token."""
    user_data = {
        "user_id": f"user_{uuid.uuid4().hex[:8]}",
        "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
        "username": f"testuser_{uuid.uuid4().hex[:8]}",
        "role": "customer",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    test_db.users.insert_one(user_data.copy())
    
    # Generate JWT token
    token = create_access_token(
        data={"sub": user_data["user_id"], "role": user_data["role"]}
    )
    
    return {
        **user_data,
        "token": token
    }


@pytest.fixture(scope="function")
def test_admin(test_db) -> Dict[str, Any]:
    """Create a test admin user."""
    admin_data = {
        "user_id": f"admin_{uuid.uuid4().hex[:8]}",
        "email": f"admin_{uuid.uuid4().hex[:8]}@example.com",
        "username": f"admin_{uuid.uuid4().hex[:8]}",
        "role": "admin",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    test_db.users.insert_one(admin_data.copy())
    
    token = create_access_token(
        data={"sub": admin_data["user_id"], "role": admin_data["role"]}
    )
    
    return {
        **admin_data,
        "token": token
    }


@pytest.fixture
def sample_order_data() -> Dict[str, Any]:
    """Generate sample order data for testing."""
    return {
        "user_id": f"user_{uuid.uuid4().hex[:8]}",
        "items": [
            {
                "product_id": "p001",
                "name": "Laptop",
                "price": 1200.00,
                "quantity": 1
            },
            {
                "product_id": "p002",
                "name": "Mouse",
                "price": 25.00,
                "quantity": 2
            }
        ],
        "total_price": 1250.00,
        "status": "Pending"
    }


@pytest.fixture
def auth_headers(test_user: Dict[str, Any]) -> Dict[str, str]:
    """Generate authorization headers for API requests."""
    return {"Authorization": f"Bearer {test_user['token']}"}


@pytest.fixture
def admin_headers(test_admin: Dict[str, Any]) -> Dict[str, str]:
    """Generate admin authorization headers."""
    return {"Authorization": f"Bearer {test_admin['token']}"}