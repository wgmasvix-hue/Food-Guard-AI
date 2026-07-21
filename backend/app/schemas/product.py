from datetime import date

from pydantic import BaseModel

from app.schemas.common import TimestampedORMModel


class ProductCreate(BaseModel):
    name: str
    sku: str | None = None
    category: str | None = None
    description: str | None = None
    allergens: str | None = None
    shelf_life_days: int | None = None
    storage_conditions: str | None = None
    intended_use: str | None = None


class ProductRead(TimestampedORMModel):
    company_id: str
    name: str
    sku: str | None = None
    category: str | None = None
    description: str | None = None
    allergens: str | None = None
    shelf_life_days: int | None = None
    storage_conditions: str | None = None
    intended_use: str | None = None
    is_active: bool


class SupplierCreate(BaseModel):
    name: str
    contact_name: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    certification: str | None = None
    certification_expires_on: date | None = None
    risk_rating: str | None = None
    notes: str | None = None


class SupplierUpdate(BaseModel):
    name: str | None = None
    contact_name: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    approval_status: str | None = None
    certification: str | None = None
    certification_expires_on: date | None = None
    risk_rating: str | None = None
    notes: str | None = None
    is_active: bool | None = None


class SupplierRead(TimestampedORMModel):
    company_id: str
    name: str
    contact_name: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    approval_status: str
    certification: str | None = None
    certification_expires_on: date | None = None
    risk_rating: str | None = None
    notes: str | None = None
    is_active: bool


class BatchCreate(BaseModel):
    product_id: str
    facility_id: str | None = None
    batch_number: str
    production_date: date | None = None
    expiry_date: date | None = None
    quantity: float | None = None
    unit: str | None = None


class BatchRead(TimestampedORMModel):
    product_id: str
    facility_id: str | None = None
    batch_number: str
    production_date: date | None = None
    expiry_date: date | None = None
    quantity: float | None = None
    unit: str | None = None
    status: str
