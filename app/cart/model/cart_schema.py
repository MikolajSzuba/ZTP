from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CartItemCreate(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0, strict=True)


class CartItemQuantityUpdate(BaseModel):
    quantity: int = Field(..., gt=0, strict=True)


class CartProductResponse(BaseModel):
    id: int
    name: str
    price: float
    stock_quantity: int

    model_config = ConfigDict(from_attributes=True)


class CartItemResponse(BaseModel):
    id: int
    quantity: int
    line_total: float
    created_at: datetime
    product: CartProductResponse

    model_config = ConfigDict(from_attributes=True)


class CartResponse(BaseModel):
    id: int
    operator_id: int
    items: list[CartItemResponse]
    items_count: int
    total_amount: float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    unit_price: float
    quantity: int
    line_total: float

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    id: int
    operator_id: int
    order_number: str
    status: str
    total_amount: float
    created_at: datetime
    items: list[OrderItemResponse]

    model_config = ConfigDict(from_attributes=True)


class OrderListItemResponse(BaseModel):
    id: int
    order_number: str
    status: str
    total_amount: float
    products_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LastOrderSummary(BaseModel):
    id: int
    order_number: str
    status: str
    total_amount: float
    products_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DashboardSummaryResponse(BaseModel):
    total_orders: int
    pending_orders: int
    completed_orders: int
    cancelled_orders: int
    last_order: LastOrderSummary | None = None
    recent_orders: list[OrderListItemResponse] = []
