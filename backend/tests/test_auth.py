def test_register_and_login(client):
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": "new@acme.com", "password": "SuperSecret123",
            "full_name": "New User", "company_name": "Acme", "role": "company_admin",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["email"] == "new@acme.com"

    resp = client.post("/api/v1/auth/login", json={"email": "new@acme.com", "password": "SuperSecret123"})
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body and "refresh_token" in body


def test_login_wrong_password(client, registered_user):
    resp = client.post("/api/v1/auth/login", json={"email": registered_user["email"], "password": "wrong"})
    assert resp.status_code == 401


def test_me_requires_auth(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_me_returns_current_user(auth_client, registered_user):
    resp = auth_client.get("/api/v1/auth/me")
    assert resp.status_code == 200
    assert resp.json()["email"] == registered_user["email"]


def test_password_reset_flow(client, registered_user):
    resp = client.post("/api/v1/auth/password-reset/request", json={"email": registered_user["email"]})
    assert resp.status_code == 200
