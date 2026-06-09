from typing import Set

from app.cart.model.order_orm import OrderORM


ALLOWED_STATUS_TRANSITIONS = {
    "PENDING": {"COMPLETED", "CANCELLED"},
    "COMPLETED": set(),
    "CANCELLED": set(),
}


def validate_status_transition(current_status: str, new_status: str) -> None:
    allowed: Set[str] = ALLOWED_STATUS_TRANSITIONS.get(current_status, set())

    if new_status not in allowed:
        raise ValueError(
            f"Nieprawidlowe przejscie statusu: {current_status} -> {new_status}"
        )
