from sqlalchemy.orm import Session
from app.REST.data.product_repository import (
    get_all_products,
    get_product_by_id,
    add_product,
    save_product,
    delete_product,
)
from app.REST.data.product_history_repository import (
    get_product_history_by_product_id,
    add_product_history,
)

from app.REST.model.product_orm import ProductORM
from app.REST.model.product_schema import ProductCreate, ProductUpdate
from app.REST.model.product_history_orm import ProductHistoryORM
from app.REST.service.product_validators import (
    validate_price_not_negative,
    validate_product_banned_names,
    validate_category_exist,
    validate_product_unique_name_in_category,
)


def _build_product_snapshot(product: ProductORM) -> dict:
    category = product.category

    return {
        "id": product.id,
        "name": product.name,
        "price": float(product.price) if product.price is not None else None,
        "category": {
            "id": category.id if category is not None else None,
            "name": category.name if category is not None else None,
        },
    }


def _save_product_history(
    db: Session,
    product_id: int | None,
    previous_state: dict,
    current_state: dict,
    action: str,
):
    history_entry = ProductHistoryORM(
        product_id=product_id,
        action=action,
        previous_state=previous_state,
        current_state=current_state,
    )
    return add_product_history(db, history_entry)

def _validate_product_full_data(db: Session, payload: ProductCreate, product_id: int | None = None):

    validate_price_not_negative(payload.price)
    validate_product_banned_names(db, payload.name)
    category = validate_category_exist(db, payload.category_id)
    validate_product_unique_name_in_category(db, payload.name, payload.category_id, product_id)
    
    return category

def list_products(db: Session):
    return get_all_products(db)


def find_product(db: Session, product_id: int):
    return get_product_by_id(db, product_id)


def list_product_history(db: Session, product_id: int):
    return get_product_history_by_product_id(db, product_id)

def create_product(db: Session, payload: ProductCreate):

    _validate_product_full_data(db, payload)

    product = ProductORM(
        name=payload.name,
        category_id=payload.category_id,
        price=payload.price,
    )
    created_product = add_product(db, product)

    current_state = _build_product_snapshot(created_product)

    _save_product_history(
        db=db,
        product_id=created_product.id,
        previous_state={},
        current_state=current_state,
        action="CREATE",
    )

    return created_product

def replace_product(db: Session, product_id: int, payload: ProductCreate):

    product = get_product_by_id(db, product_id)
    if product is None:
        return None

    previous_state = _build_product_snapshot(product)

    _validate_product_full_data(db, payload, product_id)

    product.name = payload.name
    product.category_id = payload.category_id
    product.price = payload.price

    updated_product = save_product(db, product)

    current_state = _build_product_snapshot(updated_product)

    _save_product_history(
        db=db,
        product_id=updated_product.id,
        previous_state=previous_state,
        current_state=current_state,
        action="REPLACE",
    )

    return updated_product

def patch_product(db: Session, product_id: int, payload: ProductUpdate):
    product = get_product_by_id(db, product_id)
    if product is None:
        return None

    previous_state = _build_product_snapshot(product)

    if payload.name is not None:
        validate_product_banned_names(db, payload.name)
        product.name = payload.name
    if payload.category_id is not None:
        validate_category_exist(db, payload.category_id)
        product.category_id = payload.category_id
    if payload.price is not None:
        validate_price_not_negative(payload.price)
        product.price = payload.price

    target_name = payload.name if payload.name is not None else product.name
    target_category_id = payload.category_id if payload.category_id is not None else product.category_id
    validate_product_unique_name_in_category(db, target_name, target_category_id, product_id)

    updated_product = save_product(db, product)

    current_state = _build_product_snapshot(updated_product)

    _save_product_history(
        db=db,
        product_id=updated_product.id,
        previous_state=previous_state,
        current_state=current_state,
        action="UPDATE",
    )

    return updated_product


def remove_product(db: Session, product_id: int):
    product = get_product_by_id(db, product_id)
    if product is None:
        return None

    previous_state = _build_product_snapshot(product)

    delete_product(db, product)

    _save_product_history(
        db=db,
        product_id=product.id,
        previous_state=previous_state,
        current_state={},
        action="DELETE",
    )

    return product