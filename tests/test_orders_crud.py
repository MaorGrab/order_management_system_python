import requests
from bson import ObjectId
from datetime import datetime

BASE = "http://localhost:8000"


def test_create_order_success(sample_order, api_headers):
    res = requests.post(f"{BASE}/orders", json=sample_order, headers=api_headers)
    assert res.status_code == 200
    data = res.json()
    assert "_id" in data
    assert data["status"] == "Pending"
    assert data["updated_at"] == data["created_at"]


def test_get_order(orders_collection, sample_order):
    inserted_id = orders_collection.insert_one(sample_order).inserted_id
    inserted_id_str = str(inserted_id)
    res = requests.get(f"{BASE}/orders/{inserted_id_str}")
    assert res.status_code == 200
    data = res.json()
    assert data["user_id"] == sample_order["user_id"]
    assert data["updated_at"] >= data["created_at"]


def test_update_order(orders_collection, sample_order):
    inserted_id = orders_collection.insert_one(sample_order).inserted_id

    res = requests.patch(f"{BASE}/orders/{inserted_id}", json={"status": "Processing"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "Processing"
    assert data["updated_at"] > data["created_at"]


def test_delete_order(orders_collection, sample_order):
    inserted_id = orders_collection.insert_one(sample_order).inserted_id

    res = requests.delete(f"{BASE}/orders/{inserted_id}")
    assert res.status_code == 200

    assert orders_collection.find_one({"_id": inserted_id}) is None
