from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Literal
from datetime import datetime
from bson import ObjectId


class OrderItem(BaseModel):
    product_id: str
    name: str
    price: float = Field(gt=0, description="Price must be greater than 0")
    quantity: int = Field(gt=0, description="Quantity must be greater than 0")


class OrderCreate(BaseModel):
    user_id: str
    items: List[OrderItem] = Field(min_length=1, description="Order must have at least one item")
    total_price: float = Field(gt=0)
    
    @field_validator('items')
    @classmethod
    def validate_items(cls, v):
        if not v:
            raise ValueError("Order must contain at least one item")
        return v


class OrderUpdate(BaseModel):
    status: Optional[Literal["Pending", "Processing", "Shipped", "Delivered", "Cancelled"]] = None


class OrderResponse(BaseModel):
    id: str
    user_id: str
    items: List[OrderItem]
    total_price: float
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        json_encoders = {
            ObjectId: str
        }


class OrderListResponse(BaseModel):
    orders: List[OrderResponse]
    total: int
    page: int
    limit: int
    total_pages: int