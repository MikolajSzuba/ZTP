from sqlalchemy.orm import Session

from app.cart.data.cart_repository import get_orders_by_operator_id
from app.cart.model.cart_schema import (
    DashboardSummaryResponse,
    LastOrderSummary,
    OrderListItemResponse,
)


def get_dashboard_summary(db: Session, operator_id: int) -> DashboardSummaryResponse:
    orders = get_orders_by_operator_id(db=db, operator_id=operator_id)

    total_orders = len(orders)
    pending_orders = len([order for order in orders if order.status == "PENDING"])
    completed_orders = len([order for order in orders if order.status == "COMPLETED"])
    cancelled_orders = len([order for order in orders if order.status == "CANCELLED"])

    last_order = None
    if orders:
        latest = orders[0]
        last_order = LastOrderSummary(
            id=latest.id,
            order_number=latest.order_number,
            status=latest.status,
            total_amount=float(latest.total_amount),
            products_count=len(latest.items),
            created_at=latest.created_at,
        )

    recent_orders = [
        OrderListItemResponse(
            id=order.id,
            order_number=order.order_number,
            status=order.status,
            total_amount=float(order.total_amount),
            products_count=len(order.items),
            created_at=order.created_at,
        )
        for order in orders[:5]
    ]

    return DashboardSummaryResponse(
        total_orders=total_orders,
        pending_orders=pending_orders,
        completed_orders=completed_orders,
        cancelled_orders=cancelled_orders,
        last_order=last_order,
        recent_orders=recent_orders,
    )
