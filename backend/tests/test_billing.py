from app.models.billing import Subscription, SubscriptionPlan


def _seed_plans(db_session):
    free = SubscriptionPlan(
        code="free", name="Free", price_cents=0, currency="usd", billing_interval="none",
        max_facilities=1, max_employees=2, ai_assistant_included=False, is_self_serve=True, sort_order=0,
    )
    pro = SubscriptionPlan(
        code="pro", name="Pro", price_cents=9900, currency="usd", billing_interval="month",
        max_facilities=5, max_employees=100, ai_assistant_included=True, is_self_serve=True, sort_order=1,
    )
    db_session.add_all([free, pro])
    db_session.commit()
    return {"free": free, "pro": pro}


def _register_and_login(client, email="owner@acme-foods.com"):
    payload = {
        "email": email,
        "password": "SuperSecret123",
        "full_name": "Owner Acme",
        "company_name": "Acme Foods",
        "role": "company_admin",
    }
    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 201, resp.text
    login = client.post("/api/v1/auth/login", json={"email": email, "password": payload["password"]})
    assert login.status_code == 200, login.text
    client.headers.update({"Authorization": f"Bearer {login.json()['access_token']}"})
    return client


def test_registration_creates_free_subscription(client, db_session):
    _seed_plans(db_session)
    auth = _register_and_login(client)

    resp = auth.get("/api/v1/billing/subscription")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["plan"]["code"] == "free"
    assert data["status"] == "active"


def test_subscription_404_without_seeded_plans(client):
    # No SubscriptionPlan rows exist -> registration can't attach a
    # default plan -> no Subscription row for the new company.
    auth = _register_and_login(client)
    resp = auth.get("/api/v1/billing/subscription")
    assert resp.status_code == 404


def test_list_plans_ordered_and_active_only(client, db_session):
    plans = _seed_plans(db_session)
    plans["pro"].is_active = False
    db_session.commit()

    resp = client.get("/api/v1/billing/plans")
    assert resp.status_code == 200
    codes = [p["code"] for p in resp.json()]
    assert codes == ["free"]  # inactive "pro" excluded


def test_facility_limit_enforced_on_free_plan(client, db_session):
    _seed_plans(db_session)
    auth = _register_and_login(client)

    assert auth.post("/api/v1/companies/facilities", json={"name": "Plant 1"}).status_code == 201
    resp = auth.post("/api/v1/companies/facilities", json={"name": "Plant 2"})
    assert resp.status_code == 402
    assert "Free" in resp.json()["detail"]


def test_employee_limit_enforced_on_free_plan(client, db_session):
    _seed_plans(db_session)
    auth = _register_and_login(client)

    for i in range(2):
        resp = auth.post("/api/v1/companies/employees", json={"full_name": f"Employee {i}"})
        assert resp.status_code == 201, resp.text
    resp = auth.post("/api/v1/companies/employees", json={"full_name": "One too many"})
    assert resp.status_code == 402


def test_ai_assistant_gated_on_free_plan(client, db_session):
    _seed_plans(db_session)
    auth = _register_and_login(client)

    resp = auth.post("/api/v1/ai/chat", json={"message": "hello"})
    assert resp.status_code == 402


def test_ai_assistant_allowed_on_pro_plan_falls_through_to_503(client, db_session):
    plans = _seed_plans(db_session)
    auth = _register_and_login(client)

    sub = db_session.query(Subscription).first()
    sub.plan_id = plans["pro"].id
    db_session.commit()

    resp = auth.post("/api/v1/ai/chat", json={"message": "hello"})
    # Pro plan includes the AI Assistant, so this clears the plan gate and
    # fails downstream instead — no AI backend is configured in tests.
    assert resp.status_code == 503


def test_canceled_subscription_does_not_count_as_usable(client, db_session):
    from app.models.enums import SubscriptionStatus

    plans = _seed_plans(db_session)
    auth = _register_and_login(client)

    sub = db_session.query(Subscription).first()
    sub.plan_id = plans["pro"].id
    sub.status = SubscriptionStatus.CANCELED
    db_session.commit()

    # A canceled subscription is treated the same as "no plan on file" —
    # fails open rather than blocking, since the real webhook handler
    # (customer.subscription.deleted) immediately resets canceled
    # subscriptions back to an active Free plan; this state is only
    # reachable transiently or via direct manipulation like this test.
    resp = auth.post("/api/v1/ai/chat", json={"message": "hello"})
    assert resp.status_code == 503  # falls through to "no AI backend configured"
