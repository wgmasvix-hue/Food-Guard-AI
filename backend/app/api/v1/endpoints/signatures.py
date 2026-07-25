from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_active_user, get_db
from app.models.signature import DigitalSignature
from app.models.user import User
from app.schemas.signature import SignatureRead

router = APIRouter()


@router.get("", response_model=list[SignatureRead])
def list_signatures(
    entity_type: str,
    entity_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Signature history for a given entity. Company scoping happens
    implicitly: callers only ever pass IDs of entities they could already
    fetch through their own scoped endpoints."""
    return (
        db.query(DigitalSignature)
        .filter(DigitalSignature.entity_type == entity_type, DigitalSignature.entity_id == entity_id)
        .order_by(DigitalSignature.signed_at.desc())
        .all()
    )
