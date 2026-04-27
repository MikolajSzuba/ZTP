import time

from sqlalchemy.orm import Session

from app.REST.data.database import SessionLocal
from app.notifications.data.notification_repository import get_ready_notifications
from app.notifications.service.notification_service import execute_notification


def process_ready_notifications(db: Session) -> int:
    notifications = get_ready_notifications(db)

    for notification in notifications:
        execute_notification(db, notification.id)

    return len(notifications)


def run_worker(interval_seconds: int = 5) -> None:
    print(f"[WORKER] Uruchomiono worker. Interwal: {interval_seconds} s")

    while True:
        db = SessionLocal()
        try:
            processed = process_ready_notifications(db)
            if processed:
                print(f"[WORKER] Przetworzono {processed} powiadomien.")
        except Exception as exc:
            print(f"[WORKER] Wystapil blad: {exc}")
        finally:
            db.close()

        time.sleep(interval_seconds)
