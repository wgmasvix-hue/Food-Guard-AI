"""Full-text search over uploaded/generated documents — the retrieval
half of a retrieval-augmented-generation (RAG) setup: results from here
get fed into the AI Assistant's prompt (see app.services.ai.company_context)
so answers can cite the company's own SOPs/policies/plans, and are also
exposed directly as a plain search endpoint.

Real Postgres full-text search (tsvector/ts_rank) is used in production.
A portable, weaker LIKE-based fallback exists purely so the test suite
(SQLite) exercises the same code path — SQLite is never used in
production for this app, so its ranking quality doesn't need to match.
"""
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.document import Document

MAX_RESULTS = 5
SNIPPET_LENGTH = 240


@dataclass
class SearchResult:
    document_id: str
    title: str
    category: str
    snippet: str


def _snippet(content: str, terms: list[str], length: int = SNIPPET_LENGTH) -> str:
    lower = content.lower()
    idx = -1
    for term in terms:
        idx = lower.find(term.lower())
        if idx != -1:
            break
    if idx == -1:
        idx = 0
    start = max(0, idx - 40)
    end = min(len(content), start + length)
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(content) else ""
    return f"{prefix}{content[start:end].strip()}{suffix}"


def search_documents(db: Session, company_id: str | None, query: str, limit: int = MAX_RESULTS) -> list[SearchResult]:
    query = (query or "").strip()
    if not query or not company_id:
        return []

    dialect = db.bind.dialect.name if db.bind is not None else ""
    if dialect == "postgresql":
        rows = db.execute(
            text(
                """
                SELECT d.id AS id, d.title AS title, d.category AS category, dv.content_text AS content_text
                FROM documents d
                JOIN document_versions dv ON dv.document_id = d.id
                    AND dv.version = (SELECT MAX(version) FROM document_versions WHERE document_id = d.id)
                WHERE d.company_id = :company_id
                  AND d.is_archived = false
                  AND dv.content_text IS NOT NULL
                  AND to_tsvector('english', dv.content_text) @@ plainto_tsquery('english', :query)
                ORDER BY ts_rank(to_tsvector('english', dv.content_text), plainto_tsquery('english', :query)) DESC
                LIMIT :limit
                """
            ),
            {"query": query, "company_id": company_id, "limit": limit},
        ).all()
        terms = query.split()
        return [
            SearchResult(document_id=r.id, title=r.title, category=r.category, snippet=_snippet(r.content_text or "", terms))
            for r in rows
        ]

    # Portable fallback: naive OR-of-terms match over each document's
    # latest version, ranked by how many distinct query terms hit.
    terms = [t for t in query.lower().split() if t]
    if not terms:
        return []
    documents = (
        db.query(Document).filter(Document.company_id == company_id, Document.is_archived.is_(False)).all()
    )
    scored = []
    for doc in documents:
        latest = doc.versions[0] if doc.versions else None
        content = (latest.content_text or "") if latest else ""
        if not content:
            continue
        haystack = f"{doc.title}\n{content}".lower()
        score = sum(1 for t in terms if t in haystack)
        if score:
            scored.append((score, doc, content))
    scored.sort(key=lambda row: row[0], reverse=True)
    return [
        SearchResult(document_id=doc.id, title=doc.title, category=doc.category, snippet=_snippet(content, terms))
        for _, doc, content in scored[:limit]
    ]
