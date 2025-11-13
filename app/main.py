from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from typing import List, Optional
from datetime import datetime, timezone

from app.database import get_database
from app.models import OrderCreate, OrderUpdate, OrderResponse, OrderListResponse
from app.auth import get_current_user, get_current_admin_user, User
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

app = FastAPI(
    title="Order Management System API",
    version="1.0.0",
    description="API for managing orders in an e-commerce system"
)


@app.get("/")
async def root():
    return {"message": "Order Management System API", "status": "running"}


@app.get("/health")
async def health_check(db: AsyncIOMotorDatabase = Depends(get_database)):
    try:
        # Ping MongoDB
        await db.command("ping")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {str(e)}"
        )


@app.post("/api/v1/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    # Validate user_id matches authenticated user
    if order_data.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create order for another user"
        )
    
    # Create order document
    order_dict = order_data.model_dump()
    order_dict["created_at"] = datetime.now(timezone.utc)
    order_dict["updated_at"] = datetime.now(timezone.utc)
    order_dict["status"] = "Pending"
    
    # Insert into MongoDB
    result = await db.orders.insert_one(order_dict)
    
    # Retrieve created order
    created_order = await db.orders.find_one({"_id": result.inserted_id})
    created_order["id"] = str(created_order["_id"])
    
    return OrderResponse(**created_order)


@app.get("/api/v1/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    # Validate ObjectId
    try:
        obj_id = ObjectId(order_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid order ID format"
        )
    
    # Find order
    order = await db.orders.find_one({"_id": obj_id})
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Check authorization (users can only see their own orders, admins can see all)
    if current_user.role != "admin" and order["user_id"] != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this order"
        )
    
    order["id"] = str(order["_id"])
    return OrderResponse(**order)


@app.get("/api/v1/orders", response_model=OrderListResponse)
async def list_orders(
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    # Build query
    query = {}
    
    # Regular users only see their orders
    if current_user.role != "admin":
        query["user_id"] = current_user.user_id
    
    # Filter by status if provided
    if status:
        query["status"] = status
    
    # Calculate pagination
    skip = (page - 1) * limit
    
    # Get total count
    total = await db.orders.count_documents(query)
    
    # Fetch orders
    cursor = db.orders.find(query).skip(skip).limit(limit).sort("created_at", -1)
    orders = await cursor.to_list(length=limit)
    
    # Convert ObjectId to string
    for order in orders:
        order["id"] = str(order["_id"])
    
    return OrderListResponse(
        orders=[OrderResponse(**order) for order in orders],
        total=total,
        page=page,
        limit=limit,
        total_pages=(total + limit - 1) // limit
    )


@app.patch("/api/v1/orders/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: str,
    update_data: OrderUpdate,
    current_user: User = Depends(get_current_admin_user),  # Only admins can update
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    # Validate ObjectId
    try:
        obj_id = ObjectId(order_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid order ID format"
        )
    
    # Find order
    order = await db.orders.find_one({"_id": obj_id})
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Update order
    update_dict = update_data.model_dump(exclude_unset=True)
    update_dict["updated_at"] = datetime.now(timezone.utc)
    
    await db.orders.update_one(
        {"_id": obj_id},
        {"$set": update_dict}
    )
    
    # Return updated order
    updated_order = await db.orders.find_one({"_id": obj_id})
    updated_order["id"] = str(updated_order["_id"])
    
    return OrderResponse(**updated_order)


@app.delete("/api/v1/orders/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(
    order_id: str,
    current_user: User = Depends(get_current_admin_user),  # Only admins can delete
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    # Validate ObjectId
    try:
        obj_id = ObjectId(order_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid order ID format"
        )
    
    # Delete order
    result = await db.orders.delete_one({"_id": obj_id})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return None