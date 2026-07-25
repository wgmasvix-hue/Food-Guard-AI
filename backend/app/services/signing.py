"""Lightweight e-signature capture shared by HACCP approval, corrective
action verification, and audit completion.

This is NOT a cryptographic PKI signature — it's a re-authentication-style
attestation (typed full name + timestamp + IP + hash of what was signed)
suitable for an internal QMS audit trail. For regulated contexts requiring
21 CFR Part 11 / EU Annex 11 compliance, layer real PKI signing on top of
this record rather than replacing it.
"""
import hashlib
from datetime import datetime, timezone

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.models.signature import DigitalSignature
from app.models.user import User
from app.schemas.signature import SignatureCreate


def _hash_content(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def sign(
    db: Session,
    *,
    request: Request,
    current_user: User,
    payload: SignatureCreate,
    entity_type: str,
    entity_id: str,
    content_to_hash: str,
) -> DigitalSignature:
    """Validate the typed name matches the signer, then persist the signature.

    Raises 400 if the typed name doesn't match — this is the whole
    "re-authentication" gesture for a lightweight e-signature.
    """
    if payload.typed_name.strip().lower() != current_user.full_name.strip().lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Typed name must match your account's full name to sign.",
        )

    signature = DigitalSignature(
        entity_type=entity_type,
        entity_id=entity_id,
        meaning=payload.meaning,
        signed_by_id=current_user.id,
        typed_name=payload.typed_name,
        content_hash=_hash_content(content_to_hash),
        ip_address=request.client.host if request.client else None,
        signed_at=datetime.now(timezone.utc),
        notes=payload.notes,
    )
    db.add(signature)
    db.flush()
    return signature
