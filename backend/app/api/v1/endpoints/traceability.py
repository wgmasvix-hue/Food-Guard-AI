"""Raw material lot tracking and recall trace — the other half of
product traceability from app.api.v1.endpoints.products (which owns
finished-goods Batch records). Kept as its own router since lots are
company-wide (not scoped under a single product) and the trace
endpoints cut across both sides of the model.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_active_user, get_db
from app.core.rbac import require_min_role
from app.models.enums import UserRole
from app.models.product import Batch, BatchLotUsage, Product, RawMaterialLot
from app.models.user import User
from app.schemas.product import (
    BatchTraceResult,
    LotTraceResult,
    RawMaterialLotCreate,
    RawMaterialLotRead,
    RawMaterialLotUpdate,
    TraceBatchSummary,
)

router = APIRouter()


def _get_lot_or_404(db: Session, lot_id: str, company_id: str) -> RawMaterialLot:
    lot = db.get(RawMaterialLot, lot_id)
    if not lot or lot.company_id != company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Raw material lot not found")
    return lot


@router.get("/lots", response_model=list[RawMaterialLotRead])
def list_lots(
    status_filter: str | None = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    query = db.query(RawMaterialLot).filter(RawMaterialLot.company_id == current_user.company_id)
    if status_filter:
        query = query.filter(RawMaterialLot.status == status_filter)
    return query.order_by(RawMaterialLot.received_date.desc().nullslast()).all()


@router.post("/lots", response_model=RawMaterialLotRead, status_code=status.HTTP_201_CREATED)
def create_lot(
    payload: RawMaterialLotCreate,
    current_user: User = Depends(require_min_role(UserRole.PRODUCTION_SUPERVISOR)),
    db: Session = Depends(get_db),
):
    lot = RawMaterialLot(company_id=current_user.company_id, **payload.model_dump())
    db.add(lot)
    db.commit()
    db.refresh(lot)
    return lot


@router.patch("/lots/{lot_id}", response_model=RawMaterialLotRead)
def update_lot(
    lot_id: str,
    payload: RawMaterialLotUpdate,
    current_user: User = Depends(require_min_role(UserRole.PRODUCTION_SUPERVISOR)),
    db: Session = Depends(get_db),
):
    lot = _get_lot_or_404(db, lot_id, current_user.company_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(lot, field, value)
    db.commit()
    db.refresh(lot)
    return lot


@router.get("/trace/lot/{lot_number}", response_model=LotTraceResult)
def trace_lot(
    lot_number: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Forward trace — the question a recall starts with: 'this raw
    material lot is bad, which finished batches does it affect?'"""
    lot = (
        db.query(RawMaterialLot)
        .filter(RawMaterialLot.company_id == current_user.company_id, RawMaterialLot.lot_number == lot_number)
        .first()
    )
    if not lot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lot not found")
    batches = (
        db.query(Batch)
        .join(BatchLotUsage, BatchLotUsage.batch_id == Batch.id)
        .filter(BatchLotUsage.raw_material_lot_id == lot.id)
        .all()
    )
    return LotTraceResult(
        lot=lot,
        affected_batches=[TraceBatchSummary.model_validate(b) for b in batches],
    )


@router.get("/trace/batch/{batch_number}", response_model=BatchTraceResult)
def trace_batch(
    batch_number: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Backward trace: 'this finished batch has a complaint, what raw
    material lots (and which suppliers) went into it?'"""
    batch = (
        db.query(Batch)
        .join(Product, Batch.product_id == Product.id)
        .filter(Batch.batch_number == batch_number, Product.company_id == current_user.company_id)
        .first()
    )
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    usages = db.query(BatchLotUsage).filter(BatchLotUsage.batch_id == batch.id).all()
    return BatchTraceResult(batch=batch, lots_used=usages)
