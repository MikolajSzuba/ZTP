from datetime import datetime

from sqlalchemy.orm import Session

from app.REST.data.product_repository import get_product_by_id
from app.cart.data.cart_repository import (
    add_cart_item,
    delete_cart_item,
    get_cart_item_by_cart_and_product,
    get_cart_item_by_id,
    get_or_create_cart,
    get_order_by_id_and_operator_id,
    get_orders_by_operator_id,
    save_cart_item,
)
from app.cart.model.cart_orm import CartORM
from app.cart.model.cart_schema import (
    CartItemCreate,
    CartItemQuantityUpdate,
    CartItemResponse,
    CartResponse,
    OrderListItemResponse,
    OrderResponse,
)
from app.cart.service.cart_exceptions import (
    CartConflictError,
    CartNotFoundError,
    CartValidationError,
)


def _calculate_total_amount(cart: CartORM) -> float:
    total = 0.0
    for item in cart.items:
        if item.product is not None:
            total += float(item.product.price) * item.quantity
    return total


def _build_cart_item_response(item) -> CartItemResponse:
    return CartItemResponse(
        id=item.id,
        quantity=item.quantity,
        line_total=float(item.product.price) * item.quantity,
        created_at=item.created_at,
        product=item.product,
    )


def _build_cart_response(cart: CartORM) -> CartResponse:
    return CartResponse(
        id=cart.id,
        operator_id=cart.operator_id,
        items=[_build_cart_item_response(item) for item in cart.items],
        items_count=len(cart.items),
        total_amount=_calculate_total_amount(cart),
        created_at=cart.created_at,
        updated_at=cart.updated_at,
    )


def _validate_requested_quantity(quantity: int, available_quantity: int) -> None:
    if quantity <= 0:
        raise CartValidationError("Ilosc produktu musi byc dodatnia.")

    if quantity > available_quantity:
        raise CartValidationError(
            "Nie mozna dodac wiekszej ilosci produktu niz dostepna w magazynie."
        )


def get_current_cart(
    db: Session,
    operator_id: int,
) -> CartResponse:
    cart = get_or_create_cart(db, operator_id)
    return _build_cart_response(cart)


def add_product_to_cart(
    db: Session,
    operator_id: int,
    payload: CartItemCreate,
) -> CartResponse:
    cart = get_or_create_cart(db, operator_id)

    product = get_product_by_id(db, payload.product_id)
    if product is None:
        raise CartNotFoundError("Produkt o podanym identyfikatorze nie istnieje.")

    _validate_requested_quantity(payload.quantity, product.stock_quantity)

    existing_item = get_cart_item_by_cart_and_product(
        db=db,
        cart_id=cart.id,
        product_id=payload.product_id,
    )
    if existing_item is not None:
        raise CartConflictError("Ten produkt jest juz dodany do koszyka.")

    add_cart_item(
        db=db,
        cart_id=cart.id,
        product_id=payload.product_id,
        quantity=payload.quantity,
    )

    cart.updated_at = datetime.now()
    db.add(cart)
    db.commit()
    db.refresh(cart)

    refreshed_cart = get_or_create_cart(db, operator_id)
    return _build_cart_response(refreshed_cart)


def update_cart_item_quantity(
    db: Session,
    operator_id: int,
    item_id: int,
    payload: CartItemQuantityUpdate,
) -> CartResponse:
    cart = get_or_create_cart(db, operator_id)

    item = get_cart_item_by_id(db, item_id)
    if item is None:
        raise CartNotFoundError("Pozycja koszyka nie istnieje.")

    if item.cart_id != cart.id:
        raise CartNotFoundError("Pozycja nie nalezy do koszyka aktualnego operatora.")

    product = item.product
    if product is None:
        raise CartNotFoundError("Produkt przypisany do pozycji koszyka nie istnieje.")

    _validate_requested_quantity(payload.quantity, product.stock_quantity)

    item.quantity = payload.quantity
    save_cart_item(db, item)

    cart.updated_at = datetime.now()
    db.add(cart)
    db.commit()
    db.refresh(cart)

    refreshed_cart = get_or_create_cart(db, operator_id)
    return _build_cart_response(refreshed_cart)


def remove_product_from_cart(
    db: Session,
    operator_id: int,
    item_id: int,
) -> bool:
    cart = get_or_create_cart(db, operator_id)

    item = get_cart_item_by_id(db, item_id)
    if item is None:
        raise CartNotFoundError("Pozycja koszyka nie istnieje.")

    if item.cart_id != cart.id:
        raise CartNotFoundError("Pozycja nie nalezy do koszyka aktualnego operatora.")

    delete_cart_item(db, item)

    cart.updated_at = datetime.now()
    db.add(cart)
    db.commit()

    return True


def list_orders(
    db: Session,
    operator_id: int,
) -> list[OrderListItemResponse]:
    orders = get_orders_by_operator_id(db, operator_id)
    return [
        OrderListItemResponse(
            id=order.id,
            order_number=order.order_number,
            status=order.status,
            total_amount=float(order.total_amount),
            products_count=len(order.items),
            created_at=order.created_at,
        )
        for order in orders
    ]


def get_order_details(
    db: Session,
    operator_id: int,
    order_id: int,
) -> OrderResponse:
    order = get_order_by_id_and_operator_id(
        db=db,
        order_id=order_id,
        operator_id=operator_id,
    )

    if order is None:
        raise CartNotFoundError("Zamowienie nie istnieje.")

    return OrderResponse.model_validate(order)
