from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.cart.model.cart_item_orm import CartItemORM
from app.cart.model.cart_orm import CartORM
from app.cart.model.order_item_orm import OrderItemORM
from app.cart.model.order_orm import OrderORM


def get_cart_by_operator_id(db: Session, operator_id: int) -> CartORM | None:
    query = (
        select(CartORM)
        .where(CartORM.operator_id == operator_id)
        .options(selectinload(CartORM.items).selectinload(CartItemORM.product))
    )
    result = db.execute(query)
    return result.scalars().first()


def create_cart(db: Session, operator_id: int) -> CartORM:
    cart = CartORM(operator_id=operator_id)
    db.add(cart)
    db.commit()
    db.refresh(cart)
    return cart


def get_or_create_cart(db: Session, operator_id: int) -> CartORM:
    cart = get_cart_by_operator_id(db, operator_id)
    if cart is not None:
        return cart
    return create_cart(db, operator_id)


def get_cart_item_by_cart_and_product(
    db: Session,
    cart_id: int,
    product_id: int,
) -> CartItemORM | None:
    query = select(CartItemORM).where(
        CartItemORM.cart_id == cart_id,
        CartItemORM.product_id == product_id,
    )
    result = db.execute(query)
    return result.scalars().first()


def get_cart_item_by_id(db: Session, item_id: int) -> CartItemORM | None:
    query = (
        select(CartItemORM)
        .where(CartItemORM.id == item_id)
        .options(selectinload(CartItemORM.product))
    )
    result = db.execute(query)
    return result.scalars().first()


def add_cart_item(
    db: Session,
    cart_id: int,
    product_id: int,
    quantity: int,
) -> CartItemORM:
    item = CartItemORM(
        cart_id=cart_id,
        product_id=product_id,
        quantity=quantity,
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return item


def save_cart_item(db: Session, item: CartItemORM) -> CartItemORM:
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def delete_cart_item(db: Session, item: CartItemORM) -> None:
    db.delete(item)
    db.commit()


def clear_cart_items(db: Session, cart_id: int) -> None:
    query = delete(CartItemORM).where(CartItemORM.cart_id == cart_id)
    db.execute(query)
    db.commit()


def add_order(db: Session, order: OrderORM) -> OrderORM:
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def save_order(db: Session, order: OrderORM) -> OrderORM:
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def add_order_item(db: Session, item: OrderItemORM) -> OrderItemORM:
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_orders_by_operator_id(db: Session, operator_id: int) -> list[OrderORM]:
    query = (
        select(OrderORM)
        .where(OrderORM.operator_id == operator_id)
        .options(selectinload(OrderORM.items))
        .order_by(OrderORM.created_at.desc())
    )
    result = db.execute(query)
    return list(result.scalars().all())


def get_order_by_id_and_operator_id(
    db: Session,
    order_id: int,
    operator_id: int,
) -> OrderORM | None:
    query = (
        select(OrderORM)
        .where(
            OrderORM.id == order_id,
            OrderORM.operator_id == operator_id,
        )
        .options(selectinload(OrderORM.items))
    )
    result = db.execute(query)
    return result.scalars().first()
