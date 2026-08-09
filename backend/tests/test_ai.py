from app.services.ai.company_context import build_company_context


def _company_id(auth_client):
    resp = auth_client.get("/api/v1/companies/me")
    assert resp.status_code == 200, resp.text
    return resp.json()["id"]


def test_company_context_empty_without_company(db_session):
    assert build_company_context(db_session, None, "hello") == ""


def test_company_context_surfaces_temperature_excursion(auth_client, db_session):
    company_id = _company_id(auth_client)

    unit_resp = auth_client.post(
        "/api/v1/temperature/units",
        json={"name": "Freezer 1", "unit_type": "freezer", "min_temp": -25, "max_temp": -18},
    )
    assert unit_resp.status_code == 201
    unit_id = unit_resp.json()["id"]
    auth_client.post(f"/api/v1/temperature/units/{unit_id}/logs", json={"temperature": -5})

    context = build_company_context(db_session, company_id, "any temperature issues today?")
    assert "Freezer 1" in context
    assert "-5" in context


def test_company_context_generic_fallback_covers_multiple_modules(auth_client, db_session):
    company_id = _company_id(auth_client)
    context = build_company_context(db_session, company_id, "how are we doing overall?")
    assert "corrective action" in context.lower()
    assert "audit" in context.lower()


def test_company_context_routes_on_keyword_not_just_fallback(auth_client, db_session):
    company_id = _company_id(auth_client)
    context = build_company_context(db_session, company_id, "tell me about our HACCP plans")
    assert "HACCP plans" in context
    # A non-matching, unrelated keyword-routed section shouldn't be pulled in.
    assert "Audits (" not in context


def test_chat_endpoint_503s_without_ai_backend_configured(auth_client):
    resp = auth_client.post("/api/v1/ai/chat", json={"message": "What are our open corrective actions?"})
    assert resp.status_code == 503


def test_company_context_includes_retrieved_document_excerpts(auth_client, db_session):
    company_id = _company_id(auth_client)
    auth_client.post(
        "/api/v1/documents",
        json={
            "title": "Cold Room Cleaning SOP",
            "category": "sop",
            "content_text": "Wipe down all cold room shelving with sanitizer solution weekly.",
        },
    )

    context = build_company_context(db_session, company_id, "what's our cold room cleaning sanitizer procedure?")
    assert "Cold Room Cleaning SOP" in context
    assert "Relevant excerpts from your documents" in context
