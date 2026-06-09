from sqlalchemy.orm import Session

from app.cart.model.processed_command_orm import ProcessedCommandORM


def is_command_already_processed(
    db: Session,
    command_name: str,
    idempotency_key: str,
) -> bool:
    return (
        db.query(ProcessedCommandORM)
        .filter_by(command_name=command_name, idempotency_key=idempotency_key)
        .first()
        is not None
    )


def add_processed_command(
    db: Session,
    command_name: str,
    idempotency_key: str,
    operator_id: int,
) -> ProcessedCommandORM:
    processed = ProcessedCommandORM(
        command_name=command_name,
        idempotency_key=idempotency_key,
        operator_id=operator_id,
    )

    db.add(processed)
    db.commit()
    db.refresh(processed)

    return processed
