def test_create_and_list_suppliers(auth_client):
    resp = auth_client.post(
        "/api/v1/products/suppliers/all",
        json={"name": "Flour Co", "contact_name": "Jane", "email": "jane@flourco.com", "certification": "BRC"},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["name"] == "Flour Co"
    assert body["approval_status"] == "pending"
    assert body["is_active"] is True

    resp = auth_client.get("/api/v1/products/suppliers/all")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_update_supplier_approval_status(auth_client):
    create = auth_client.post("/api/v1/products/suppliers/all", json={"name": "Sugar Co"})
    supplier_id = create.json()["id"]

    resp = auth_client.patch(
        f"/api/v1/products/suppliers/all/{supplier_id}",
        json={"approval_status": "approved", "risk_rating": "low"},
    )
    assert resp.status_code == 200
    assert resp.json()["approval_status"] == "approved"
    assert resp.json()["risk_rating"] == "low"


def test_deactivate_supplier(auth_client):
    create = auth_client.post("/api/v1/products/suppliers/all", json={"name": "Salt Co"})
    supplier_id = create.json()["id"]

    resp = auth_client.patch(f"/api/v1/products/suppliers/all/{supplier_id}", json={"is_active": False})
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False


def test_update_unknown_supplier_returns_404(auth_client):
    resp = auth_client.patch("/api/v1/products/suppliers/all/does-not-exist", json={"name": "x"})
    assert resp.status_code == 404


def test_suppliers_are_company_scoped(client):
    a = {"email": "a@company-a.com", "password": "SuperSecret123", "full_name": "A Admin", "company_name": "Company A"}
    client.post("/api/v1/auth/register", json=a)
    login_a = client.post("/api/v1/auth/login", json={"email": a["email"], "password": a["password"]})
    client.headers.update({"Authorization": f"Bearer {login_a.json()['access_token']}"})
    client.post("/api/v1/products/suppliers/all", json={"name": "Company A Supplier"})

    b = {"email": "b@company-b.com", "password": "SuperSecret123", "full_name": "B Admin", "company_name": "Company B"}
    client.post("/api/v1/auth/register", json=b)
    login_b = client.post("/api/v1/auth/login", json={"email": b["email"], "password": b["password"]})
    client.headers.update({"Authorization": f"Bearer {login_b.json()['access_token']}"})

    resp = client.get("/api/v1/products/suppliers/all")
    assert resp.status_code == 200
    assert resp.json() == []
