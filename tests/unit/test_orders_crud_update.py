
import pytest
import requests
from time import sleep
from typing import Dict, Any
from bson import ObjectId
from starlette import status
from tests.conftest import FASTAPI_BASE_URL


# ============================================================================
# TEST CLASS: Valid Status Transitions
# ============================================================================

@pytest.mark.crud
@pytest.mark.update
class TestUpdateOrderSuccess:
    """Test successful order status updates."""

    def test_update_order_status_pending_to_processing(
        self,
        api_client: requests.Session,
        admin_headers: Dict[str, str],
        test_admin: Dict[str, Any],
    ):
        """
        TEST: Update order from Pending to Processing succeeds.
        
        Verifies:
        - Valid status transition accepted (Pending → Processing)
        - Returns 200 OK
        - Response contains updated status
        - Timestamp (updated_at) refreshed
        """
        # Create order
        order_data = {
            "user_id": test_admin["user_id"],
            "items": [{"product_id": "p1", "name": "Item", "price": 100, "quantity": 1}],
            "total_price": 100.00,
            "status": "Pending"
        }

        create_response = api_client.post(
            f"{FASTAPI_BASE_URL}/orders",
            json=order_data,
            headers=admin_headers
        )
        order_id = create_response.json()["_id"]
        original_updated_at = create_response.json()["updated_at"]
        sleep(1)
        # Update status
        update_data = {"status": "Processing"}
        response = api_client.patch(
            f"{FASTAPI_BASE_URL}/orders/{order_id}",
            json=update_data,
            headers=admin_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "Processing"
        assert data["updated_at"] != original_updated_at  # Timestamp changed

    def test_update_order_status_processing_to_shipped(
        self,
        api_client: requests.Session,
        admin_headers: Dict[str, str],
        test_admin: Dict[str, Any],
    ):
        """
        TEST: Update order from Processing to Shipped succeeds.
        
        Valid transition: Processing → Shipped
        """
        # Create and update to Processing first
        order_data = {
            "user_id": test_admin["user_id"],
            "items": [{"product_id": "p1", "name": "Item", "price": 100, "quantity": 1}],
            "total_price": 100.00,
            "status": "Pending"
        }

        create_response = api_client.post(
            f"{FASTAPI_BASE_URL}/orders",
            json=order_data,
            headers=admin_headers
        )
        order_id = create_response.json()["_id"]

        # Update to Processing
        api_client.patch(
            f"{FASTAPI_BASE_URL}/orders/{order_id}",
            json={"status": "Processing"},
            headers=admin_headers
        )

        # Update to Shipped
        response = api_client.patch(
            f"{FASTAPI_BASE_URL}/orders/{order_id}",
            json={"status": "Shipped"},
            headers=admin_headers
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "Shipped"

    def test_update_order_status_shipped_to_delivered(
        self,
        api_client: requests.Session,
        admin_headers: Dict[str, str],
        test_admin: Dict[str, Any],
    ):
        """
        TEST: Update order from Shipped to Delivered succeeds.
        
        Valid transition: Shipped → Delivered
        """
        # Create order and transition through statuses
        order_data = {
            "user_id": test_admin["user_id"],
            "items": [{"product_id": "p1", "name": "Item", "price": 100, "quantity": 1}],
            "total_price": 100.00,
            "status": "Pending"
        }

        create_response = api_client.post(
            f"{FASTAPI_BASE_URL}/orders",
            json=order_data,
            headers=admin_headers
        )
        order_id = create_response.json()["_id"]

        # Transition through statuses
        for status_value in ["Processing", "Shipped"]:
            api_client.patch(
                f"{FASTAPI_BASE_URL}/orders/{order_id}",
                json={"status": status_value},
                headers=admin_headers
            )

        # Update to Delivered
        response = api_client.patch(
            f"{FASTAPI_BASE_URL}/orders/{order_id}",
            json={"status": "Delivered"},
            headers=admin_headers
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "Delivered"

    @pytest.mark.parametrize("transitions", [
        ("Pending", "Processing"),
        ("Processing", "Shipped"),
        ("Shipped", "Delivered"),
    ])
    def test_update_order_valid_transitions(
        self,
        api_client: requests.Session,
        admin_headers: Dict[str, str],
        test_admin: Dict[str, Any],
        transitions: tuple,
    ):
        """
        TEST: All valid status transitions work correctly.
        
        Parameterized test for all valid transitions.
        """
        from_status, to_status = transitions

        # Create order at initial status
        order_data = {
            "user_id": test_admin["user_id"],
            "items": [{"product_id": "p1", "name": "Item", "price": 100, "quantity": 1}],
            "total_price": 100.00,
            "status": from_status
        }

        # If not Pending, need to transition first
        if from_status != "Pending":
            create_response = api_client.post(
                f"{FASTAPI_BASE_URL}/orders",
                json={"user_id": test_admin["user_id"], "items": order_data["items"],
                      "total_price": 100.00, "status": "Pending"},
                headers=admin_headers
            )
            order_id = create_response.json()["_id"]

            # Transition to from_status
            all_statuses = ["Pending", "Processing", "Shipped", "Delivered"]
            for status_val in all_statuses[1:all_statuses.index(from_status) + 1]:
                api_client.patch(
                    f"{FASTAPI_BASE_URL}/orders/{order_id}",
                    json={"status": status_val},
                    headers=admin_headers
                )
        else:
            create_response = api_client.post(
                f"{FASTAPI_BASE_URL}/orders",
                json=order_data,
                headers=admin_headers
            )
            order_id = create_response.json()["_id"]

        # Now test the transition
        response = api_client.patch(
            f"{FASTAPI_BASE_URL}/orders/{order_id}",
            json={"status": to_status},
            headers=admin_headers
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == to_status


# ============================================================================
# TEST CLASS: Invalid Status Transitions
# ============================================================================

@pytest.mark.crud
@pytest.mark.update
class TestUpdateOrderInvalidTransitions:
    """Test invalid status transitions are rejected."""
    def test_update_order_invalid_status_value(
        self,
        api_client: requests.Session,
        admin_headers: Dict[str, str],
        test_admin: Dict[str, Any],
    ):
        """
        TEST: Invalid status value rejected with 422.
        
        From test_edge_cases.py - validates status field.
        """
        # Create order
        order_data = {
            "user_id": test_admin["user_id"],
            "items": [{"product_id": "p1", "name": "Item", "price": 100, "quantity": 1}],
            "total_price": 100.00,
            "status": "Pending"
        }

        create_response = api_client.post(
            f"{FASTAPI_BASE_URL}/orders",
            json=order_data,
            headers=admin_headers
        )
        order_id = create_response.json()["_id"]

        # Try invalid status value
        response = api_client.patch(
            f"{FASTAPI_BASE_URL}/orders/{order_id}",
            json={"status": "InvalidStatus"},
            headers=admin_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================================================
# TEST CLASS: Update Non-Existent Orders
# ============================================================================

@pytest.mark.crud
@pytest.mark.update
class TestUpdateOrderNotFound:
    """Test updating non-existent orders."""

    def test_update_nonexistent_order_returns_404(
        self,
        api_client: requests.Session,
        admin_headers: Dict[str, str],
    ):
        """
        TEST: Updating non-existent order returns 404.
        
        Verifies:
        - Cannot update orders that don't exist
        - Proper error handling
        """
        fake_id = str(ObjectId())

        response = api_client.patch(
            f"{FASTAPI_BASE_URL}/orders/{fake_id}",
            json={"status": "Processing"},
            headers=admin_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# TEST CLASS: Update with Invalid ID Format
# ============================================================================

@pytest.mark.crud
@pytest.mark.update
class TestUpdateOrderInvalidId:
    """Test update with invalid order ID format."""

    @pytest.mark.parametrize("invalid_id", [
        "not-a-valid-objectid",
        "12345",
        "gggggggggggggggggggggggg",
    ])
    def test_update_invalid_id_format_fails(
        self,
        api_client: requests.Session,
        admin_headers: Dict[str, str],
        invalid_id: str,
    ):
        """
        TEST: Invalid ID format returns 400.
        
        Parameterized for multiple invalid formats.
        """
        response = api_client.patch(
            f"{FASTAPI_BASE_URL}/orders/{invalid_id}",
            json={"status": "Processing"},
            headers=admin_headers
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ============================================================================
# TEST CLASS: Authentication and Authorization
# ============================================================================

@pytest.mark.crud
@pytest.mark.update
@pytest.mark.auth
class TestUpdateOrderAuthentication:
    """Test authentication and authorization for updates."""

    def test_update_order_without_authentication_fails(
        self,
        api_client: requests.Session,
    ):
        """
        TEST: Updating order without authentication fails with 401.
        """
        order_id = str(ObjectId())

        response = api_client.patch(
            f"{FASTAPI_BASE_URL}/orders/{order_id}",
            json={"status": "Processing"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_order_with_invalid_token_fails(
        self,
        api_client: requests.Session,
    ):
        """
        TEST: Updating order with invalid token fails with 401.
        """
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        order_id = str(ObjectId())

        response = api_client.patch(
            f"{FASTAPI_BASE_URL}/orders/{order_id}",
            json={"status": "Processing"},
            headers=invalid_headers
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_order_by_user(
        self,
        api_client: requests.Session,
        auth_headers: Dict[str, str],
        test_user: Dict[str, Any],
    ):
        """
        TEST: Updating order by user fails with 403.
        """
        order_id = str(ObjectId())

        response = api_client.patch(
            f"{FASTAPI_BASE_URL}/orders/{order_id}",
            json={"status": "Processing"},
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# TEST CLASS: Update Verification
# ============================================================================

@pytest.mark.crud
@pytest.mark.update
class TestUpdateOrderVerification:
    """Test that updates are properly persisted."""

    def test_update_persists_to_database(
        self,
        api_client: requests.Session,
        admin_headers: Dict[str, str],
        test_admin: Dict[str, Any],
    ):
        """
        TEST: Updated status is persisted to database.
        
        Verifies:
        - Update not just in response
        - Read after update returns updated value
        """
        # Create order
        order_data = {
            "user_id": test_admin["user_id"],
            "items": [{"product_id": "p1", "name": "Item", "price": 100, "quantity": 1}],
            "total_price": 100.00,
            "status": "Pending"
        }

        create_response = api_client.post(
            f"{FASTAPI_BASE_URL}/orders",
            json=order_data,
            headers=admin_headers
        )
        order_id = create_response.json()["_id"]

        # Update status
        update_response = api_client.patch(
            f"{FASTAPI_BASE_URL}/orders/{order_id}",
            json={"status": "Processing"},
            headers=admin_headers
        )
        assert update_response.status_code == status.HTTP_200_OK

        # Read to verify persistence
        read_response = api_client.get(
            f"{FASTAPI_BASE_URL}/orders/{order_id}",
            headers=admin_headers
        )

        assert read_response.status_code == status.HTTP_200_OK
        assert read_response.json()["status"] == "Processing"

    def test_update_other_fields_unchanged(
        self,
        api_client: requests.Session,
        admin_headers: Dict[str, str],
        test_admin: Dict[str, Any],
    ):
        """
        TEST: Update only changes status, other fields unchanged.
        
        Verifies:
        - Only status updated
        - user_id, items, total_price unchanged
        - created_at unchanged
        """
        # Create order
        order_data = {
            "user_id": test_admin["user_id"],
            "items": [
                {"product_id": "p1", "name": "Item", "price": 100, "quantity": 1},
                {"product_id": "p2", "name": "Item2", "price": 50, "quantity": 2}
            ],
            "total_price": 200.00,
            "status": "Pending"
        }

        create_response = api_client.post(
            f"{FASTAPI_BASE_URL}/orders",
            json=order_data,
            headers=admin_headers
        )
        created_data = create_response.json()
        order_id = created_data["_id"]

        sleep(1)
        # Update status
        api_client.patch(
            f"{FASTAPI_BASE_URL}/orders/{order_id}",
            json={"status": "Processing"},
            headers=admin_headers
        )

        # Read and verify
        read_response = api_client.get(
            f"{FASTAPI_BASE_URL}/orders/{order_id}",
            headers=admin_headers
        )
        updated_data = read_response.json()

        # Verify unchanged fields
        assert updated_data["user_id"] == created_data["user_id"]
        assert len(updated_data["items"]) == 2
        assert updated_data["total_price"] == 200.00
        assert updated_data["created_at"] == created_data["created_at"]
        
        # Verify changed fields
        assert updated_data["status"] == "Processing"
        assert updated_data["updated_at"] != created_data["updated_at"]
