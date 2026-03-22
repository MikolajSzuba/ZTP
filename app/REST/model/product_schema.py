from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Any


class Category(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)
        
        
class ProductCreate(BaseModel):
    name:str
    category_id: int
    price:float
        
class ProductUpdate(BaseModel):
    name:str | None=None
    category_id: int | None=None
    price:float | None=None
        
class Product(BaseModel):
    id: int
    name: str
    category: Category
    price: float

    model_config = ConfigDict(from_attributes=True)


class ProductHistoryEntry(BaseModel):
    id: int
    product_id: int
    action: str
    previous_state: dict[str, Any]
    current_state: dict[str, Any]
    changed_at: datetime

    model_config = ConfigDict(from_attributes=True)

