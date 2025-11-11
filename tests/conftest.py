import pytest
from pymongo import MongoClient
from datetime import datetime

MONGO_URI = "mongodb://root:root_password@localhost:27017/?authSource=admin"
DB_NAME = "oms_test_db"


@pytest.fixture(scope="session")
def mongo():
    client = MongoClient(MONGO_URI)
    yield client
    client.close()


@pytest.fixture(scope="function")
def orders_collection(mongo):
    db = mongo[DB_NAME]
    col = db["orders"]
    yield col
    db.drop_collection("orders")


@pytest.fixture(scope="function")
def sample_order():
    return {
        "user_id": "test_user_001",
        "items": [
            {"product_id": "p001", "name": "Laptop", "price": 1200.0, "quantity": 1},
            {"product_id": "p002", "name": "Mouse", "price": 25.0, "quantity": 2},
        ],
        "total_price": 1250.0,
        "status": "Pending",
    }


@pytest.fixture(scope="function")
def api_headers():
    return {"Content-Type": "application/json"}
