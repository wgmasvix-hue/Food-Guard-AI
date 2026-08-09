def _create_product(auth_client, name="Peanut Butter"):
    resp = auth_client.post("/api/v1/products", json={"name": name, "category": "spread"})
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def test_create_formulation_with_items_and_rollups(auth_client):
    product_id = _create_product(auth_client)

    resp = auth_client.post(
        f"/api/v1/products/{product_id}/formulations",
        json={
            "batch_size": 100,
            "batch_size_unit": "kg",
            "items": [
                {"name": "Roasted Peanuts", "percentage": 90, "quantity": 90, "unit": "kg", "unit_cost": 2.5, "is_allergen": True},
                {"name": "Salt", "percentage": 5, "quantity": 5, "unit": "kg", "unit_cost": 0.5},
                {"name": "Sugar", "percentage": 5, "quantity": 5, "unit": "kg", "unit_cost": 1.0},
            ],
        },
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["version"] == 1
    assert data["status"] == "draft"
    assert len(data["items"]) == 3
    assert data["total_percentage"] == 100
    assert data["total_cost"] == 90 * 2.5 + 5 * 0.5 + 5 * 1.0
    assert data["allergens"] == ["Roasted Peanuts"]


def test_formulation_versioning_increments(auth_client):
    product_id = _create_product(auth_client, "Bread")

    v1 = auth_client.post(f"/api/v1/products/{product_id}/formulations", json={"items": []})
    assert v1.json()["version"] == 1
    v2 = auth_client.post(f"/api/v1/products/{product_id}/formulations", json={"items": []})
    assert v2.json()["version"] == 2

    listing = auth_client.get(f"/api/v1/products/{product_id}/formulations")
    assert [f["version"] for f in listing.json()] == [2, 1]  # newest first


def test_setting_active_archives_previous_active(auth_client):
    product_id = _create_product(auth_client, "Bread")
    v1 = auth_client.post(f"/api/v1/products/{product_id}/formulations", json={"items": []}).json()
    v2 = auth_client.post(f"/api/v1/products/{product_id}/formulations", json={"items": []}).json()

    r1 = auth_client.patch(f"/api/v1/products/{product_id}/formulations/{v1['id']}", json={"status": "active"})
    assert r1.status_code == 200
    assert r1.json()["status"] == "active"

    r2 = auth_client.patch(f"/api/v1/products/{product_id}/formulations/{v2['id']}", json={"status": "active"})
    assert r2.status_code == 200
    assert r2.json()["status"] == "active"
    assert r2.json()["approved_by_id"] is not None

    v1_after = auth_client.get(f"/api/v1/products/{product_id}/formulations/{v1['id']}")
    assert v1_after.json()["status"] == "archived"


def test_add_update_delete_formulation_item(auth_client):
    product_id = _create_product(auth_client, "Bread")
    formulation = auth_client.post(f"/api/v1/products/{product_id}/formulations", json={"items": []}).json()
    fid = formulation["id"]

    item_resp = auth_client.post(
        f"/api/v1/products/{product_id}/formulations/{fid}/items",
        json={"name": "Flour", "percentage": 60, "quantity": 60, "unit": "kg"},
    )
    assert item_resp.status_code == 201, item_resp.text
    item_id = item_resp.json()["id"]

    upd = auth_client.patch(
        f"/api/v1/products/{product_id}/formulations/{fid}/items/{item_id}", json={"percentage": 65}
    )
    assert upd.status_code == 200
    assert upd.json()["percentage"] == 65

    dele = auth_client.delete(f"/api/v1/products/{product_id}/formulations/{fid}/items/{item_id}")
    assert dele.status_code == 204

    fetched = auth_client.get(f"/api/v1/products/{product_id}/formulations/{fid}")
    assert fetched.json()["items"] == []


def test_formulation_not_found_for_wrong_product(auth_client):
    p1 = _create_product(auth_client, "A")
    p2 = _create_product(auth_client, "B")
    formulation = auth_client.post(f"/api/v1/products/{p1}/formulations", json={"items": []}).json()

    resp = auth_client.get(f"/api/v1/products/{p2}/formulations/{formulation['id']}")
    assert resp.status_code == 404
