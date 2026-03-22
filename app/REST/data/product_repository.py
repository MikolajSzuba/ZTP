from sqlalchemy.orm import Session
from sqlalchemy import select

from app.REST.model.product_orm import ProductORM
from app.REST.model.product_history_orm import ProductHistoryORM
from app.REST.data.database import Base, engine


def create_tables():
    Base.metadata.create_all(engine)


def get_all_products(db: Session):
    query = select(ProductORM)
    result = db.execute(query)
    return result.scalars().all()


def get_product_by_id(db: Session, product_id: int):
    query = select(ProductORM).where(ProductORM.id == product_id)
    result = db.execute(query)
    return result.scalars().first()


def get_product_by_name_and_category(db: Session, name: str, category_id: int):
    query = select(ProductORM).where(
        ProductORM.name == name,
        ProductORM.category_id == category_id,
    )
    result = db.execute(query)
    return result.scalars().first()

def add_product(db: Session, product: ProductORM):
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

def save_product(db:Session, product: ProductORM):
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

def delete_product(db:Session,product:ProductORM):
    db.delete(product)
    db.commit()