from pydantic import BaseModel, ConfigDict, Field
from bson import ObjectId
from typing import List
#from .models import PydanticObjectId
from datetime import datetime

class Item(BaseModel):
    product_id: str
    name: str
    price: float
    quantity: int

class OrderBase(BaseModel):
    user_id: str
    items: List[Item]
    total_price: float
    status: str = "Pending"
    # created_at: datetime
    # updated_at: datetime

class OrderCreate(OrderBase):
    pass

class OrderResponse(OrderBase):
    id: ObjectId = Field(alias="_id")
    model_config = {                  
        "json_encoders": {ObjectId: str},
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }
