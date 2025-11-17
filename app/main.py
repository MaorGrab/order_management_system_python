# app/application.py
import os
from bson import ObjectId
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import MongoDB
from app.models import OrderCreate, OrderResponse, OrderListResponse, OrderUpdate
from app.auth import User, get_current_user, get_current_admin_user


# Config defaults (consider switching to pydantic Settings in production)
DEFAULT_MONGO_URI = os.getenv("MONGODB_URL", "mongodb://root:root_password@localhost:27017/")
DEFAULT_DB_NAME  = os.getenv("MONGODB_DB_NAME", "oms_db")


class OMSApp:
    """
    Application factory for Order Management System.
    Use OMSApp.create_app() to get a FastAPI instance ready to run or test.
    """

    def __init__(self, mongo_uri: str = DEFAULT_MONGO_URI, db_name: str = DEFAULT_DB_NAME):
        self.mongo_uri = mongo_uri
        self.db_name = db_name

    def create_app(self) -> FastAPI:
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # create the MongoDB wrapper and store on app.state
            mongodb = MongoDB(self.mongo_uri, self.db_name)
            # Force client creation here (optional); Motor will lazily connect on first operation.
            _ = mongodb.client
            app.state.mongodb = mongodb
            app.state.db = mongodb.get_database()
            try:
                yield
            finally:
                # close client on shutdown
                mongodb.close()

        app = FastAPI(
            title="Order Management System API",
            version="1.0.0",
            description="API for managing orders in an e-commerce system",
            lifespan=lifespan,
        )

        # dependency to return the AsyncIOMotorDatabase stored on the app state
        def get_db(request: Request) -> AsyncIOMotorDatabase:
            """
            Small, fast DI function that returns the app-scoped database.
            Accessing request.app.state ensures we don't depend on module globals.
            """
            db = getattr(request.app.state, "db", None)
            if db is None:
                # defensive: if lifespan didn't run or state not set
                raise RuntimeError("Database not initialized")
            return db

        # simple health endpoint — uses get_db DI
        @app.get("/health")
        async def health_check(db: AsyncIOMotorDatabase = Depends(get_db)):
            try:
                await db.command("ping")
                return {"status": "healthy", "database": "connected"}
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Database connection failed: {str(e)}",
                )

        # root
        @app.get("/")
        async def root():
            return {"message": "Order Management System API", "status": "running"}

        @app.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
        async def create_order(
            order_data: OrderCreate,
            current_user: User = Depends(get_current_user),
            db: AsyncIOMotorDatabase = Depends(get_db)
        ):
            # Validate user_id matches authenticated user
            if order_data.user_id != current_user.user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot create order for another user"
                )
            
            # Create order document
            order_dict = order_data.model_dump()

            if current_user.role != "admin":
                if order_dict["status"] != "Pending":
                    # Non-admins can only create pending orders
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Only pending orders can be created by XXX-admin users"
                    )
            
            # Insert into MongoDB
            result = await db.orders.insert_one(order_dict)
            
            # Retrieve created order
            created_order = await db.orders.find_one({"_id": result.inserted_id})
            return created_order


        @app.get("/orders/{order_id}", response_model=OrderResponse)
        async def get_order(
            order_id: str,
            current_user: User = Depends(get_current_user),
            db: AsyncIOMotorDatabase = Depends(get_db)
        ):
            # Validate ObjectId
            if (not order_id) or (not ObjectId.is_valid(order_id)):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid order ID format"
                )
            obj_id = ObjectId(order_id)
            
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
            return order


        @app.get("/orders", response_model=OrderListResponse)
        async def list_orders(
            status: Optional[str] = None,
            page: int = 1,
            limit: int = 10,
            current_user: User = Depends(get_current_user),
            db: AsyncIOMotorDatabase = Depends(get_db)
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
            
            return OrderListResponse(
                orders=[OrderResponse(**order) for order in orders],
                total=total,
                page=page,
                limit=limit,
                total_pages=(total + limit - 1) // limit
            )


        @app.patch("/orders/{order_id}", response_model=OrderResponse)
        async def update_order(
            order_id: str,
            update_data: OrderUpdate,
            current_user: User = Depends(get_current_admin_user),  # Only admins can update
            db: AsyncIOMotorDatabase = Depends(get_db)
        ):
            # Validate ObjectId
            if not ObjectId.is_valid(order_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid order ID format"
                )
            obj_id = ObjectId(order_id)
            
            # Find order
            order = await db.orders.find_one({"_id": obj_id})
            
            if not order:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Order not found"
                )
            
            # Update order
            update_dict = update_data.model_dump(exclude_unset=True)
            
            await db.orders.update_one(
                {"_id": obj_id},
                {"$set": update_dict}
            )
            
            # Return updated order
            updated_order = await db.orders.find_one({"_id": obj_id})    
            return updated_order


        @app.delete("/orders/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
        async def delete_order(
            order_id: str,
            current_user: User = Depends(get_current_admin_user),  # Only admins can delete
            db: AsyncIOMotorDatabase = Depends(get_db)
        ):
            # Validate ObjectId
            if not ObjectId.is_valid(order_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid order ID format"
                )
            obj_id = ObjectId(order_id)
            
            # Delete order
            result = await db.orders.delete_one({"_id": obj_id})
            
            if result.deleted_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Order not found"
                )
            return None

        return app

    # convenience: create app in one call
    @classmethod
    def create(cls, mongo_uri: Optional[str] = None, db_name: Optional[str] = None) -> FastAPI:
        return cls(mongo_uri or DEFAULT_MONGO_URI, db_name or DEFAULT_DB_NAME).create_app()


# Create the app instance for uvicorn
app = OMSApp.create()
