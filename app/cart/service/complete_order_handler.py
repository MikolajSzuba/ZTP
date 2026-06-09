import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session

from app.cart.data.processed_command_repository import (
    is_command_already_processed,
    add_processed_command,
)
from app.cart.data.cart_repository import get_order_by_id_and_operator_id, save_order
from app.cart.service.cart_exceptions import CartNotFoundError
from app.cart.model.order_orm import OrderORM
from app.cart.service.complete_order_command import CompleteOrderCommand
from app.cart.service.order_state_machine import validate_status_transition
from app.notifications.service.notification_service import (
    create_notification,
)
from app.notifications.model.notification_schema import NotificationCreate
from app.notifications.model.notification_channel import NotificationChannel

logger = logging.getLogger(__name__)


def handle_complete_order(db: Session, command: CompleteOrderCommand) -> OrderORM:
    try:
        logger.info(f"[complete_order] Starting for order_id={command.order_id}, operator_id={command.operator_id}")
        
        # idempotency check
        if is_command_already_processed(
            db=db,
            command_name=command.command_name,
            idempotency_key=command.idempotency_key,
        ):
            logger.info(f"[complete_order] Command already processed, returning cached order")
            order = get_order_by_id_and_operator_id(
                db=db,
                order_id=command.order_id,
                operator_id=command.operator_id,
            )
            return order

        order = get_order_by_id_and_operator_id(
            db=db,
            order_id=command.order_id,
            operator_id=command.operator_id,
        )
        logger.info(f"[complete_order] Fetched order: {order}")

        if order is None:
            logger.error(f"[complete_order] Order not found")
            raise CartNotFoundError("Zamowienie nie zostalo znalezione.")

        logger.info(f"[complete_order] Order status before transition: {order.status}")
        validate_status_transition(current_status=order.status, new_status="COMPLETED")

        order.status = "COMPLETED"
        order = save_order(db, order)
        logger.info(f"[complete_order] Order saved with new status: {order.status}")

        add_processed_command(
            db=db,
            command_name=command.command_name,
            idempotency_key=command.idempotency_key,
            operator_id=command.operator_id,
        )

        # create notifications
        items_count = len(order.items) if order.items else 0
        content = (
            f"Zamowienie {order.order_number} zostalo zakonczone. "
            f"Liczba pozycji: {items_count}. "
            f"Suma: {float(order.total_amount)}. "
            f"Status: {order.status}."
        )
        logger.info(f"[complete_order] Notification content: {content}")

        scheduled_at = datetime.now(timezone.utc) + timedelta(seconds=1)

        if command.notify_email:
            logger.info(f"[complete_order] Creating EMAIL notification")
            email_notification = NotificationCreate(
                content=content,
                channel=NotificationChannel.EMAIL,
                recipient=command.completed_by,
                scheduled_at=scheduled_at,
                timezone="UTC",
            )
            create_notification(db=db, notification_data=email_notification)

        if command.notify_push:
            logger.info(f"[complete_order] Creating PUSH notification")
            push_notification = NotificationCreate(
                content=content,
                channel=NotificationChannel.PUSH,
                recipient="push",
                scheduled_at=scheduled_at,
                timezone="UTC",
            )
            create_notification(db=db, notification_data=push_notification)

        logger.info(f"[complete_order] Completed successfully")
        return order
    
    except Exception as e:
        logger.exception(f"[complete_order] Exception occurred: {str(e)}")
        raise
