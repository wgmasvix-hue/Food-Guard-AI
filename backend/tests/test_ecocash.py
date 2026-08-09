from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.main import app
from app.models.billing import SubscriptionPlan
from app.models.enums import UserRole
from app.models.user import User


def _seed_plans(db_session):
    free = SubscriptionPlan(
        code="free", name="Free", price_cents=0, currency="usd", billing_interval="none",
        max_facilities=1, max_employees=2, ai_assistant_included=True, ai_credits_per_month=20,
        is_self_serve=True, sort_order=0,
    )
    pro = SubscriptionPlan(
        code="pro", name="Pro", price_cents=9900, currency="usd", billing_interval="month",
        max_facilities=5, max_employees=100, ai_assistant_included=True, ai_credits_per_month=None,
        is_self_serve=True, sort_order=1,
    )
    enterprise = SubscriptionPlan(
        code="enterprise", name="Enterprise", price_cents=0, currency="usd", billing_interval="none",
        max_facilities=None, max_employees=None, ai_assistant_included=True, ai_credits_per_month=None,
        is_self_serve=False, sort_order=2,
    )
    db_session.add_all([free, pro, enterprise])
    db_session.commit()
    return {"free": free, "pro": pro, "enterprise": enterprise}


def _register_and_login(client, email="owner@acme-foods.com"):
    payload = {
        "email": email, "password": "SuperSecret123", "full_name": "Owner Acme",
        "company_name": "Acme Foods", "role": "company_admin",
    }
    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 201, resp.text
    login = client.post("/api/v1/auth/login", json={"email": email, "password": payload["password"]})
    assert login.status_code == 200, login.text
    client.headers.update({"Authorization": f"Bearer {login.json()['access_token']}"})
    return client


def _super_admin_client(db_session, email="root@foodos.internal"):
    user = User(
        email=email, full_name="Platform Admin", role=UserRole.SUPER_ADMIN,
        hashed_password=hash_password("SuperSecret123"),
    )
    db_session.add(user)
    db_session.commit()

    admin_client = TestClient(app)
    login = admin_client.post("/api/v1/auth/login", json={"email": email, "password": "SuperSecret123"})
    assert login.status_code == 200, login.text
    admin_client.headers.update({"Authorization": f"Bearer {login.json()['access_token']}"})
    return admin_client


def test_ecocash_info_is_public(client):
    resp = client.get("/api/v1/billing/ecocash/info")
    assert resp.status_code == 200
    assert resp.json()["merchant_number"]


def test_submit_and_confirm_ecocash_payment(client, db_session):
    _seed_plans(db_session)
    auth = _register_and_login(client)

    submit = auth.post("/api/v1/billing/ecocash/submit", json={"plan_code": "pro"})
    assert submit.status_code == 201, submit.text
    payment = submit.json()
    assert payment["status"] == "pending"
    assert payment["reference_code"].startswith("FG-")
    assert payment["amount_cents"] == 9900

    confirm = auth.post(
        f"/api/v1/billing/ecocash/{payment['id']}/confirm",
        json={"transaction_reference": "MP240101.1234.A56789", "payer_phone": "0771234567"},
    )
    assert confirm.status_code == 200, confirm.text
    assert confirm.json()["status"] == "submitted"
    assert confirm.json()["transaction_reference"] == "MP240101.1234.A56789"

    # Can't confirm twice.
    again = auth.post(
        f"/api/v1/billing/ecocash/{payment['id']}/confirm", json={"transaction_reference": "duplicate"}
    )
    assert again.status_code == 400


def test_ecocash_submit_rejects_sales_assisted_plan(client, db_session):
    _seed_plans(db_session)
    auth = _register_and_login(client)

    resp = auth.post("/api/v1/billing/ecocash/submit", json={"plan_code": "enterprise"})
    assert resp.status_code == 400


def test_non_admin_cannot_review_ecocash_payments(client, db_session):
    _seed_plans(db_session)
    auth = _register_and_login(client)

    resp = auth.get("/api/v1/billing/ecocash/pending")
    assert resp.status_code == 403


def test_super_admin_approve_activates_plan(client, db_session):
    plans = _seed_plans(db_session)
    auth = _register_and_login(client)

    submit = auth.post("/api/v1/billing/ecocash/submit", json={"plan_code": "pro"}).json()
    auth.post(f"/api/v1/billing/ecocash/{submit['id']}/confirm", json={"transaction_reference": "ABC123"})

    admin = _super_admin_client(db_session)
    pending = admin.get("/api/v1/billing/ecocash/pending")
    assert pending.status_code == 200
    assert len(pending.json()) == 1
    assert pending.json()[0]["id"] == submit["id"]

    approve = admin.post(f"/api/v1/billing/ecocash/{submit['id']}/approve")
    assert approve.status_code == 200, approve.text
    assert approve.json()["status"] == "approved"

    sub = auth.get("/api/v1/billing/subscription")
    assert sub.json()["plan"]["code"] == "pro"

    # Can't approve twice.
    again = admin.post(f"/api/v1/billing/ecocash/{submit['id']}/approve")
    assert again.status_code == 400


def test_super_admin_reject_leaves_plan_unchanged(client, db_session):
    _seed_plans(db_session)
    auth = _register_and_login(client)

    submit = auth.post("/api/v1/billing/ecocash/submit", json={"plan_code": "pro"}).json()
    auth.post(f"/api/v1/billing/ecocash/{submit['id']}/confirm", json={"transaction_reference": "ABC123"})

    admin = _super_admin_client(db_session)
    reject = admin.post(f"/api/v1/billing/ecocash/{submit['id']}/reject", json={"reason": "Reference not found"})
    assert reject.status_code == 200
    assert reject.json()["status"] == "rejected"
    assert reject.json()["review_notes"] == "Reference not found"

    sub = auth.get("/api/v1/billing/subscription")
    assert sub.json()["plan"]["code"] == "free"


def test_ecocash_payment_scoped_to_own_company(client, db_session):
    _seed_plans(db_session)
    auth_a = _register_and_login(client, email="a@company-a.com")
    submit = auth_a.post("/api/v1/billing/ecocash/submit", json={"plan_code": "pro"}).json()

    # A fresh client as a different company shouldn't be able to confirm it.
    client_b = TestClient(app)
    b_payload = {
        "email": "b@company-b.com", "password": "SuperSecret123", "full_name": "B Admin",
        "company_name": "Company B", "role": "company_admin",
    }
    client_b.post("/api/v1/auth/register", json=b_payload)
    login_b = client_b.post("/api/v1/auth/login", json={"email": "b@company-b.com", "password": "SuperSecret123"})
    client_b.headers.update({"Authorization": f"Bearer {login_b.json()['access_token']}"})

    resp = client_b.post(f"/api/v1/billing/ecocash/{submit['id']}/confirm", json={"transaction_reference": "x"})
    assert resp.status_code == 404
