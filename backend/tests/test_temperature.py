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
