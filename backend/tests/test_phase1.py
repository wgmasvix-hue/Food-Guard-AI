def test_production_line_crud(auth_client):
    facilities = auth_client.post("/api/v1/companies/facilities", json={"name": "Main Plant"})
    assert facilities.status_code == 201
    facility_id = facilities.json()["id"]

    create = auth_client.post(
        f"/api/v1/companies/facilities/{facility_id}/production-lines",
        json={"name": "Line 1", "line_type": "packaging", "capacity_per_hour": 500},
    )
    assert create.status_code == 201
    line_id = create.json()["id"]
    assert create.json()["status"] == "active"

    listed = auth_client.get(f"/api/v1/companies/facilities/{facility_id}/production-lines")
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    updated = auth_client.patch(f"/api/v1/companies/production-lines/{line_id}", json={"status": "maintenance"})
    assert updated.status_code == 200
    assert updated.json()["status"] == "maintenance"


def test_haccp_plan_approval_requires_matching_typed_name(auth_client):
    plan_resp = auth_client.post("/api/v1/haccp/plans", json={"name": "Test Plan"})
    plan_id = plan_resp.json()["id"]

    wrong_name = auth_client.post(
        f"/api/v1/haccp/plans/{plan_id}/approve",
        json={
            "entity_type": "haccp_plan", "entity_id": plan_id,
            "meaning": "haccp_plan_approval", "typed_name": "Someone Else",
        },
    )
    assert wrong_name.status_code == 400

    me = auth_client.get("/api/v1/auth/me").json()
    signed = auth_client.post(
        f"/api/v1/haccp/plans/{plan_id}/approve",
        json={
            "entity_type": "haccp_plan", "entity_id": plan_id,
            "meaning": "haccp_plan_approval", "typed_name": me["full_name"],
        },
    )
    assert signed.status_code == 200
    assert signed.json()["status"] == "approved"

    signatures = auth_client.get(
        "/api/v1/signatures", params={"entity_type": "haccp_plan", "entity_id": plan_id}
    )
    assert signatures.status_code == 200
    assert len(signatures.json()) == 1
    assert signatures.json()[0]["meaning"] == "haccp_plan_approval"


def test_corrective_action_verify_requires_signature(auth_client):
    ca = auth_client.post(
        "/api/v1/corrective-actions",
        json={"title": "Spill", "issue_description": "Water spill in aisle 3"},
    ).json()

    me = auth_client.get("/api/v1/auth/me").json()
    resp = auth_client.post(
        f"/api/v1/corrective-actions/{ca['id']}/verify",
        json={"verification_notes": "Cleaned and re-inspected.", "typed_name": me["full_name"]},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "closed"


def test_audit_template_generates_checklist_and_critical_fail_creates_ca(auth_client):
    template = auth_client.post(
        "/api/v1/audits/templates",
        json={
            "name": "GMP Walkthrough",
            "standard": "ISO 22000",
            "items": [
                {"order": 1, "question": "Hairnets worn?", "is_critical": True},
                {"order": 2, "question": "Floors clean?", "is_critical": False},
            ],
        },
    )
    assert template.status_code == 201
    template_id = template.json()["id"]
    assert len(template.json()["items"]) == 2

    audit = auth_client.post(
        "/api/v1/audits",
        json={"title": "Q1 Audit", "audit_type": "internal", "template_id": template_id},
    )
    assert audit.status_code == 201
    audit_id = audit.json()["id"]
    checklist_items = audit.json()["checklist_items"]
    assert len(checklist_items) == 2

    critical_item = next(i for i in checklist_items if i["is_critical"])
    submit = auth_client.post(
        f"/api/v1/audits/{audit_id}/checklist/submit",
        json=[{"id": critical_item["id"], "result": "fail", "comment": "No hairnet observed"}],
    )
    assert submit.status_code == 200
    updated_item = next(i for i in submit.json()["checklist_items"] if i["id"] == critical_item["id"])
    assert updated_item["corrective_action_id"] is not None

    cas = auth_client.get("/api/v1/corrective-actions")
    assert any(ca["source"] == "audit" for ca in cas.json())


def test_audit_completion_requires_signature(auth_client):
    audit = auth_client.post(
        "/api/v1/audits", json={"title": "Q2 Audit", "audit_type": "internal"}
    ).json()
    me = auth_client.get("/api/v1/auth/me").json()

    resp = auth_client.post(
        f"/api/v1/audits/{audit['id']}/complete",
        json={
            "entity_type": "audit", "entity_id": audit["id"],
            "meaning": "audit_completion", "typed_name": me["full_name"],
        },
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"
    assert resp.json()["completed_date"] is not None


def test_audit_ai_analysis_unavailable_returns_503(auth_client):
    """No Ollama/AI backend is running in the test environment, so this
    should fail cleanly with 503 rather than crash with a 500."""
    audit = auth_client.post(
        "/api/v1/audits", json={"title": "AI Audit", "audit_type": "internal"}
    ).json()
    resp = auth_client.post(f"/api/v1/audits/{audit['id']}/ai-analysis")
    assert resp.status_code == 503

    latest = auth_client.get(f"/api/v1/audits/{audit['id']}/ai-analysis")
    assert latest.status_code == 200
    assert latest.json() is None


def test_attachment_upload_and_list(auth_client):
    audit = auth_client.post(
        "/api/v1/audits", json={"title": "Attach Audit", "audit_type": "internal"}
    ).json()

    upload = auth_client.post(
        "/api/v1/attachments",
        data={"entity_type": "audit", "entity_id": audit["id"], "caption": "Evidence photo"},
        files={"file": ("evidence.txt", b"fake image bytes", "text/plain")},
    )
    assert upload.status_code == 201
    assert upload.json()["caption"] == "Evidence photo"

    listed = auth_client.get(
        "/api/v1/attachments", params={"entity_type": "audit", "entity_id": audit["id"]}
    )
    assert listed.status_code == 200
    assert len(listed.json()) == 1
