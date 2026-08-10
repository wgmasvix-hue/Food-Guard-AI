def test_status_needs_onboarding_for_fresh_company(auth_client):
    resp = auth_client.get("/api/v1/onboarding/status")
    assert resp.status_code == 200
    assert resp.json()["needs_onboarding"] is True


def test_status_false_once_a_plan_exists(auth_client):
    auth_client.post("/api/v1/haccp/plans", json={"name": "Existing Plan"})
    resp = auth_client.get("/api/v1/onboarding/status")
    assert resp.json()["needs_onboarding"] is False


def test_status_false_once_a_product_exists(auth_client):
    auth_client.post("/api/v1/products", json={"name": "Existing Product"})
    resp = auth_client.get("/api/v1/onboarding/status")
    assert resp.json()["needs_onboarding"] is False


def test_list_industries(auth_client):
    resp = auth_client.get("/api/v1/onboarding/industries")
    assert resp.status_code == 200
    assert "bakery" in resp.json()


def test_setup_creates_haccp_plan_even_without_ai_configured(auth_client):
    # No Ollama running in the test sandbox, so this exercises the
    # graceful-degradation path: plan skeleton created, AI draft skipped.
    resp = auth_client.post(
        "/api/v1/onboarding/setup",
        json={"industry": "bakery", "process_description": "Mixing, baking, cooling, packaging of bread loaves."},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["haccp_plan_id"]
    assert body["ai_generated"] is False
    assert body["document_id"] is None

    plan = auth_client.get(f"/api/v1/haccp/plans/{body['haccp_plan_id']}")
    assert plan.status_code == 200
    assert plan.json()["name"] == "Bakery HACCP Plan"
    assert "Mixing" in plan.json()["process_description"]

    status_resp = auth_client.get("/api/v1/onboarding/status")
    assert status_resp.json()["needs_onboarding"] is False


def test_setup_uses_custom_plan_name(auth_client):
    resp = auth_client.post(
        "/api/v1/onboarding/setup",
        json={"industry": "dairy", "process_description": "Pasteurizing and bottling fresh milk.", "plan_name": "Milk Line HACCP"},
    )
    assert resp.status_code == 200
    plan = auth_client.get(f"/api/v1/haccp/plans/{resp.json()['haccp_plan_id']}")
    assert plan.json()["name"] == "Milk Line HACCP"


def test_setup_requires_min_role(client):
    payload = {
        "email": "operator@acme.com", "password": "SuperSecret123",
        "full_name": "Op User", "company_name": "Acme Ops",
    }
    client.post("/api/v1/auth/register", json=payload)
    # Demote the newly-registered company_admin to operator to exercise
    # the role gate (registration always makes the first user an admin).
    login = client.post("/api/v1/auth/login", json={"email": payload["email"], "password": payload["password"]})
    client.headers.update({"Authorization": f"Bearer {login.json()['access_token']}"})
    me = client.get("/api/v1/auth/me").json()
    client.patch(f"/api/v1/users/{me['id']}", json={"role": "operator"})

    resp = client.post(
        "/api/v1/onboarding/setup",
        json={"industry": "bakery", "process_description": "Some process description here."},
    )
    assert resp.status_code == 403


def test_setup_requires_min_description_length(auth_client):
    resp = auth_client.post("/api/v1/onboarding/setup", json={"industry": "bakery", "process_description": "short"})
    assert resp.status_code == 422
