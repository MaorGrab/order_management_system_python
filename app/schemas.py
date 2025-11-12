from pydantic import BaseModel, ConfigDict, Field
from bson import ObjectId
from typing import List
#from .models import PydanticObjectId
from datetime import datetime

INVALID_DATE = datetime(1970, 1, 1)

def time_to_str(time: datetime):
    return time.strftime("%Y-%m-%d %H:%M:%S").replace(' ', 'T') + 'Z'

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
    created_at: datetime = INVALID_DATE
    updated_at: datetime = INVALID_DATE

class OrderCreate(OrderBase):
    pass

class OrderResponse(OrderBase):
    id: ObjectId = Field(alias="_id")
    model_config = {                  
        "json_encoders": {
            ObjectId: str,
            datetime: time_to_str,
        },
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }
