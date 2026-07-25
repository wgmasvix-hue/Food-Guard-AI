import os
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_active_user, get_db
from app.models.attachment import Attachment
from app.models.user import User
from app.schemas.attachment import AttachmentRead

router = APIRouter()

ALLOWED_ENTITY_TYPES = {"audit", "audit_finding", "audit_checklist_item", "corrective_action", "checklist_item"}


@router.get("", response_model=list[AttachmentRead])
def list_attachments(
    entity_type: str,
    entity_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Attachment)
        .filter(Attachment.entity_type == entity_type, Attachment.entity_id == entity_id)
        .order_by(Attachment.created_at.desc())
        .all()
    )


@router.post("", response_model=AttachmentRead, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    entity_type: str = Form(...),
    entity_id: str = Form(...),
    caption: str | None = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if entity_type not in ALLOWED_ENTITY_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported entity_type: {entity_type}")

    contents = await file.read()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    stored_name = f"{uuid.uuid4()}_{os.path.basename(file.filename or 'upload')}"
    stored_path = os.path.join(settings.UPLOAD_DIR, stored_name)
    with open(stored_path, "wb") as f:
        f.write(contents)

    attachment = Attachment(
        entity_type=entity_type,
        entity_id=entity_id,
        uploaded_by_id=current_user.id,
        file_path=stored_path,
        file_name=file.filename,
        content_type=file.content_type,
        size_bytes=len(contents),
        caption=caption,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment
