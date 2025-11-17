import pytest
from typing import Dict, Any
from starlette import status
from fastapi.testclient import TestClient
from tests.conftest import FASTAPI_BASE_URL

# ============================================================================
# TEST CLASS: Valid Order Creation
# ============================================================================

@pytest.mark.crud
@pytest.mark.create
class TestCreateOrderSuccess:
    """Test successful order creation scenarios."""

    def test_create_order_with_valid_data_success(
        self,
        sync_client: TestClient,
        auth_headers: Dict[str, str],
        test_user: Dict[str, Any],
    ):
        """
        TEST: Create order with valid data returns 201 Created.
        
        Verifies:
        - API accepts valid order data
        - Returns 201 Created status
        - Response contains user_id, status, total_price
        - Order is marked as 'Pending' initially
        """
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

        response = sync_client.post(
            f"{FASTAPI_BASE_URL}/orders",
            json=order_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["user_id"] == test_user["user_id"]
        assert data["status"] == "Pending"
        assert data["total_price"] == 1200.00
        assert "_id" in data  # Order ID assigned

    def test_create_order_with_multiple_items(
        self,
        sync_client: TestClient,
        auth_headers: Dict[str, str],
        test_user: Dict[str, Any],
    ):
        """
        TEST: Create order with multiple items.
        
        Verifies:
        - API handles multiple items in single order
        - All items are preserved
        - Total price calculated correctly
        """
        order_data = {
            "user_id": test_user["user_id"],
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
                    "price": 50.00,
                    "quantity": 2
                },
                {
                    "product_id": "p003",
                    "name": "Keyboard",
                    "price": 150.00,
                    "quantity": 1
                }
            ],
        }

        response = sync_client.post(
            f"{FASTAPI_BASE_URL}/orders",
            json=order_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert len(data["items"]) == 3
        assert data["total_price"] == 1450.00

    @pytest.mark.parametrize("total_price,items", [
        (100.00, [{"product_id": "p1", "name": "Item1", "price": 100.00, "quantity": 1}]),
        (250.00, [
            {"product_id": "p1", "name": "Item1", "price": 100.00, "quantity": 1},
            {"product_id": "p2", "name": "Item2", "price": 150.00, "quantity": 1}
        ]),
        (500.00, [
            {"product_id": "p1", "name": "Item1", "price": 250.00, "quantity": 1},
            {"product_id": "p2", "name": "Item2", "price": 250.00, "quantity": 1}
        ]),
    ])
    def test_create_order_various_prices(
        self,
        sync_client: TestClient,
        auth_headers: Dict[str, str],
        test_user: Dict[str, Any],
        total_price: float,
        items: list,
    ):
        """
        TEST: Create orders with various valid price combinations.
        
        Parameterized test covering multiple price scenarios.
        """
        order_data = {
            "user_id": test_user["user_id"],
            "items": items,
        }

        response = sync_client.post(
            f"{FASTAPI_BASE_URL}/orders",
            json=order_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["total_price"] == total_price


# ============================================================================
# TEST CLASS: Input Validation (Missing Fields)
# ============================================================================

@pytest.mark.crud
@pytest.mark.create
@pytest.mark.validation
class TestCreateOrderValidation:
    """Test input validation for order creation."""

    def test_create_order_missing_user_id(
        self,
        sync_client: TestClient,
        auth_headers: Dict[str, str],
    ):
        """
        TEST: Creating order without user_id fails with 422.
        
        Verifies:
        - user_id is required field
        - API rejects missing user_id
        - Returns proper error status
        """
        order_data = {
            "items": [{"product_id": "p1", "name": "Item", "price": 100, "quantity": 1}],
        }

        response = sync_client.post(
            f"{FASTAPI_BASE_URL}/orders",
            json=order_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_order_missing_items(
        self,
        sync_client: TestClient,
        auth_headers: Dict[str, str],
        test_user: Dict[str, Any],
    ):
        """
        TEST: Creating order without items fails with 422.
        
        Verifies:
        - items is required field
        - API rejects missing items
        """
        order_data = {
            "user_id": test_user["user_id"],
        }

        response = sync_client.post(
            f"{FASTAPI_BASE_URL}/orders",
            json=order_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_order_empty_items_array(
        self,
        sync_client: TestClient,
        auth_headers: Dict[str, str],
        test_user: Dict[str, Any],
    ):
        """
        TEST: Creating order with empty items array fails with 422.
        
        Verifies:
        - items array cannot be empty
        - API validates array is not empty
        """
        order_data = {
            "user_id": test_user["user_id"],
            "items": [],
        }

        response = sync_client.post(
            f"{FASTAPI_BASE_URL}/orders",
            json=order_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================================================
# TEST CLASS: Price Validation (Edge Cases)
# ============================================================================

@pytest.mark.crud
@pytest.mark.create
@pytest.mark.validation
class TestCreateOrderPriceValidation:
    """Test price validation for order creation."""

    def test_create_order_negative_price(
        self,
        sync_client: TestClient,
        auth_headers: Dict[str, str],
        test_user: Dict[str, Any],
    ):
        """
        TEST: Creating order with negative price fails with 422.
        
        Verifies:
        - Negative prices rejected
        - API validates price is positive
        - Error message references 'price'
        """
        order_data = {
            "user_id": test_user["user_id"],
            "items": [
                {
                    "product_id": "p001",
                    "name": "Laptop",
                    "price": -1200.00,
                    "quantity": 1
                }
            ],
        }

        response = sync_client.post(
            f"{FASTAPI_BASE_URL}/orders",
            json=order_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "price" in str(response.json()).lower()

    def test_create_order_zero_price(
        self,
        sync_client: TestClient,
        auth_headers: Dict[str, str],
        test_user: Dict[str, Any],
    ):
        """
        TEST: Creating order with zero price.
        
        Note: Depending on business logic, zero price might be allowed
        (promotional items, discounts). This test documents the behavior.
        """
        order_data = {
            "user_id": test_user["user_id"],
            "items": [
                {
                    "product_id": "p001",
                    "name": "Free Item",
                    "price": 0.00,
                    "quantity": 1
                }
            ],
        }

        response = sync_client.post(
            f"{FASTAPI_BASE_URL}/orders",
            json=order_data,
            headers=auth_headers
        )

        # Depending on business logic:
        # If zero prices not allowed: assert response.status_code == 422
        # If zero prices allowed: assert response.status_code == 201
        # Document the actual behavior
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_422_UNPROCESSABLE_ENTITY]


# ============================================================================
# TEST CLASS: Quantity Validation (Edge Cases)
# ============================================================================

@pytest.mark.crud
@pytest.mark.create
@pytest.mark.validation
class TestCreateOrderQuantityValidation:
    """Test quantity validation for order items."""

    def test_create_order_with_zero_quantity(
        self,
        sync_client: TestClient,
        auth_headers: Dict[str, str],
        test_user: Dict[str, Any],
    ):
        """
        TEST: Creating order with zero quantity fails with 422.
        
        Verifies:
        - Quantity must be positive
        - API rejects zero quantity
        """
        order_data = {
            "user_id": test_user["user_id"],
            "items": [
                {
                    "product_id": "p001",
                    "name": "Laptop",
                    "price": 1200.00,
                    "quantity": 0
                }
            ],
        }

        response = sync_client.post(
            f"{FASTAPI_BASE_URL}/orders",
            json=order_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_order_with_negative_quantity(
        self,
        sync_client: TestClient,
        auth_headers: Dict[str, str],
        test_user: Dict[str, Any],
    ):
        """
        TEST: Creating order with negative quantity fails with 422.
        """
        order_data = {
            "user_id": test_user["user_id"],
            "items": [
                {
                    "product_id": "p001",
                    "name": "Laptop",
                    "price": 1200.00,
                    "quantity": -5
                }
            ],
        }

        response = sync_client.post(
            f"{FASTAPI_BASE_URL}/orders",
            json=order_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.parametrize("quantity", [1, 5, 10, 100, 1000])
    def test_create_order_valid_quantities(
        self,
        sync_client: TestClient,
        auth_headers: Dict[str, str],
        test_user: Dict[str, Any],
        quantity: int,
    ):
        """
        TEST: Create orders with various valid quantities.
        
        Parameterized test for valid quantity values.
        """
        order_data = {
            "user_id": test_user["user_id"],
            "items": [
                {
                    "product_id": "p001",
                    "name": "Item",
                    "price": 100.00,
                    "quantity": quantity
                }
            ],
        }

        response = sync_client.post(
            f"{FASTAPI_BASE_URL}/orders",
            json=order_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_201_CREATED


# ============================================================================
# TEST CLASS: Authentication and Authorization
# ============================================================================

@pytest.mark.crud
@pytest.mark.create
@pytest.mark.auth
class TestCreateOrderAuthentication:
    """Test authentication and authorization for order creation."""

    def test_create_order_without_authentication(
        self,
        sync_client: TestClient,
    ):
        """
        TEST: Creating order without authentication fails with 401.
        
        Verifies:
        - Authentication required
        - Unauthenticated requests rejected
        """
        order_data = {
            "user_id": "test_user",
            "items": [{"product_id": "p1", "name": "Item", "price": 100, "quantity": 1}],
        }

        response = sync_client.post(
            f"{FASTAPI_BASE_URL}/orders",
            json=order_data
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_order_with_invalid_token(
        self,
        sync_client: TestClient,
    ):
        """
        TEST: Creating order with invalid JWT token fails with 401.
        
        Verifies:
        - Invalid tokens rejected
        - API validates token format and signature
        """
        invalid_headers = {"Authorization": "Bearer invalid_token_here"}
        order_data = {
            "user_id": "test_user",
            "items": [{"product_id": "p1", "name": "Item", "price": 100, "quantity": 1}],
        }

        response = sync_client.post(
            f"{FASTAPI_BASE_URL}/orders",
            json=order_data,
            headers=invalid_headers
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_order_for_different_user_forbidden(
        self,
        sync_client: TestClient,
        auth_headers: Dict[str, str],
        test_user: Dict[str, Any],
    ):
        """
        TEST: Creating order for different user fails with 403 Forbidden.
        
        Verifies:
        - Authorization enforced
        - User cannot create orders for other users
        - API validates user_id matches authenticated user
        """
        order_data = {
            "user_id": "different_user_123",  # Different from authenticated user
            "items": [{"product_id": "p1", "name": "Item", "price": 100, "quantity": 1}],
        }

        response = sync_client.post(
            f"{FASTAPI_BASE_URL}/orders",
            json=order_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# TEST CLASS: Status Field Validation
# ============================================================================

@pytest.mark.crud
@pytest.mark.create
@pytest.mark.validation
class TestCreateOrderStatusValidation:
    """Test status field validation for new orders."""

    def test_create_order_with_pending_status(
        self,
        sync_client: TestClient,
        auth_headers: Dict[str, str],
        test_user: Dict[str, Any],
    ):
        """
        TEST: Creating order with 'Pending' status succeeds.
        
        Verifies:
        - 'Pending' is valid initial status
        - New orders start in Pending state
        """
        order_data = {
            "user_id": test_user["user_id"],
            "items": [{"product_id": "p1", "name": "Item", "price": 100, "quantity": 1}],
        }

        response = sync_client.post(
            f"{FASTAPI_BASE_URL}/orders",
            json=order_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["status"] == "Pending"

    def test_create_order_with_invalid_status(
        self,
        sync_client: TestClient,
        auth_headers: Dict[str, str],
        test_user: Dict[str, Any],
    ):
        """
        TEST: Creating order with invalid status fails with 422.
        
        Verifies:
        - Only valid statuses accepted
        - API rejects invalid status values
        """
        order_data = {
            "user_id": test_user["user_id"],
            "items": [{"product_id": "p1", "name": "Item", "price": 100, "quantity": 1}],
            "status": "InvalidStatus"
        }

        response = sync_client.post(
            f"{FASTAPI_BASE_URL}/orders",
            json=order_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.parametrize("invalid_status", ["Processing", "Shipped", "Delivered", "Cancelled"])
    def test_create_order_invalid_initial_statuses(
        self,
        sync_client: TestClient,
        auth_headers: Dict[str, str],
        test_user: Dict[str, Any],
        invalid_status: str,
    ):
        """
        TEST: Creating order with non-Pending status fails.
        
        Verifies:
        - Only 'Pending' allowed for new orders made by users (not admins)
        - Cannot create orders with other statuses
        
        Parameterized for multiple invalid statuses.
        """
        order_data = {
            "user_id": test_user["user_id"],
            "items": [{"product_id": "p1", "name": "Item", "price": 100, "quantity": 1}],
            "status": invalid_status
        }

        response = sync_client.post(
            f"{FASTAPI_BASE_URL}/orders",
            json=order_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# TEST CLASS: Edge Cases and Boundary Conditions
# ============================================================================

@pytest.mark.crud
@pytest.mark.create
@pytest.mark.validation
class TestCreateOrderEdgeCases:
    """Test edge cases and boundary conditions for order creation."""

    def test_create_order_with_special_characters_in_product_name(
        self,
        sync_client: TestClient,
        auth_headers: Dict[str, str],
        test_user: Dict[str, Any],
    ):
        """
        TEST: Order items can have special characters in name.
        
        Verifies:
        - API handles special characters
        - Names with punctuation, unicode, etc. accepted
        """
        order_data = {
            "user_id": test_user["user_id"],
            "items": [
                {
                    "product_id": "p001",
                    "name": "Laptop Pro™ 16\" (2024)",
                    "price": 2000.00,
                    "quantity": 1
                }
            ],
        }

        response = sync_client.post(
            f"{FASTAPI_BASE_URL}/orders",
            json=order_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert "Laptop Pro" in response.json()["items"][0]["name"]

    def test_create_order_with_decimal_precision(
        self,
        sync_client: TestClient,
        auth_headers: Dict[str, str],
        test_user: Dict[str, Any],
    ):
        """
        TEST: Order prices preserve decimal precision.
        
        Verifies:
        - API handles decimal values correctly
        - Precision not lost in calculations
        """
        order_data = {
            "user_id": test_user["user_id"],
            "items": [
                {
                    "product_id": "p001",
                    "name": "Item",
                    "price": 9.99,
                    "quantity": 3
                }
            ],
        }

        response = sync_client.post(
            f"{FASTAPI_BASE_URL}/orders",
            json=order_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["total_price"] == 29.97

    @pytest.mark.slow
    def test_create_order_with_very_large_quantity(
        self,
        sync_client: TestClient,
        auth_headers: Dict[str, str],
        test_user: Dict[str, Any],
    ):
        """
        TEST: Order with very large quantity.
        
        Marked as slow due to potential large response.
        """
        order_data = {
            "user_id": test_user["user_id"],
            "items": [
                {
                    "product_id": "p001",
                    "name": "Bulk Item",
                    "price": 10.00,
                    "quantity": 10000
                }
            ],
        }

        response = sync_client.post(
            f"{FASTAPI_BASE_URL}/orders",
            json=order_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_201_CREATED

    def test_create_order_invalid_order_id_format_in_response(
        self,
        sync_client: TestClient,
        auth_headers: Dict[str, str],
        test_user: Dict[str, Any],
    ):
        """
        TEST: Response contains valid order ID format.
        
        Verifies:
        - _id field present in response
        - _id is valid MongoDB ObjectId format (string representation)
        """
        order_data = {
            "user_id": test_user["user_id"],
            "items": [{"product_id": "p1", "name": "Item", "price": 100, "quantity": 1}],
        }

        response = sync_client.post(
            f"{FASTAPI_BASE_URL}/orders",
            json=order_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_201_CREATED
        order_id = response.json()["_id"]
        
        # Verify _id is a valid MongoDB ObjectId string (24 hex chars)
        assert isinstance(order_id, str)
        assert len(order_id) == 24
        assert all(c in "0123456789abcdef" for c in order_id)
