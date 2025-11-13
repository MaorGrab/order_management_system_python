import pytest
import requests
from typing import Dict, Any
from pymongo.database import Database
import httpx

FASTAPI_BASE_URL = "http://localhost:8000"


@pytest.mark.crud
@pytest.mark.asyncio
async def test_create_order_good(
    api_client: requests.Session,
    auth_headers: Dict[str, str],
    test_user: Dict[str, Any],
    
):
    """Test that orders with negative prices are rejected."""
    invalid_order = {
        "user_id": test_user["user_id"],
        "items": [
            {
                "product_id": "p001",
                "name": "Laptop",
                "price": 1200.00,
                "quantity": 1
            }
        ],
        "total_price": 1200.00
    }
    
    async with httpx.AsyncClient(base_url=FASTAPI_BASE_URL) as api_client:
        response = await api_client.post(
            "/api/v1/orders",
            json=invalid_order,
            headers=auth_headers
        )
    
    assert response.status_code == 201

@pytest.mark.crud
def test_create_order_with_negative_price(
    api_client: requests.Session,
    auth_headers: Dict[str, str],
    test_user: Dict[str, Any],
    
):
    """Test that orders with negative prices are rejected."""
    invalid_order = {
        "user_id": test_user["user_id"],
        "items": [
            {
                "product_id": "p001",
                "name": "Laptop",
                "price": -1200.00,
                "quantity": 1
            }
        ],
        "total_price": -1200.00
    }
    
    response = api_client.post(
        f"{FASTAPI_BASE_URL}/api/v1/orders",
        json=invalid_order,
        headers=auth_headers
    )
    
    assert response.status_code == 422
    assert "price" in str(response.json()).lower()


@pytest.mark.crud
def test_create_order_with_zero_quantity(
    api_client: requests.Session,
    auth_headers: Dict[str, str],
    test_user: Dict[str, Any],
    # override_db_dependency
):
    """Test that orders with zero quantity are rejected."""
    invalid_order = {
        "user_id": test_user["user_id"],
        "items": [
            {
                "product_id": "p001",
                "name": "Laptop",
                "price": 1200.00,
                "quantity": 0
            }
        ],
        "total_price": 0
    }
    
    response = api_client.post(
        f"{FASTAPI_BASE_URL}/api/v1/orders",
        json=invalid_order,
        headers=auth_headers
    )
    
    assert response.status_code == 422


@pytest.mark.crud
def test_create_order_empty_items_list(
    api_client: requests.Session,
    auth_headers: Dict[str, str],
    test_user: Dict[str, Any],
    # override_db_dependency
):
    """Test that orders with no items are rejected."""
    invalid_order = {
        "user_id": test_user["user_id"],
        "items": [],
        "total_price": 0
    }
    
    response = api_client.post(
        f"{FASTAPI_BASE_URL}/api/v1/orders",
        json=invalid_order,
        headers=auth_headers
    )
    
    assert response.status_code == 422


@pytest.mark.crud
def test_update_with_invalid_status(
    api_client: requests.Session,
    test_user: Dict[str, Any],
    admin_headers: Dict[str, str],
    auth_headers: Dict[str, str],
    sample_order_data: Dict[str, Any],
    # override_db_dependency
):
    """Test that invalid status transitions are rejected."""
    # Create order
    sample_order_data["user_id"] = test_user["user_id"]
    create_response = api_client.post(
        f"{FASTAPI_BASE_URL}/api/v1/orders",
        json=sample_order_data,
        headers=auth_headers
    )
    order_id = create_response.json()["id"]
    
    # Try invalid status
    invalid_update = {"status": "InvalidStatus"}
    response = api_client.patch(
        f"{FASTAPI_BASE_URL}/api/v1/orders/{order_id}",
        json=invalid_update,
        headers=admin_headers
    )
    
    assert response.status_code == 422


@pytest.mark.auth
def test_create_order_without_authentication(
    api_client: requests.Session,
    sample_order_data: Dict[str, Any],
    # override_db_dependency
):
    """Test that unauthenticated requests are rejected."""
    response = api_client.post(
        f"{FASTAPI_BASE_URL}/api/v1/orders",
        json=sample_order_data
    )
    
    assert response.status_code == 401


@pytest.mark.auth
def test_create_order_with_invalid_token(
    api_client: requests.Session,
    sample_order_data: Dict[str, Any],
    # override_db_dependency
):
    """Test that invalid JWT tokens are rejected."""
    invalid_headers = {"Authorization": "Bearer invalid_token_here"}
    
    response = api_client.post(
        f"{FASTAPI_BASE_URL}/api/v1/orders",
        json=sample_order_data,
        headers=invalid_headers
    )
    
    assert response.status_code == 401


@pytest.mark.auth
def test_get_order_belonging_to_another_user(
    api_client: requests.Session,
    test_db: Database,
    test_user: Dict[str, Any],
    auth_headers: Dict[str, str],
    sample_order_data: Dict[str, Any],
    # override_db_dependency
):
    """Test that users cannot access other users' orders."""
    # Create order for first user
    sample_order_data["user_id"] = test_user["user_id"]
    create_response = api_client.post(
        f"{FASTAPI_BASE_URL}/api/v1/orders",
        json=sample_order_data,
        headers=auth_headers
    )
    order_id = create_response.json()["id"]
    
    # Create second user with different token
    import uuid
    from app.auth import create_access_token
    from datetime import timedelta
    
    other_user = {
        "user_id": f"user_{uuid.uuid4().hex[:8]}",
        "role": "customer"
    }
    other_token = create_access_token(
        data={"sub": other_user["user_id"], "role": "customer"},
        expires_delta=timedelta(hours=1)
    )
    other_headers = {"Authorization": f"Bearer {other_token}"}
    
    # Try to access with different user
    response = api_client.get(
        f"{FASTAPI_BASE_URL}/api/v1/orders/{order_id}",
        headers=other_headers
    )
    
    assert response.status_code == 403


@pytest.mark.crud
def test_create_order_for_different_user(
    api_client: requests.Session,
    auth_headers: Dict[str, str],
    sample_order_data: Dict[str, Any],
    # override_db_dependency
):
    """Test that users cannot create orders for other users."""
    # Try to create order with different user_id than token
    sample_order_data["user_id"] = "different_user_123"
    
    response = api_client.post(
        f"{FASTAPI_BASE_URL}/api/v1/orders",
        json=sample_order_data,
        headers=auth_headers
    )
    
    assert response.status_code == 403


@pytest.mark.crud
def test_invalid_order_id_format(
    api_client: requests.Session,
    auth_headers: Dict[str, str],
    # override_db_dependency
):
    """Test that invalid ObjectId formats are handled."""
    invalid_id = "not-a-valid-objectid"
    
    response = api_client.get(
        f"{FASTAPI_BASE_URL}/api/v1/orders/{invalid_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 400