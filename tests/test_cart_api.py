import re
import uuid


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


def test_get_cart_requires_auth(client):
    response = client.get("/cart")

    assert response.status_code == 401
    assert response.json()["detail"] == "Brak aktywnej sesji."


def test_add_item_and_patch_quantity_in_cart(client):
    auth_token = login_and_get_cookie(client, f"cart-user-{uuid.uuid4().hex[:8]}@example.com")

    product_id = create_product_with_stock(
        client,
        name=f"CartProduct-{uuid.uuid4().hex[:8]}",
        stock_quantity=8,
        price=12.5,
    )

    add_response = client.post(
        "/cart/items",
        cookies={"auth_token": auth_token},
        json={"product_id": product_id, "quantity": 2},
    )

    assert add_response.status_code == 201
    add_data = add_response.json()
    assert add_data["items_count"] == 1
    assert add_data["total_amount"] == 25.0

    item_id = add_data["items"][0]["id"]

    patch_response = client.patch(
        f"/cart/items/{item_id}",
        cookies={"auth_token": auth_token},
        json={"quantity": 5},
    )

    assert patch_response.status_code == 200
    patch_data = patch_response.json()
    assert patch_data["items"][0]["quantity"] == 5
    assert patch_data["total_amount"] == 62.5


def test_cart_rejects_quantity_above_available_stock(client):
    auth_token = login_and_get_cookie(client, f"cart-stock-{uuid.uuid4().hex[:8]}@example.com")

    product_id = create_product_with_stock(
        client,
        name=f"LowStock-{uuid.uuid4().hex[:8]}",
        stock_quantity=3,
    )

    response = client.post(
        "/cart/items",
        cookies={"auth_token": auth_token},
        json={"product_id": product_id, "quantity": 4},
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Nie mozna dodac wiekszej ilosci produktu niz dostepna w magazynie."
    )


def test_checkout_creates_order_decreases_stock_and_clears_cart(client):
    auth_token = login_and_get_cookie(client, f"checkout-{uuid.uuid4().hex[:8]}@example.com")

    product_id = create_product_with_stock(
        client,
        name=f"CheckoutProduct-{uuid.uuid4().hex[:8]}",
        stock_quantity=6,
        price=20.0,
    )

    add_response = client.post(
        "/cart/items",
        cookies={"auth_token": auth_token},
        json={"product_id": product_id, "quantity": 3},
    )
    assert add_response.status_code == 201

    checkout_response = client.post(
        "/cart/checkout",
        cookies={"auth_token": auth_token},
    )

    assert checkout_response.status_code == 201
    order = checkout_response.json()

    assert re.match(r"^ZAM-\d{8}-\d{6}$", order["order_number"]) is not None
    assert order["total_amount"] == 60.0
    assert len(order["items"]) == 1
    assert order["items"][0]["quantity"] == 3

    cart_after = client.get("/cart", cookies={"auth_token": auth_token})
    assert cart_after.status_code == 200
    assert cart_after.json()["items_count"] == 0

    product_after = client.get(f"/api/v1/products/{product_id}")
    assert product_after.status_code == 200
    assert product_after.json()["stock_quantity"] == 3

    list_orders_response = client.get("/orders", cookies={"auth_token": auth_token})
    assert list_orders_response.status_code == 200
    orders = list_orders_response.json()
    assert len(orders) >= 1

    order_id = order["id"]
    order_details_response = client.get(
        f"/orders/{order_id}",
        cookies={"auth_token": auth_token},
    )
    assert order_details_response.status_code == 200
    details = order_details_response.json()
    assert details["id"] == order_id
    assert details["items"][0]["product_id"] == product_id
