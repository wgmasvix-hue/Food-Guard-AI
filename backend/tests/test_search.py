def test_search_finds_matching_document(auth_client):
    auth_client.post(
        "/api/v1/documents",
        json={
            "title": "Cold Room Cleaning SOP",
            "category": "sop",
            "content_text": "Wipe down all cold room shelving with sanitizer solution weekly. Record temperature before cleaning.",
        },
    )
    auth_client.post(
        "/api/v1/documents",
        json={
            "title": "Allergen Control Policy",
            "category": "policy",
            "content_text": "This policy governs handling of peanut and tree nut allergens across all production lines.",
        },
    )

    resp = auth_client.get("/api/v1/documents/search", params={"q": "cold room sanitizer"})
    assert resp.status_code == 200, resp.text
    results = resp.json()
    assert len(results) >= 1
    assert results[0]["title"] == "Cold Room Cleaning SOP"
    assert "sanitizer" in results[0]["snippet"].lower()


def test_search_no_match_returns_empty(auth_client):
    auth_client.post(
        "/api/v1/documents",
        json={"title": "Waste Disposal SOP", "category": "sop", "content_text": "Segregate waste streams."},
    )
    resp = auth_client.get("/api/v1/documents/search", params={"q": "nonexistent gibberish term"})
    assert resp.status_code == 200
    assert resp.json() == []


def test_search_ignores_archived_documents(auth_client):
    create = auth_client.post(
        "/api/v1/documents",
        json={"title": "Old Allergen Policy", "category": "policy", "content_text": "outdated allergen guidance"},
    )
    doc_id = create.json()["id"]
    auth_client.delete(f"/api/v1/documents/{doc_id}")  # archives, doesn't hard-delete

    resp = auth_client.get("/api/v1/documents/search", params={"q": "allergen guidance"})
    assert resp.status_code == 200
    assert resp.json() == []


def test_search_empty_query_returns_empty(auth_client):
    resp = auth_client.get("/api/v1/documents/search", params={"q": ""})
    assert resp.status_code == 200
    assert resp.json() == []


def test_search_is_scoped_to_own_company(client):
    # Company A creates a document.
    a = {
        "email": "a@company-a.com", "password": "SuperSecret123", "full_name": "A Admin",
        "company_name": "Company A", "role": "company_admin",
    }
    client.post("/api/v1/auth/register", json=a)
    login_a = client.post("/api/v1/auth/login", json={"email": a["email"], "password": a["password"]})
    client.headers.update({"Authorization": f"Bearer {login_a.json()['access_token']}"})
    client.post(
        "/api/v1/documents",
        json={"title": "Company A Secret SOP", "category": "sop", "content_text": "confidential recipe details"},
    )

    # Company B searches — should see nothing from Company A.
    b = {
        "email": "b@company-b.com", "password": "SuperSecret123", "full_name": "B Admin",
        "company_name": "Company B", "role": "company_admin",
    }
    client.post("/api/v1/auth/register", json=b)
    login_b = client.post("/api/v1/auth/login", json={"email": b["email"], "password": b["password"]})
    client.headers.update({"Authorization": f"Bearer {login_b.json()['access_token']}"})

    resp = client.get("/api/v1/documents/search", params={"q": "confidential recipe"})
    assert resp.status_code == 200
    assert resp.json() == []
