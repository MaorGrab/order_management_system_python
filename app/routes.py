from fastapi import APIRouter, HTTPException
from bson import ObjectId
from .database import orders_collection
from .schemas import OrderCreate, OrderResponse

router = APIRouter()


@router.post("/orders", response_model=OrderResponse)
def create_order(order: OrderCreate):
    # Use model_dump to get dict of the model
    order_dict = order.model_dump()
    # Ensure status field is set if missing
    order_dict["status"] = order_dict.get("status", "Pending")
    # Insert into MongoDB
    result = orders_collection.insert_one(order_dict)
    # Convert _id to string for response
    order_dict["_id"] = result.inserted_id
    print("hehe", order_dict["_id"])
    return order_dict


@router.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: str):
    try:
        oid = ObjectId(order_id)
    except:
        raise HTTPException(400, "Invalid order ID")

    order = orders_collection.find_one({"_id": oid})
    if not order:
        raise HTTPException(404, "Order not found")

    return order


@router.patch("/orders/{order_id}", response_model=OrderResponse)
def update_order(order_id: str, update_data: dict):
    try:
        oid = ObjectId(order_id)
    except:
        raise HTTPException(400, "Invalid order ID")

    result = orders_collection.update_one({"_id": oid}, {"$set": update_data})

    if result.matched_count == 0:
        raise HTTPException(404, "Order not found")

    updated = orders_collection.find_one({"_id": oid})
    return updated


@router.delete("/orders/{order_id}")
def delete_order(order_id: str):
    try:
        oid = ObjectId(order_id)
    except:
        raise HTTPException(400, "Invalid order ID")

    result = orders_collection.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(404, "Order not found")

    return {"deleted": True}
