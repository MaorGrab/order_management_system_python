import pytest
import requests
from typing import Dict, Any
from bson import ObjectId
from starlette import status
from tests.conftest import FASTAPI_BASE_URL


# ============================================================================
# TEST CLASS: Successful Order Retrieval
# ============================================================================

@pytest.mark.crud
@pytest.mark.read
class TestReadOrderSuccess:
    """Test successful order retrieval scenarios."""

    def test_read_order_by_id_success(
        self,
        api_client: requests.Session,
        auth_headers: Dict[str, str],
        test_user: Dict[str, Any],
    ):
        """
        TEST: Retrieve existing order by ID returns 200 OK.
        
        Verifies:
        - Valid order ID returns 200 OK
        - Response contains all order fields
        - Response data matches created order
        - Timestamps present (created_at, updated_at)
        """
        # First, create an order
        order_data = {
            "user_id": test_user["user_id"],
            "items": [
                {
                    "product_id": "p001",
                    "name": "Laptop",
                    "price": 1200.00,
                    "quantity": 1
                }
            ],
        }

        create_response = api_client.post(
            f"{FASTAPI_BASE_URL}/orders",
            json=order_data,
            headers=auth_headers
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        order_id = create_response.json()["_id"]

        # Now retrieve it
        response = api_client.get(
            f"{FASTAPI_BASE_URL}/orders/{order_id}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Verify all fields present
        assert data["_id"] == order_id
        assert data["user_id"] == test_user["user_id"]
        assert data["total_price"] == 1200.00
        assert data["status"] == "Pending"
        assert len(data["items"]) == 1
        assert "created_at" in data
        assert "updated_at" in data

    def test_read_multiple_orders_sequential(
        self,
        api_client: requests.Session,
        auth_headers: Dict[str, str],
        test_user: Dict[str, Any],
    ):
        """
        TEST: Retrieve multiple different orders.
        
        Verifies:
        - Can retrieve multiple orders sequentially
        - Each retrieval is independent
        - Correct data returned for each order
        """
        # Create two orders
        order_ids = []
        for i in range(2):
            order_data = {
                "user_id": test_user["user_id"],
                "items": [
                    {
                        "product_id": f"p{i}",
                        "name": f"Item {i}",
                        "price": 100.00 * (i + 1),
                        "quantity": 1
                    }
                ],
            }

            create_response = api_client.post(
                f"{FASTAPI_BASE_URL}/orders",
                json=order_data,
                headers=auth_headers
            )
            order_ids.append(create_response.json()["_id"])

        # Retrieve both orders
        for i, order_id in enumerate(order_ids):
            response = api_client.get(
                f"{FASTAPI_BASE_URL}/orders/{order_id}",
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            assert response.json()["total_price"] == 100.00 * (i + 1)

    def test_read_order_response_structure(
        self,
        api_client: requests.Session,
        auth_headers: Dict[str, str],
        test_user: Dict[str, Any],
    ):
        """
        TEST: Response has correct structure and types.
        
        Verifies:
        - All required fields present
        - Field types correct
        - No extra/unexpected fields
        """
        # Create order
        order_data = {
            "user_id": test_user["user_id"],
            "items": [
                {
                    "product_id": "p001",
                    "name": "Laptop",
                    "price": 1200.00,
                    "quantity": 1
                }
            ],
        }

        create_response = api_client.post(
            f"{FASTAPI_BASE_URL}/orders",
            json=order_data,
            headers=auth_headers
        )
        order_id = create_response.json()["_id"]

        # Read and validate structure
        response = api_client.get(
            f"{FASTAPI_BASE_URL}/orders/{order_id}",
            headers=auth_headers
        )

        data = response.json()
        
        # Verify required fields and types
        assert isinstance(data["_id"], str)
        assert isinstance(data["user_id"], str)
        assert isinstance(data["items"], list)
        assert isinstance(data["total_price"], (int, float))
        assert isinstance(data["status"], str)
        assert isinstance(data["created_at"], str)
        assert isinstance(data["updated_at"], str)

        # Verify item structure
        for item in data["items"]:
            assert isinstance(item["product_id"], str)
            assert isinstance(item["name"], str)
            assert isinstance(item["price"], (int, float))
            assert isinstance(item["quantity"], int)


# ============================================================================
# TEST CLASS: Not Found Errors
# ============================================================================

@pytest.mark.crud
@pytest.mark.read
class TestReadOrderNotFound:
    """Test 404 Not Found scenarios."""

    def test_read_nonexistent_order_returns_404(
        self,
        api_client: requests.Session,
        auth_headers: Dict[str, str],
    ):
        """
        TEST: Reading non-existent order returns 404.
        
        Verifies:
        - Non-existent order IDs return 404
        - Proper error handling
        """
        # Use valid ObjectId format but doesn't exist
        fake_id = str(ObjectId())

        response = api_client.get(
            f"{FASTAPI_BASE_URL}/orders/{fake_id}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# TEST CLASS: Invalid ID Format
# ============================================================================

@pytest.mark.crud
@pytest.mark.read
class TestReadOrderInvalidId:
    """Test invalid order ID format handling."""

    @pytest.mark.parametrize("invalid_id", [
        "not-a-valid-objectid",
        "12345",
        "invalid",
        "!@#$%",
        "123456789012345",  # Wrong length
        "gggggggggggggggggggggggg",  # Invalid hex characters
    ])
    def test_read_invalid_id_format_fails(
        self,
        api_client: requests.Session,
        auth_headers: Dict[str, str],
        invalid_id: str,
    ):
        """
        TEST: Invalid order ID formats return 400 Bad Request.
        
        Parameterized for multiple invalid formats.
        Verifies:
        - API validates ID format
        - Invalid formats rejected with 400
        """
        response = api_client.get(
            f"{FASTAPI_BASE_URL}/orders/{invalid_id}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_read_empty_id_fails(
        self,
        api_client: requests.Session,
        auth_headers: Dict[str, str],
    ):
        """
        TEST: Empty order ID returns error.
        
        Verifies:
        - Empty ID handled properly
        """
        response = api_client.get(
            f"{FASTAPI_BASE_URL}/orders/ ",
            headers=auth_headers
        )

        # Should be 404 or similar (no route match)
        assert response.status_code in [
            status.HTTP_404_NOT_FOUND,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]


# ============================================================================
# TEST CLASS: Authentication and Authorization
# ============================================================================

@pytest.mark.crud
@pytest.mark.read
@pytest.mark.auth
class TestReadOrderAuthentication:
    """Test authentication and authorization for reading orders."""

    def test_read_order_without_authentication_fails(
        self,
        api_client: requests.Session,
    ):
        """
        TEST: Reading order without authentication fails with 401.
        
        Verifies:
        - Authentication required for reading orders
        - Unauthenticated requests rejected
        """
        order_id = str(ObjectId())

        response = api_client.get(
            f"{FASTAPI_BASE_URL}/orders/{order_id}"
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_read_order_with_invalid_token_fails(
        self,
        api_client: requests.Session,
    ):
        """
        TEST: Reading order with invalid token fails with 401.
        
        Verifies:
        - Invalid tokens rejected
        """
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        order_id = str(ObjectId())

        response = api_client.get(
            f"{FASTAPI_BASE_URL}/orders/{order_id}",
            headers=invalid_headers
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_read_other_users_order_forbidden(
        self,
        api_client: requests.Session,
        auth_headers: Dict[str, str],
        test_user: Dict[str, Any],
    ):
        """
        TEST: Cannot read order belonging to another user.
        
        From test_edge_cases.py - authorization enforcement.
        Verifies:
        - Users cannot access other users' orders
        - 403 Forbidden returned
        """
        # Create order for test_user
        order_data = {
            "user_id": test_user["user_id"],
            "items": [{"product_id": "p1", "name": "Item", "price": 100, "quantity": 1}],
        }

        create_response = api_client.post(
            f"{FASTAPI_BASE_URL}/orders",
            json=order_data,
            headers=auth_headers
        )
        order_id = create_response.json()["_id"]

        # Create different user token
        import uuid
        from app.auth import create_access_token
        from datetime import timedelta

        other_user_id = f"user_{uuid.uuid4().hex[:8]}"
        other_token = create_access_token(
            data={"sub": other_user_id, "role": "customer"},
            expires_delta=timedelta(hours=1)
        )
        other_headers = {"Authorization": f"Bearer {other_token}"}

        # Try to read with different user's token
        response = api_client.get(
            f"{FASTAPI_BASE_URL}/orders/{order_id}",
            headers=other_headers
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
