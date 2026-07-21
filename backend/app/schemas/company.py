from pydantic import BaseModel

from app.schemas.common import TimestampedORMModel


class CompanyCreate(BaseModel):
    name: str
    legal_name: str | None = None
    registration_number: str | None = None
    industry: str | None = None
    address: str | None = None
    country: str | None = None
    phone: str | None = None
    email: str | None = None


class CompanyUpdate(BaseModel):
    name: str | None = None
    legal_name: str | None = None
    registration_number: str | None = None
    industry: str | None = None
    address: str | None = None
    country: str | None = None
    phone: str | None = None
    email: str | None = None
    is_active: bool | None = None


class CompanyRead(TimestampedORMModel):
    name: str
    legal_name: str | None = None
    registration_number: str | None = None
    industry: str | None = None
    address: str | None = None
    country: str | None = None
    phone: str | None = None
    email: str | None = None
    is_active: bool


class FacilityCreate(BaseModel):
    name: str
    facility_type: str | None = None
    address: str | None = None
    manager_name: str | None = None


class FacilityUpdate(BaseModel):
    name: str | None = None
    facility_type: str | None = None
    address: str | None = None
    manager_name: str | None = None
    is_active: bool | None = None


class FacilityRead(TimestampedORMModel):
    company_id: str
    name: str
    facility_type: str | None = None
    address: str | None = None
    manager_name: str | None = None
    is_active: bool


class DepartmentCreate(BaseModel):
    name: str
    description: str | None = None


class DepartmentRead(TimestampedORMModel):
    facility_id: str
    name: str
    description: str | None = None


class EmployeeCreate(BaseModel):
    facility_id: str | None = None
    department_id: str | None = None
    full_name: str
    position: str | None = None
    email: str | None = None
    phone: str | None = None
    food_safety_trained: bool = False


class EmployeeRead(TimestampedORMModel):
    company_id: str
    facility_id: str | None = None
    department_id: str | None = None
    full_name: str
    position: str | None = None
    email: str | None = None
    phone: str | None = None
    food_safety_trained: bool
    is_active: bool
