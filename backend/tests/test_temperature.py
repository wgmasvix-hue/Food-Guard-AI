def test_temperature_alert_creates_corrective_action(auth_client):
    unit_resp = auth_client.post(
        "/api/v1/temperature/units",
        json={"name": "Freezer 1", "unit_type": "freezer", "min_temp": -25, "max_temp": -18},
    )
    assert unit_resp.status_code == 201
    unit_id = unit_resp.json()["id"]

    log_resp = auth_client.post(f"/api/v1/temperature/units/{unit_id}/logs", json={"temperature": -10})
    assert log_resp.status_code == 201
    assert log_resp.json()["within_limits"] is False

    alerts = auth_client.get("/api/v1/temperature/alerts")
    assert alerts.status_code == 200
    assert len(alerts.json()) == 1


def test_temperature_within_limits_no_alert(auth_client):
    unit_resp = auth_client.post(
        "/api/v1/temperature/units",
        json={"name": "Cold Room", "unit_type": "cold_room", "min_temp": 0, "max_temp": 4},
    )
    unit_id = unit_resp.json()["id"]
    log_resp = auth_client.post(f"/api/v1/temperature/units/{unit_id}/logs", json={"temperature": 3})
    assert log_resp.json()["within_limits"] is True

    alerts = auth_client.get("/api/v1/temperature/alerts")
    assert alerts.json() == []


def test_temperature_out_of_range_creates_in_app_notification(auth_client, db_session):
    from app.models.notification import Notification
    from app.models.user import User

    unit_resp = auth_client.post(
        "/api/v1/temperature/units",
        json={"name": "Freezer 2", "unit_type": "freezer", "min_temp": -25, "max_temp": -18},
    )
    unit_id = unit_resp.json()["id"]
    auth_client.post(f"/api/v1/temperature/units/{unit_id}/logs", json={"temperature": -5})

    admin = db_session.query(User).filter(User.email == "owner@acme-foods.com").first()
    notifications = db_session.query(Notification).filter(Notification.user_id == admin.id).all()
    assert len(notifications) == 1
    assert notifications[0].level == "critical"
    assert "Freezer 2" in notifications[0].title
