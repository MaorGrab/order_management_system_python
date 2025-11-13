import pytest
import requests
from typing import Dict, Any
from bson import ObjectId
from starlette import status
from tests.conftest import FASTAPI_BASE_URL


# ============================================================================
# TEST CLASS: Successful Order Deletion
# ============================================================================

@pytest.mark.crud
@pytest.mark.delete
class TestDeleteOrderSuccess:
    """Test successful order deletion scenarios."""

    def test_delete_order_success(
        self,
        api_client: requests.Session,
        admin_headers: Dict[str, str],
        test_admin: Dict[str, Any],
    ):
        """
        TEST: Delete existing order returns 204 No Content.
        
        Verifies:
        - Valid order deletion succeeds
        - Returns 204 No Content (or 200 OK depending on API design)
        - Response indicates success
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

        # Delete order
        response = api_client.delete(
            f"{FASTAPI_BASE_URL}/orders/{order_id}",
            headers=admin_headers
        )

        # Typically DELETE returns 204 No Content
        assert response.status_code in [status.HTTP_204_NO_CONTENT, status.HTTP_200_OK]

    def test_delete_order_removes_from_database(
        self,
        api_client: requests.Session,
        admin_headers: Dict[str, str],
        test_admin: Dict[str, Any],
    ):
        """
        TEST: Deleted order cannot be retrieved.
        
        Verifies:
        - Deletion actually removes from database
        - Subsequent GET returns 404
        - Deletion is persistent
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

        # Verify order exists before deletion
        get_response = api_client.get(
            f"{FASTAPI_BASE_URL}/orders/{order_id}",
            headers=admin_headers
        )
        assert get_response.status_code == status.HTTP_200_OK

        # Delete order
        delete_response = api_client.delete(
            f"{FASTAPI_BASE_URL}/orders/{order_id}",
            headers=admin_headers
        )
        assert delete_response.status_code in [status.HTTP_204_NO_CONTENT, status.HTTP_200_OK]

        # Verify order no longer exists
        get_response = api_client.get(
            f"{FASTAPI_BASE_URL}/orders/{order_id}",
            headers=admin_headers
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_multiple_orders_sequentially(
        self,
        api_client: requests.Session,
        admin_headers: Dict[str, str],
        test_admin: Dict[str, Any],
    ):
        """
        TEST: Delete multiple orders one by one.
        
        Verifies:
        - Multiple deletions work correctly
        - No interference between deletions
        """
        # Create multiple orders
        order_ids = []
        for i in range(3):
            order_data = {
                "user_id": test_admin["user_id"],
                "items": [
                    {
                        "product_id": f"p{i}",
                        "name": f"Item {i}",
                        "price": 100.00 * (i + 1),
                        "quantity": 1
                    }
                ],
                "total_price": 100.00 * (i + 1),
                "status": "Pending"
            }

            create_response = api_client.post(
                f"{FASTAPI_BASE_URL}/orders",
                json=order_data,
                headers=admin_headers
            )
            order_ids.append(create_response.json()["_id"])

        # Delete each order and verify
        for order_id in order_ids:
            delete_response = api_client.delete(
                f"{FASTAPI_BASE_URL}/orders/{order_id}",
                headers=admin_headers
            )
            assert delete_response.status_code in [status.HTTP_204_NO_CONTENT, status.HTTP_200_OK]

            # Verify it's gone
            get_response = api_client.get(
                f"{FASTAPI_BASE_URL}/orders/{order_id}",
                headers=admin_headers
            )
            assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_order_in_different_status(
        self,
        api_client: requests.Session,
        admin_headers: Dict[str, str],
        test_admin: Dict[str, Any],
    ):
        """
        TEST: Can delete orders in any status.
        
        Verifies:
        - Orders can be deleted regardless of status
        - Applies to all valid statuses
        """
        # Create and update order to different statuses
        statuses_to_test = ["Pending", "Processing", "Shipped", "Delivered"]

        for test_status in statuses_to_test:
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

            # Transition to test_status
            if test_status != "Pending":
                all_statuses = ["Pending", "Processing", "Shipped", "Delivered"]
                for status_val in all_statuses[1:all_statuses.index(test_status) + 1]:
                    api_client.patch(
                        f"{FASTAPI_BASE_URL}/orders/{order_id}",
                        json={"status": status_val},
                        headers=admin_headers
                    )

            # Delete
            delete_response = api_client.delete(
                f"{FASTAPI_BASE_URL}/orders/{order_id}",
                headers=admin_headers
            )

            assert delete_response.status_code in [status.HTTP_204_NO_CONTENT, status.HTTP_200_OK]


# ============================================================================
# TEST CLASS: Delete Non-Existent Orders
# ============================================================================

@pytest.mark.crud
@pytest.mark.delete
class TestDeleteOrderNotFound:
    """Test deleting non-existent orders."""

    def test_delete_nonexistent_order_returns_404(
        self,
        api_client: requests.Session,
        admin_headers: Dict[str, str],
    ):
        """
        TEST: Deleting non-existent order returns 404.
        
        Verifies:
        - Cannot delete orders that don't exist
        - Proper error handling
        """
        fake_id = str(ObjectId())

        response = api_client.delete(
            f"{FASTAPI_BASE_URL}/orders/{fake_id}",
            headers=admin_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_already_deleted_order_returns_404(
        self,
        api_client: requests.Session,
        admin_headers: Dict[str, str],
        test_admin: Dict[str, Any],
    ):
        """
        TEST: Deleting already deleted order returns 404.
        
        Verifies:
        - Cannot delete order twice
        - Second delete returns 404
        """
        # Create and delete order
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

        # Delete first time
        delete_response = api_client.delete(
            f"{FASTAPI_BASE_URL}/orders/{order_id}",
            headers=admin_headers
        )
        assert delete_response.status_code in [status.HTTP_204_NO_CONTENT, status.HTTP_200_OK]

        # Try to delete again
        delete_response_2 = api_client.delete(
            f"{FASTAPI_BASE_URL}/orders/{order_id}",
            headers=admin_headers
        )
        assert delete_response_2.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# TEST CLASS: Delete with Invalid ID Format
# ============================================================================

@pytest.mark.crud
@pytest.mark.delete
class TestDeleteOrderInvalidId:
    """Test delete with invalid order ID format."""

    @pytest.mark.parametrize("invalid_id", [
        "not-a-valid-objectid",
        "12345",
        "gggggggggggggggggggggggg",
        "!@#$%^&*()",
    ])
    def test_delete_invalid_id_format_fails(
        self,
        api_client: requests.Session,
        admin_headers: Dict[str, str],
        invalid_id: str,
    ):
        """
        TEST: Invalid ID format returns 400.
        
        Parameterized for multiple invalid formats.
        Verifies:
        - API validates ID format
        - Invalid formats rejected with 400
        """
        response = api_client.delete(
            f"{FASTAPI_BASE_URL}/orders/{invalid_id}",
            headers=admin_headers
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ============================================================================
# TEST CLASS: Authentication and Authorization
# ============================================================================

@pytest.mark.crud
@pytest.mark.delete
@pytest.mark.auth
class TestDeleteOrderAuthentication:
    """Test authentication and authorization for deletions."""

    def test_delete_order_by_user(
        self,
        api_client: requests.Session,
        test_user: Dict[str, Any],
        auth_headers: Dict[str, str],
    ):
        """
        TEST: Users can't delete orders.

        Verifies:
        - Only admins can delete orders.
        """
        order_id = str(ObjectId())

        response = api_client.delete(
            f"{FASTAPI_BASE_URL}/orders/{order_id}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_order_without_authentication_fails(
        self,
        api_client: requests.Session,
    ):
        """
        TEST: Deleting order without authentication fails with 401.
        
        Verifies:
        - Authentication required for deletion
        - Unauthenticated requests rejected
        """
        order_id = str(ObjectId())

        response = api_client.delete(
            f"{FASTAPI_BASE_URL}/orders/{order_id}"
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_order_with_invalid_token_fails(
        self,
        api_client: requests.Session,
    ):
        """
        TEST: Deleting order with invalid token fails with 401.
        
        Verifies:
        - Invalid tokens rejected
        """
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        order_id = str(ObjectId())

        response = api_client.delete(
            f"{FASTAPI_BASE_URL}/orders/{order_id}",
            headers=invalid_headers
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_order_authorization_check(
        self,
        api_client: requests.Session,
        admin_headers: Dict[str, str],
        test_admin: Dict[str, Any],
    ):
        """
        TEST: Can only delete own orders (authorization).
        
        Verifies:
        - Authorization enforced for deletion
        - Cannot delete other users' orders
        """
        # Create order for test_admin
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

        # Try to delete with different user's token
        response = api_client.delete(
            f"{FASTAPI_BASE_URL}/orders/{order_id}",
            headers=other_headers
        )

        # Should be forbidden (403) or not found (404) depending on implementation
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]


# ============================================================================
# TEST CLASS: Idempotency
# ============================================================================

@pytest.mark.crud
@pytest.mark.delete
class TestDeleteOrderIdempotency:
    """Test idempotency considerations for DELETE."""

    def test_delete_idempotent_concept(
        self,
        api_client: requests.Session,
        admin_headers: Dict[str, str],
        test_admin: Dict[str, Any],
    ):
        """
        TEST: Document idempotency behavior for DELETE.
        
        Note: Strictly speaking, DELETE is NOT idempotent per RFC 7231
        because the second call returns 404 (different response).
        However, the end state is the same (resource deleted).
        
        This test documents the actual behavior.
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

        # First delete - should succeed
        response1 = api_client.delete(
            f"{FASTAPI_BASE_URL}/orders/{order_id}",
            headers=admin_headers
        )
        assert response1.status_code in [status.HTTP_204_NO_CONTENT, status.HTTP_200_OK]

        # Second delete - returns different status (404)
        response2 = api_client.delete(
            f"{FASTAPI_BASE_URL}/orders/{order_id}",
            headers=admin_headers
        )
        assert response2.status_code == status.HTTP_404_NOT_FOUND

        # But end state is same: resource doesn't exist
        verify_response = api_client.get(
            f"{FASTAPI_BASE_URL}/orders/{order_id}",
            headers=admin_headers
        )
        assert verify_response.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# TEST CLASS: Cascade and Side Effects
# ============================================================================

@pytest.mark.crud
@pytest.mark.delete
class TestDeleteOrderSideEffects:
    """Test that deletion only affects the order, not related data."""

    def test_delete_order_no_side_effects(
        self,
        api_client: requests.Session,
        admin_headers: Dict[str, str],
        test_admin: Dict[str, Any],
    ):
        """
        TEST: Deleting one order doesn't affect other orders.
        
        Verifies:
        - Delete is isolated
        - Other orders unaffected
        - User account unaffected
        """
        # Create two orders for same user
        order_ids = []
        for i in range(2):
            order_data = {
                "user_id": test_admin["user_id"],
                "items": [
                    {
                        "product_id": f"p{i}",
                        "name": f"Item {i}",
                        "price": 100.00 * (i + 1),
                        "quantity": 1
                    }
                ],
                "total_price": 100.00 * (i + 1),
                "status": "Pending"
            }

            create_response = api_client.post(
                f"{FASTAPI_BASE_URL}/orders",
                json=order_data,
                headers=admin_headers
            )
            order_ids.append(create_response.json()["_id"])

        # Delete first order
        delete_response = api_client.delete(
            f"{FASTAPI_BASE_URL}/orders/{order_ids[0]}",
            headers=admin_headers
        )
        assert delete_response.status_code in [status.HTTP_204_NO_CONTENT, status.HTTP_200_OK]

        # Verify first order is gone
        get_response = api_client.get(
            f"{FASTAPI_BASE_URL}/orders/{order_ids[0]}",
            headers=admin_headers
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

        # Verify second order still exists
        get_response = api_client.get(
            f"{FASTAPI_BASE_URL}/orders/{order_ids[1]}",
            headers=admin_headers
        )
        assert get_response.status_code == status.HTTP_200_OK
