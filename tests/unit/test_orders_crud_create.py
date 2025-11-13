import pytest
import requests
from typing import Dict, Any
from starlette import status

from tests.conftest import FASTAPI_BASE_URL


@pytest.mark.crud
@pytest.mark.create
def test_create_order_with_valid_data_success(
    api_client: requests.Session,
    auth_headers: Dict[str, str],
    test_user: Dict[str, Any],
):
    """Test creating order with valid data returns 201."""
    order_data = {
        "user_id": test_user["user_id"],
        "items": [
            {
                "product_id": "p001",
                "name": "Laptop",
                "price": 1200.00,
                "quantity": 1
            }
        ]
    }
    
    response = api_client.post(
        f"{FASTAPI_BASE_URL}/orders",
        json=order_data,
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["user_id"] == test_user["user_id"]
    assert data["status"] == "Pending"
    assert data["total_price"] == 1200.00


@pytest.mark.crud
@pytest.mark.create
def test_create_order_missing_user_id(
    api_client: requests.Session,
    auth_headers: Dict[str, str],
):
    """Test creating order without user_id fails with 422."""
    order_data = {
        "items": [{"product_id": "p1", "name": "Item", "price": 100, "quantity": 1}]
    }
    
    response = api_client.post(
        f"{FASTAPI_BASE_URL}/orders",
        json=order_data,
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.crud
@pytest.mark.create
def test_create_order_empty_items_array(
    api_client: requests.Session,
    auth_headers: Dict[str, str],
    test_user: Dict[str, Any],
):
    """Test creating order with empty items fails with 422."""
    order_data = {
        "user_id": test_user["user_id"],
        "items": []
    }
    
    response = api_client.post(
        f"{FASTAPI_BASE_URL}/orders",
        json=order_data,
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.crud
@pytest.mark.create
def test_create_order_negative_price(
    api_client: requests.Session,
    auth_headers: Dict[str, str],
    test_user: Dict[str, Any],
):
    """Test creating order with negative price fails with 422."""
    order_data = {
        "user_id": test_user["user_id"],
        "items": [
            {
                "product_id": "p1",
                "name": "Item",
                "price": -100,
                "quantity": 1
            }
        ]
    }
    
    response = api_client.post(
        f"{FASTAPI_BASE_URL}/orders",
        json=order_data,
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.crud
@pytest.mark.create
def test_create_order_for_different_user_forbidden(
    api_client: requests.Session,
    auth_headers: Dict[str, str],
):
    """Test creating order for different user fails with 403."""
    order_data = {
        "user_id": "different_user_123",
        "items": [{"product_id": "p1", "name": "Item", "price": 100, "quantity": 1}]
    }
    
    response = api_client.post(
        f"{FASTAPI_BASE_URL}/orders",
        json=order_data,
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.parametrize("total_price,items", [
    (100, [{"product_id": "p1", "name": "Item1", "price": 100, "quantity": 1}]),
    (250, [
        {"product_id": "p1", "name": "Item1", "price": 100, "quantity": 1},
        {"product_id": "p2", "name": "Item2", "price": 150, "quantity": 1}
    ]),
])
@pytest.mark.crud
@pytest.mark.create
def test_create_order_various_prices(
    api_client: requests.Session,
    auth_headers: Dict[str, str],
    test_user: Dict[str, Any],
    total_price,
    items,
):
    """Test creating orders with various valid price combinations."""
    order_data = {
        "user_id": test_user["user_id"],
        "items": items
    }
    
    response = api_client.post(
        f"{FASTAPI_BASE_URL}/orders",
        json=order_data,
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["total_price"] == total_price
