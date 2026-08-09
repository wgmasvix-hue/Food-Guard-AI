import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_active_user, get_db
from app.models.document import Document, DocumentVersion
from app.models.user import User
from app.schemas.document import DocumentCreate, DocumentRead, DocumentSearchResult, DocumentVersionRead
from app.services.search import search_documents
from app.services.text_extraction import extract_text

router = APIRouter()


def _get_or_404(db: Session, document_id: str, company_id: str) -> Document:
    document = db.get(Document, document_id)
    if not document or document.company_id != company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document


@router.get("", response_model=list[DocumentRead])
def list_documents(
    category: str | None = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    query = db.query(Document).filter(
        Document.company_id == current_user.company_id, Document.is_archived.is_(False)
    )
    if category:
        query = query.filter(Document.category == category)
    return query.order_by(Document.title).all()


@router.get("/search", response_model=list[DocumentSearchResult])
def search(
    q: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Free-text search over this company's documents — full-text ranked
    search on Postgres, a portable keyword fallback elsewhere. Available
    on every plan; the AI Assistant also uses this internally to ground
    chat answers in retrieved document content (Pro-gated there via AI
    credits, not here)."""
    results = search_documents(db, current_user.company_id, q)
    return [DocumentSearchResult(document_id=r.document_id, title=r.title, category=r.category, snippet=r.snippet) for r in results]


@router.post("", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
def create_document(
    payload: DocumentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    data = payload.model_dump(exclude={"content_text"})
    document = Document(company_id=current_user.company_id, owner_id=current_user.id, **data)
    db.add(document)
    db.flush()
    if payload.content_text:
        document.versions.append(
            DocumentVersion(uploaded_by_id=current_user.id, version=1, content_text=payload.content_text)
        )
    db.commit()
    db.refresh(document)
    return document


@router.get("/{document_id}", response_model=DocumentRead)
def get_document(document_id: str, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return _get_or_404(db, document_id, current_user.company_id)


@router.post("/{document_id}/versions", response_model=DocumentVersionRead, status_code=status.HTTP_201_CREATED)
async def upload_version(
    document_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    document = _get_or_404(db, document_id, current_user.company_id)

    contents = await file.read()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    stored_name = f"{uuid.uuid4()}_{os.path.basename(file.filename or 'upload')}"
    stored_path = os.path.join(settings.UPLOAD_DIR, stored_name)
    with open(stored_path, "wb") as f:
        f.write(contents)

    # Best-effort text extraction so this version is searchable by RAG
    # (see app.services.search / app.services.text_extraction) — failures
    # never block the upload, they just leave content_text empty.
    content_text = extract_text(contents, file.content_type, file.filename)

    next_version = (max((v.version for v in document.versions), default=0)) + 1
    version = DocumentVersion(
        document_id=document.id,
        uploaded_by_id=current_user.id,
        version=next_version,
        file_path=stored_path,
        file_name=file.filename,
        content_type=file.content_type,
        size_bytes=len(contents),
        content_text=content_text,
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return version


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def archive_document(document_id: str, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    document = _get_or_404(db, document_id, current_user.company_id)
    document.is_archived = True
    db.commit()
