from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_active_user, get_db
from app.core.rbac import require_min_role
from app.models.enums import FormulationStatus, UserRole
from app.models.product import Batch, BatchLotUsage, FormulationItem, Product, ProductFormulation, RawMaterialLot
from app.models.supplier import Supplier
from app.models.user import User
from app.schemas.product import (
    BatchCreate,
    BatchLotUsageCreate,
    BatchLotUsageRead,
    BatchRead,
    BatchUpdate,
    FormulationItemCreate,
    FormulationItemRead,
    FormulationItemUpdate,
    ProductCreate,
    ProductFormulationCreate,
    ProductFormulationRead,
    ProductFormulationUpdate,
    ProductRead,
    SupplierCreate,
    SupplierRead,
    SupplierUpdate,
)

router = APIRouter()


# --- Products ---

@router.get("", response_model=list[ProductRead])
def list_products(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return db.query(Product).filter(Product.company_id == current_user.company_id).order_by(Product.name).all()


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    current_user: User = Depends(require_min_role(UserRole.PRODUCTION_SUPERVISOR)),
    db: Session = Depends(get_db),
):
    product = Product(company_id=current_user.company_id, **payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("/{product_id}", response_model=ProductRead)
def get_product(product_id: str, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product or product.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


# --- Batches ---

@router.get("/{product_id}/batches", response_model=list[BatchRead])
def list_batches(product_id: str, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product or product.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return db.query(Batch).filter(Batch.product_id == product_id).order_by(Batch.production_date.desc()).all()


@router.post("/{product_id}/batches", response_model=BatchRead, status_code=status.HTTP_201_CREATED)
def create_batch(
    product_id: str,
    payload: BatchCreate,
    current_user: User = Depends(require_min_role(UserRole.PRODUCTION_SUPERVISOR)),
    db: Session = Depends(get_db),
):
    product = db.get(Product, product_id)
    if not product or product.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    batch = Batch(**payload.model_dump())
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch


def _get_batch_or_404(db: Session, product_id: str, batch_id: str, company_id: str) -> Batch:
    product = db.get(Product, product_id)
    if not product or product.company_id != company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    batch = db.get(Batch, batch_id)
    if not batch or batch.product_id != product_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    return batch


@router.patch("/{product_id}/batches/{batch_id}", response_model=BatchRead)
def update_batch(
    product_id: str,
    batch_id: str,
    payload: BatchUpdate,
    current_user: User = Depends(require_min_role(UserRole.PRODUCTION_SUPERVISOR)),
    db: Session = Depends(get_db),
):
    """Move a batch through its lifecycle (in_production -> released, or
    -> on_hold/recalled). Recalling requires a reason so there's a record
    of why, for the audit trail this exists to support."""
    batch = _get_batch_or_404(db, product_id, batch_id, current_user.company_id)
    data = payload.model_dump(exclude_unset=True)
    if data.get("status") == "recalled" and not data.get("recall_reason") and not batch.recall_reason:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="recall_reason is required to mark a batch recalled")
    for field, value in data.items():
        setattr(batch, field, value)
    db.commit()
    db.refresh(batch)
    return batch


@router.get("/{product_id}/batches/{batch_id}/lots", response_model=list[BatchLotUsageRead])
def list_batch_lots(
    product_id: str,
    batch_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """The raw material lots recorded as consumed in this batch — the
    backward half of a recall trace ("what went into this batch?")."""
    batch = _get_batch_or_404(db, product_id, batch_id, current_user.company_id)
    return db.query(BatchLotUsage).filter(BatchLotUsage.batch_id == batch.id).all()


@router.post("/{product_id}/batches/{batch_id}/lots", response_model=BatchLotUsageRead, status_code=status.HTTP_201_CREATED)
def record_batch_lot_usage(
    product_id: str,
    batch_id: str,
    payload: BatchLotUsageCreate,
    current_user: User = Depends(require_min_role(UserRole.PRODUCTION_SUPERVISOR)),
    db: Session = Depends(get_db),
):
    """Record that this batch consumed (some quantity of) a given raw
    material lot. Call once per lot used in the batch."""
    batch = _get_batch_or_404(db, product_id, batch_id, current_user.company_id)
    lot = db.get(RawMaterialLot, payload.raw_material_lot_id)
    if not lot or lot.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Raw material lot not found")
    usage = BatchLotUsage(batch_id=batch.id, raw_material_lot_id=lot.id, quantity_used=payload.quantity_used, unit=payload.unit)
    db.add(usage)
    db.commit()
    db.refresh(usage)
    return usage


# --- Formulations ---

def _get_product_or_404(db: Session, product_id: str, company_id: str) -> Product:
    product = db.get(Product, product_id)
    if not product or product.company_id != company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


def _get_formulation_or_404(db: Session, product_id: str, formulation_id: str, company_id: str) -> ProductFormulation:
    _get_product_or_404(db, product_id, company_id)
    formulation = db.get(ProductFormulation, formulation_id)
    if not formulation or formulation.product_id != product_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Formulation not found")
    return formulation


@router.get("/{product_id}/formulations", response_model=list[ProductFormulationRead])
def list_formulations(
    product_id: str, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    _get_product_or_404(db, product_id, current_user.company_id)
    return (
        db.query(ProductFormulation)
        .filter(ProductFormulation.product_id == product_id)
        .order_by(ProductFormulation.version.desc())
        .all()
    )


@router.get("/{product_id}/formulations/{formulation_id}", response_model=ProductFormulationRead)
def get_formulation(
    product_id: str,
    formulation_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return _get_formulation_or_404(db, product_id, formulation_id, current_user.company_id)


@router.post(
    "/{product_id}/formulations", response_model=ProductFormulationRead, status_code=status.HTTP_201_CREATED
)
def create_formulation(
    product_id: str,
    payload: ProductFormulationCreate,
    current_user: User = Depends(require_min_role(UserRole.PRODUCTION_SUPERVISOR)),
    db: Session = Depends(get_db),
):
    _get_product_or_404(db, product_id, current_user.company_id)
    latest_version = (
        db.query(ProductFormulation.version)
        .filter(ProductFormulation.product_id == product_id)
        .order_by(ProductFormulation.version.desc())
        .first()
    )
    next_version = (latest_version[0] + 1) if latest_version else 1

    formulation = ProductFormulation(
        product_id=product_id,
        version=next_version,
        created_by_id=current_user.id,
        batch_size=payload.batch_size,
        batch_size_unit=payload.batch_size_unit,
        notes=payload.notes,
    )
    db.add(formulation)
    db.flush()
    for item in payload.items:
        formulation.items.append(FormulationItem(**item.model_dump()))
    db.commit()
    db.refresh(formulation)
    return formulation


@router.patch("/{product_id}/formulations/{formulation_id}", response_model=ProductFormulationRead)
def update_formulation(
    product_id: str,
    formulation_id: str,
    payload: ProductFormulationUpdate,
    current_user: User = Depends(require_min_role(UserRole.PRODUCTION_SUPERVISOR)),
    db: Session = Depends(get_db),
):
    formulation = _get_formulation_or_404(db, product_id, formulation_id, current_user.company_id)
    data = payload.model_dump(exclude_unset=True)
    new_status = data.get("status")
    for field, value in data.items():
        setattr(formulation, field, value)

    if new_status == FormulationStatus.ACTIVE:
        # Only one version is "active" for a product at a time.
        db.query(ProductFormulation).filter(
            ProductFormulation.product_id == product_id,
            ProductFormulation.id != formulation.id,
            ProductFormulation.status == FormulationStatus.ACTIVE,
        ).update({"status": FormulationStatus.ARCHIVED})
        from datetime import datetime, timezone

        formulation.approved_by_id = current_user.id
        formulation.approved_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(formulation)
    return formulation


@router.post(
    "/{product_id}/formulations/{formulation_id}/items",
    response_model=FormulationItemRead,
    status_code=status.HTTP_201_CREATED,
)
def add_formulation_item(
    product_id: str,
    formulation_id: str,
    payload: FormulationItemCreate,
    current_user: User = Depends(require_min_role(UserRole.PRODUCTION_SUPERVISOR)),
    db: Session = Depends(get_db),
):
    formulation = _get_formulation_or_404(db, product_id, formulation_id, current_user.company_id)
    item = FormulationItem(formulation_id=formulation.id, **payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/{product_id}/formulations/{formulation_id}/items/{item_id}", response_model=FormulationItemRead)
def update_formulation_item(
    product_id: str,
    formulation_id: str,
    item_id: str,
    payload: FormulationItemUpdate,
    current_user: User = Depends(require_min_role(UserRole.PRODUCTION_SUPERVISOR)),
    db: Session = Depends(get_db),
):
    _get_formulation_or_404(db, product_id, formulation_id, current_user.company_id)
    item = db.get(FormulationItem, item_id)
    if not item or item.formulation_id != formulation_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Formulation item not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{product_id}/formulations/{formulation_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_formulation_item(
    product_id: str,
    formulation_id: str,
    item_id: str,
    current_user: User = Depends(require_min_role(UserRole.PRODUCTION_SUPERVISOR)),
    db: Session = Depends(get_db),
):
    _get_formulation_or_404(db, product_id, formulation_id, current_user.company_id)
    item = db.get(FormulationItem, item_id)
    if not item or item.formulation_id != formulation_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Formulation item not found")
    db.delete(item)
    db.commit()


# --- Suppliers ---

@router.get("/suppliers/all", response_model=list[SupplierRead])
def list_suppliers(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return db.query(Supplier).filter(Supplier.company_id == current_user.company_id).order_by(Supplier.name).all()


@router.post("/suppliers/all", response_model=SupplierRead, status_code=status.HTTP_201_CREATED)
def create_supplier(
    payload: SupplierCreate,
    current_user: User = Depends(require_min_role(UserRole.QA_MANAGER)),
    db: Session = Depends(get_db),
):
    supplier = Supplier(company_id=current_user.company_id, **payload.model_dump())
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.patch("/suppliers/all/{supplier_id}", response_model=SupplierRead)
def update_supplier(
    supplier_id: str,
    payload: SupplierUpdate,
    current_user: User = Depends(require_min_role(UserRole.QA_MANAGER)),
    db: Session = Depends(get_db),
):
    supplier = db.get(Supplier, supplier_id)
    if not supplier or supplier.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(supplier, field, value)
    db.commit()
    db.refresh(supplier)
    return supplier
