from sqlalchemy.orm import Session
from sqlalchemy import select

from model.product_orm import ProductORM
from data.database import Base, engine


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