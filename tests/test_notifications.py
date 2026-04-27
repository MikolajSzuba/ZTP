from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import app.notifications.service.notification_service as notification_service
import app.notifications.service.notification_worker as notification_worker


def build_push_notification_payload() -> dict:
    scheduled_local = datetime.now(ZoneInfo("Europe/Warsaw")) + timedelta(minutes=10)
    return {
        "content": "Test PUSH notification",
        "channel": "PUSH",
        "recipient": "test",
        "scheduled_at": scheduled_local.replace(tzinfo=None).isoformat(timespec="seconds"),
        "timezone": "Europe/Warsaw",
    }


def test_post_notification_creates_record_with_idempotency_key(client):
    payload = build_push_notification_payload()

    response = client.post("/api/v1/notifications", json=payload)
    assert response.status_code == 201

    created = response.json()
    assert created["content"] == payload["content"]
    assert created["channel"] == payload["channel"]
    assert created["status"] == "PENDING"
    assert "idempotency_key" in created
    assert isinstance(created["idempotency_key"], str)
    assert created["idempotency_key"].startswith("notif_")


def test_get_notifications_returns_list(client):
    response = client.get("/api/v1/notifications")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_metrics_endpoint_returns_prometheus_format(client):
    response = client.get("/api/v1/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")

    body = response.text
    assert "notifications_sent_total" in body
    assert "notifications_failed_total" in body
    assert "notifications_pending_total" in body
    assert "notifications_cancelled_total" in body
    assert 'notifications_by_channel{status="PENDING",channel="PUSH"}' in body


def test_send_now_changes_status_to_sent(client, monkeypatch):
    payload = build_push_notification_payload()
    create_response = client.post("/api/v1/notifications", json=payload)
    assert create_response.status_code == 201
    notification_id = create_response.json()["id"]

    def fake_dispatch(_notification):
        return None

    monkeypatch.setattr(notification_service, "dispatch_notification", fake_dispatch)

    send_response = client.post(f"/api/v1/notifications/{notification_id}/send-now")
    assert send_response.status_code == 200
    assert send_response.json()["status"] == "SENT"


def test_process_ready_processes_due_notifications(client, monkeypatch):
    ready_payload = build_push_notification_payload()
    ready_create = client.post("/api/v1/notifications", json=ready_payload)
    assert ready_create.status_code == 201
    ready_notification = ready_create.json()
    ready_id = ready_notification["id"]

    monkeypatch.setattr(notification_service, "dispatch_notification", lambda _n: None)
    monkeypatch.setattr(
        notification_worker,
        "get_ready_notifications",
        lambda _db: [notification_service.get_notification_or_raise(_db, ready_id)],
    )

    process_response = client.post("/api/v1/notifications/process-ready")
    assert process_response.status_code == 200
    assert process_response.json()["processed_count"] == 1

    get_response = client.get(f"/api/v1/notifications/{ready_id}")
    assert get_response.status_code == 200
    assert get_response.json()["status"] == "SENT"
