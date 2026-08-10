def _make_product(auth_client, name="Bread"):
    resp = auth_client.post("/api/v1/products", json={"name": name})
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _make_batch(auth_client, product_id, batch_number="B-100"):
    resp = auth_client.post(
        f"/api/v1/products/{product_id}/batches",
        json={"product_id": product_id, "batch_number": batch_number, "quantity": 500, "unit": "kg"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _make_lot(auth_client, lot_number="L-500", material_name="Wheat Flour"):
    resp = auth_client.post(
        "/api/v1/traceability/lots",
        json={"material_name": material_name, "lot_number": lot_number, "quantity_received": 1000, "unit": "kg"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def test_create_and_list_lots(auth_client):
    _make_lot(auth_client, "L-1")
    _make_lot(auth_client, "L-2")
    resp = auth_client.get("/api/v1/traceability/lots")
    assert resp.status_code == 200
    numbers = {l["lot_number"] for l in resp.json()}
    assert numbers == {"L-1", "L-2"}


def test_update_lot_status(auth_client):
    lot_id = _make_lot(auth_client)
    resp = auth_client.patch(f"/api/v1/traceability/lots/{lot_id}", json={"status": "quarantined"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "quarantined"


def test_batch_status_update_requires_reason_for_recall(auth_client):
    product_id = _make_product(auth_client)
    batch_id = _make_batch(auth_client, product_id)

    resp = auth_client.patch(f"/api/v1/products/{product_id}/batches/{batch_id}", json={"status": "recalled"})
    assert resp.status_code == 400

    resp = auth_client.patch(
        f"/api/v1/products/{product_id}/batches/{batch_id}",
        json={"status": "recalled", "recall_reason": "Foreign material found"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "recalled"
    assert resp.json()["recall_reason"] == "Foreign material found"


def test_record_lot_usage_and_list(auth_client):
    product_id = _make_product(auth_client)
    batch_id = _make_batch(auth_client, product_id)
    lot_id = _make_lot(auth_client)

    resp = auth_client.post(
        f"/api/v1/products/{product_id}/batches/{batch_id}/lots",
        json={"raw_material_lot_id": lot_id, "quantity_used": 50, "unit": "kg"},
    )
    assert resp.status_code == 201, resp.text

    resp = auth_client.get(f"/api/v1/products/{product_id}/batches/{batch_id}/lots")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["raw_material_lot"]["lot_number"] == "L-500"


def test_trace_lot_forward_to_affected_batches(auth_client):
    product_id = _make_product(auth_client)
    batch_id = _make_batch(auth_client, product_id, "B-RECALL")
    lot_id = _make_lot(auth_client, "L-BAD")
    auth_client.post(
        f"/api/v1/products/{product_id}/batches/{batch_id}/lots",
        json={"raw_material_lot_id": lot_id, "quantity_used": 10},
    )

    resp = auth_client.get("/api/v1/traceability/trace/lot/L-BAD")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["lot"]["lot_number"] == "L-BAD"
    assert len(body["affected_batches"]) == 1
    assert body["affected_batches"][0]["batch_number"] == "B-RECALL"


def test_trace_batch_backward_to_lots_used(auth_client):
    product_id = _make_product(auth_client)
    batch_id = _make_batch(auth_client, product_id, "B-200")
    lot_id = _make_lot(auth_client, "L-999")
    auth_client.post(
        f"/api/v1/products/{product_id}/batches/{batch_id}/lots",
        json={"raw_material_lot_id": lot_id, "quantity_used": 25},
    )

    resp = auth_client.get("/api/v1/traceability/trace/batch/B-200")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["batch"]["batch_number"] == "B-200"
    assert len(body["lots_used"]) == 1
    assert body["lots_used"][0]["raw_material_lot"]["lot_number"] == "L-999"


def test_trace_unknown_lot_returns_404(auth_client):
    resp = auth_client.get("/api/v1/traceability/trace/lot/does-not-exist")
    assert resp.status_code == 404


def test_traceability_is_company_scoped(client):
    a = {
        "email": "a@company-a.com", "password": "SuperSecret123", "full_name": "A Admin",
        "company_name": "Company A",
    }
    client.post("/api/v1/auth/register", json=a)
    login_a = client.post("/api/v1/auth/login", json={"email": a["email"], "password": a["password"]})
    client.headers.update({"Authorization": f"Bearer {login_a.json()['access_token']}"})
    client.post(
        "/api/v1/traceability/lots",
        json={"material_name": "Secret Sauce", "lot_number": "L-SECRET"},
    )

    b = {
        "email": "b@company-b.com", "password": "SuperSecret123", "full_name": "B Admin",
        "company_name": "Company B",
    }
    client.post("/api/v1/auth/register", json=b)
    login_b = client.post("/api/v1/auth/login", json={"email": b["email"], "password": b["password"]})
    client.headers.update({"Authorization": f"Bearer {login_b.json()['access_token']}"})

    resp = client.get("/api/v1/traceability/lots")
    assert resp.status_code == 200
    assert resp.json() == []

    resp = client.get("/api/v1/traceability/trace/lot/L-SECRET")
    assert resp.status_code == 404
