from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import SignatureMeaning


class DigitalSignature(Base, UUIDMixin, TimestampMixin):
    """A lightweight e-signature: who signed, what they attested to, and a
    hash of the record's state at signing time for tamper evidence.

    Polymorphic by design (entity_type + entity_id) so any record — an
    audit, a HACCP plan, a corrective action — can be signed without a
    dedicated table per entity type.
    """

    __tablename__ = "digital_signatures"

    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    meaning: Mapped[SignatureMeaning] = mapped_column(String(50), nullable=False)
    signed_by_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    typed_name: Mapped[str] = mapped_column(String(255), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    signed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    signed_by = relationship("User")
