from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Literal
from datetime import datetime
from bson import ObjectId


def time_to_str(time: datetime):
    return time.strftime("%Y-%m-%d %H:%M:%S").replace(' ', 'T') + 'Z'


class OrderItem(BaseModel):
    product_id: str
    name: str
    price: float = Field(gt=0, description="Price must be greater than 0")
    quantity: int = Field(gt=0, description="Quantity must be greater than 0")


class OrderCreate(BaseModel):
    user_id: str
    items: List[OrderItem] = Field(min_length=1, description="Order must have at least one item")
    total_price: float = Field(gt=0)
    status: str = Field(default="Pending", description="Initial status of the order")
    
    @field_validator('items')
    @classmethod
    def validate_items(cls, v):
        if not v:
            raise ValueError("Order must contain at least one item")
        return v


class OrderUpdate(BaseModel):
    status: Optional[Literal["Pending", "Processing", "Shipped", "Delivered", "Cancelled"]] = None


class OrderResponse(OrderCreate):
    id: ObjectId = Field(alias="_id")
    user_id: str
    items: List[OrderItem]
    total_price: float
    status: str
    created_at: datetime
    updated_at: datetime
    
    model_config = {                  
        "json_encoders": {
            ObjectId: str,
            datetime: time_to_str,
        },
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }


class OrderListResponse(BaseModel):
    orders: List[OrderResponse]
    total: int
    page: int
    limit: int
    total_pages: int