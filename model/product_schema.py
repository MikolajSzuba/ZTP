from pydantic import BaseModel


class Category(BaseModel):
    id: int
    name: str
    
    class Config:
        from_attributes = True
        
        
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

    class Config:
        from_attributes = True

