from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional, Literal
from datetime import datetime, timezone
from bson import ObjectId

# DATE_SENTINEL = datetime(1970, 1, 1)


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
    status: str = Field(default="Pending", description="Initial status of the order")
    total_price: Optional[float] = Field(default=None, description="Auto-calculated from items")
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)
    
    @model_validator(mode='after')
    def postprocess(self):
        print('xxxxx', ' postprocessing from OrderCreate is being ran')
        self._calculate_total_price()
        self._set_timestamps()
        return self

    def _calculate_total_price(self):
        self.total_price = sum(item.price * item.quantity for item in self.items)
    
    def _set_timestamps(self):
        current_time: datetime = datetime.now(timezone.utc)
        if self.created_at is None:
            print('self.created_at is None and is being set to: ', current_time)
            self.created_at = current_time
        self.created_at = self.created_at.replace(tzinfo=timezone.utc) #  make sure timezone is UTC
        print('xxxxxxxxx', self.created_at, ' || ', current_time)
        if self.created_at > current_time:
            raise ValueError("Created at cannot be in the future")
        if self.updated_at is None:
            self.updated_at = current_time


class OrderUpdate(BaseModel):
    status: Optional[Literal["Pending", "Processing", "Shipped", "Delivered", "Cancelled"]] = None
    items: Optional[List[OrderItem]] = None
    total_price: Optional[float] = None
    updated_at: Optional[datetime] = None

    @model_validator(mode='after')
    def postprocess(self):
        print('xxxxx', ' postprocessing from OrderUpdate is being ran')
        self._update_total_price()
        self._set_update_time()
        return self
    
    def _update_total_price(self):
        if self.items is not None:
            self.total_price = sum(item.price * item.quantity for item in self.items)
    
    def _set_update_time(self):
        self.updated_at = datetime.now(timezone.utc)


class OrderResponse(OrderCreate):
    id: ObjectId = Field(alias="_id")
    
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