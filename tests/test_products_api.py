import uuid


def build_product_payload(name: str, category_id: int = 1, price: float = 10.0) -> dict:
    return {
        "name": name,
        "category_id": category_id,
        "price": price,
    }


def test_get_products_returns_200_and_list(client):
    response = client.get("/api/v1/products")

    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)

    if data:
        first = data[0]
        assert "id" in first
        assert "name" in first
        assert "price" in first
        assert "category" in first


def test_post_products_creates_product_and_history_entry(client, unique_product_name):
    payload = build_product_payload(unique_product_name)

    create_response = client.post("/api/v1/products", json=payload)

    assert create_response.status_code == 201
    created = create_response.json()

    assert created["name"] == payload["name"]
    assert created["category"]["id"] == payload["category_id"]
    assert float(created["price"]) == payload["price"]

    product_id = created["id"]

    history_response = client.get(f"/api/v1/products/{product_id}/history")
    assert history_response.status_code == 200

    history = history_response.json()
    assert isinstance(history, list)
    assert len(history) >= 1

    latest_entry = history[0]
    assert latest_entry["product_id"] == product_id
    assert latest_entry["action"] == "CREATE"
    assert latest_entry["previous_state"] == {}
    assert latest_entry["current_state"]["name"] == payload["name"]


def test_post_products_rejects_banned_name_phrase(client):
    banned_name = f"Zakazany produkt {uuid.uuid4().hex[:8]}"
    payload = build_product_payload(banned_name)

    response = client.post("/api/v1/products", json=payload)

    assert response.status_code == 422
    body = response.json()
    assert body["detail"] == "Nazwa zawiera zakazana fraze"


def test_put_products_updates_product_and_saves_history(client, unique_product_name):
    create_payload = build_product_payload(unique_product_name, price=20.0)
    create_response = client.post("/api/v1/products", json=create_payload)
    assert create_response.status_code == 201

    created_product = create_response.json()
    product_id = created_product["id"]

    updated_name = f"{create_payload['name']}-UPDATED"
    put_payload = build_product_payload(updated_name, category_id=create_payload["category_id"], price=99.99)

    put_response = client.put(f"/api/v1/products/{product_id}", json=put_payload)
    assert put_response.status_code == 200

    updated_product = put_response.json()
    assert updated_product["id"] == product_id
    assert updated_product["name"] == updated_name
    assert float(updated_product["price"]) == put_payload["price"]

    history_response = client.get(f"/api/v1/products/{product_id}/history")
    assert history_response.status_code == 200

    history = history_response.json()
    assert len(history) >= 2

    latest_entry = history[0]
    create_entry = history[1]

    assert latest_entry["action"] == "REPLACE"
    assert latest_entry["previous_state"]["name"] == create_payload["name"]
    assert latest_entry["current_state"]["name"] == updated_name

    assert create_entry["action"] == "CREATE"
