def test_dashboard_summary_defaults(auth_client):
    resp = auth_client.get("/api/v1/dashboard/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["compliance_score"] == 100.0
    assert body["open_corrective_actions"] == 0
    assert isinstance(body["today_tasks"], list) and body["today_tasks"]
    assert isinstance(body["ai_recommendations"], list) and body["ai_recommendations"]


def test_rbac_blocks_operator_from_creating_haccp_plan(client):
    # Registration always makes the first user of a new company a
    # company_admin (role can't be self-assigned - see test_auth.py), so to
    # exercise the operator-blocked path we register normally, then have the
    # admin demote themselves to operator via the /users update endpoint.
    register = client.post(
        "/api/v1/auth/register",
        json={
            "email": "op@acme.com", "password": "SuperSecret123",
            "full_name": "Op User", "company_name": "Acme Ops",
        },
    )
    user_id = register.json()["id"]
    login = client.post("/api/v1/auth/login", json={"email": "op@acme.com", "password": "SuperSecret123"})
    client.headers.update({"Authorization": f"Bearer {login.json()['access_token']}"})

    demote = client.patch(f"/api/v1/users/{user_id}", json={"role": "operator"})
    assert demote.status_code == 200

    resp = client.post("/api/v1/haccp/plans", json={"name": "Should Fail"})
    assert resp.status_code == 403
