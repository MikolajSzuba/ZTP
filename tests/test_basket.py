import uuid

from app.cart.model.processed_command_orm import ProcessedCommandORM
from app.notifications.model.notification_orm import NotificationORM


def build_register_payload(email: str) -> dict:
    return {
        "email": email,
        "password": "StrongPass1!",
        "confirm_password": "StrongPass1!",
        "first_name": "Jan",
        "last_name": "Kowalski",
    }


def login_and_get_cookie(client, email: str) -> str:
    client.post("/auth/register", json=build_register_payload(email))
    response = client.post(
        "/auth/login",
        json={"email": email, "password": "StrongPass1!"},
    )
    assert response.status_code == 200
    return response.cookies.get("auth_token")


def create_product_with_stock(client, name: str, stock_quantity: int, price: float = 10.0) -> int:
    response = client.post(
        "/api/v1/products",
        json={
            "name": name,
            "category_id": 1,
            "price": price,
            "stock_quantity": stock_quantity,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_complete_order_and_idempotency(client, db_session):
    email = f"basket-{uuid.uuid4().hex[:8]}@example.com"
    auth_token = login_and_get_cookie(client, email)

    product_id = create_product_with_stock(
        client,
        name=f"BasketProduct-{uuid.uuid4().hex[:8]}",
        stock_quantity=5,
        price=12.0,
    )

    add_response = client.post(
        "/cart/items",
        cookies={"auth_token": auth_token},
        json={"product_id": product_id, "quantity": 2},
    )
    assert add_response.status_code == 201

    checkout_response = client.post(
        "/cart/checkout",
        cookies={"auth_token": auth_token},
    )

    assert checkout_response.status_code == 201
    order = checkout_response.json()
    order_id = order["id"]

    # initial counts
    initial_email_notifs = db_session.query(NotificationORM).filter_by(channel="EMAIL").count()
    initial_push_notifs = db_session.query(NotificationORM).filter_by(channel="PUSH").count()

    complete_url = f"/orders/{order_id}/complete"
    key1 = "complete-test-001"

    resp = client.post(
        complete_url,
        cookies={"auth_token": auth_token},
        headers={"Idempotency-Key": key1},
    )

    assert resp.status_code == 200
    completed_order = resp.json()
    assert completed_order["status"] == "COMPLETED"

    # processed command recorded
    pc_count = (
        db_session.query(ProcessedCommandORM)
        .filter_by(command_name="CompleteOrderCommand", idempotency_key=key1)
        .count()
    )
    assert pc_count == 1

    # notifications created
    after_email_notifs = db_session.query(NotificationORM).filter_by(channel="EMAIL").count()
    after_push_notifs = db_session.query(NotificationORM).filter_by(channel="PUSH").count()

    assert after_email_notifs - initial_email_notifs >= 1
    assert after_push_notifs - initial_push_notifs >= 1

    # repeat with same idempotency key -> should not create duplicates
    resp2 = client.post(
        complete_url,
        cookies={"auth_token": auth_token},
        headers={"Idempotency-Key": key1},
    )
    assert resp2.status_code == 200

    pc_count_after = (
        db_session.query(ProcessedCommandORM)
        .filter_by(command_name="CompleteOrderCommand", idempotency_key=key1)
        .count()
    )
    assert pc_count_after == 1

    after_email_notifs2 = db_session.query(NotificationORM).filter_by(channel="EMAIL").count()
    after_push_notifs2 = db_session.query(NotificationORM).filter_by(channel="PUSH").count()

    assert after_email_notifs2 == after_email_notifs
    assert after_push_notifs2 == after_push_notifs

    # attempt with different idempotency key -> should be blocked (order already COMPLETED)
    resp3 = client.post(
        complete_url,
        cookies={"auth_token": auth_token},
        headers={"Idempotency-Key": "complete-test-002"},
    )
    assert resp3.status_code == 409
