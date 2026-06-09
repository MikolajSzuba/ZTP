from datetime import datetime

from sqlalchemy.orm import Session

from app.cart.data.cart_repository import (
    add_order,
    add_order_item,
    clear_cart_items,
    get_or_create_cart,
)
from app.cart.model.cart_orm import CartORM
from app.cart.model.order_item_orm import OrderItemORM
from app.cart.model.order_orm import OrderORM
from app.cart.model.cart_schema import OrderResponse
from app.cart.service.cart_exceptions import CartValidationError
from app.cart.service.checkout_command import CheckoutCommand


def _generate_order_number(order_id: int) -> str:
    today = datetime.now().strftime("%Y%m%d")
    return f"ZAM-{today}-{order_id:06d}"


def _get_valid_cart(db: Session, operator_id: int) -> CartORM:
    cart = get_or_create_cart(db, operator_id)

    if not cart.items:
        raise CartValidationError("Nie mozna wykonac checkout dla pustego koszyka.")

    return cart


def _calculate_total_amount(cart: CartORM) -> float:
    return sum(float(item.product.price) * item.quantity for item in cart.items)


def _validate_stock_availability(cart: CartORM) -> None:
    for item in cart.items:
        if item.quantity > item.product.stock_quantity:
            raise CartValidationError(
                f"Brak wystarczajacego stanu magazynowego dla produktu '{item.product.name}'."
            )


def _create_order(
    db: Session,
    operator_id: int,
    total_amount: float,
) -> OrderORM:
    order = OrderORM(
        operator_id=operator_id,
        order_number="TEMP",
        status="PENDING",
        total_amount=total_amount,
    )

    order = add_order(db, order)

    order.order_number = _generate_order_number(order.id)
    db.add(order)
    db.commit()
    db.refresh(order)

    return order


def _create_order_items_and_decrease_stock(
    db: Session,
    order_id: int,
    cart: CartORM,
) -> None:
    for item in cart.items:
        product = item.product
        line_total = float(product.price) * item.quantity

        order_item = OrderItemORM(
            order_id=order_id,
            product_id=product.id,
            product_name=product.name,
            unit_price=float(product.price),
            quantity=item.quantity,
            line_total=line_total,
        )

        add_order_item(db, order_item)

        product.stock_quantity -= item.quantity
        db.add(product)
        db.commit()


def _build_order_response(order: OrderORM) -> OrderResponse:
    return OrderResponse(
        id=order.id,
        operator_id=order.operator_id,
        order_number=order.order_number,
        status=order.status,
        total_amount=float(order.total_amount),
        created_at=order.created_at,
        items=order.items,
    )


def handle_checkout(
    db: Session,
    command: CheckoutCommand,
) -> OrderResponse:
    cart = _get_valid_cart(db, command.operator_id)

    _validate_stock_availability(cart)

    total_amount = _calculate_total_amount(cart)

    order = _create_order(
        db=db,
        operator_id=command.operator_id,
        total_amount=total_amount,
    )

    _create_order_items_and_decrease_stock(
        db=db,
        order_id=order.id,
        cart=cart,
    )

    clear_cart_items(db, cart.id)

    return _build_order_response(order)
