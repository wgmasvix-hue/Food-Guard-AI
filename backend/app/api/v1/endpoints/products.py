from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_active_user, get_db
from app.core.rbac import require_min_role
from app.models.enums import UserRole
from app.models.product import Batch, Product
from app.models.supplier import Supplier
from app.models.user import User
from app.schemas.product import (
    BatchCreate,
    BatchRead,
    ProductCreate,
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
