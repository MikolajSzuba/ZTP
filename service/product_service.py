from sqlalchemy.orm import Session
from data.product_repository import (
    get_all_products,
    get_product_by_id,
    add_product,
    save_product,
    delete_product
)

from model.product_orm import ProductORM
from model.product_schema import ProductCreate, ProductUpdate
from service.product_validators import (
    validate_price_not_negative,
    validate_product_banned_names,
    validate_category_exist
)

def _validate_product_full_data(db: Session,payload: ProductCreate, product_id: int=None):
    
    validate_price_not_negative(payload.price)
    validate_product_banned_names(db, payload.name)
    category = validate_category_exist(db, payload.category_id)
    
    return category

def list_products(db: Session):
    return get_all_products(db)


def find_product(db: Session, product_id: int):
    return get_product_by_id(db, product_id)

def create_product(db: Session,payload: ProductCreate):
    
    _validate_product_full_data(db, payload)
    
    product=ProductORM(
        name=payload.name,
        category_id = payload.category_id,
        price= payload.price,
    )
    return add_product(db, product)

def replace_product(db: Session, product_id:int, payload: ProductCreate):
    
    product = get_product_by_id(db, product_id)
    if product is None:
        return None
    
    _validate_product_full_data(db,payload,product_id)
    
    product.name=payload.name
    product.category_id = payload.category_id
    product.price = payload.price
    
    return save_product(db ,product)

def patch_product(db: Session, product_id: int, payload: ProductUpdate):
    product = get_product_by_id(db, product_id)
    if product is None:
        return None

    if payload.name is not None:
        validate_product_banned_names(db, payload.name)
        product.name = payload.name
    if payload.category_id is not None:
        validate_category_exist(db, payload.category_id)
        product.category_id = payload.category_id
    if payload.price is not None:
        validate_price_not_negative(payload.price)
        product.price = payload.price

    return save_product(db, product)


def remove_product(db: Session, product_id: int):
    product = get_product_by_id(db, product_id)
    if product is None:
        return None
    delete_product(db, product)
    return product