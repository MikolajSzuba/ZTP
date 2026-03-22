from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.REST.model.product_history_orm import ProductHistoryORM


def _ensure_product_history_table(db: Session):
    # Existing Docker volume may not have this table yet; create it lazily.
    ProductHistoryORM.__table__.create(bind=db.get_bind(), checkfirst=True)


def get_product_history_by_product_id(db: Session, product_id: int):
    _ensure_product_history_table(db)

    query = (
        select(ProductHistoryORM)
        .where(ProductHistoryORM.product_id == product_id)
        .order_by(
            desc(ProductHistoryORM.changed_at),
            desc(ProductHistoryORM.id),
        )
    )
    result = db.execute(query)
    return result.scalars().all()


def add_product_history(db: Session, history_entry: ProductHistoryORM):
    _ensure_product_history_table(db)

    db.add(history_entry)
    db.commit()
    db.refresh(history_entry)
    return history_entry
