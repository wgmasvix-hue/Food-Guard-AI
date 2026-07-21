def test_create_plan_hazard_ccp_and_monitoring_deviation(auth_client):
    plan_resp = auth_client.post("/api/v1/haccp/plans", json={"name": "Test Plan"})
    assert plan_resp.status_code == 201
    plan_id = plan_resp.json()["id"]

    ccp_resp = auth_client.post(
        f"/api/v1/haccp/plans/{plan_id}/ccps",
        json={
            "number": "CCP-1", "name": "Cook Step",
            "critical_limit_min": 75, "critical_limit_max": 100, "critical_limit_unit": "°C",
        },
    )
    assert ccp_resp.status_code == 201
    ccp_id = ccp_resp.json()["id"]

    # Within limits: no corrective action should be created.
    ok_resp = auth_client.post(f"/api/v1/haccp/ccps/{ccp_id}/monitoring", json={"measured_value": 80})
    assert ok_resp.status_code == 201
    assert ok_resp.json()["within_limits"] is True
    assert ok_resp.json()["corrective_action_id"] is None

    # Out of limits: should auto-create a corrective action.
    bad_resp = auth_client.post(f"/api/v1/haccp/ccps/{ccp_id}/monitoring", json={"measured_value": 50})
    assert bad_resp.status_code == 201
    assert bad_resp.json()["within_limits"] is False
    assert bad_resp.json()["corrective_action_id"] is not None

    ca_list = auth_client.get("/api/v1/corrective-actions")
    assert ca_list.status_code == 200
    assert len(ca_list.json()) == 1
