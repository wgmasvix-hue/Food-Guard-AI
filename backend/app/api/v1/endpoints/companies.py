from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_active_user, get_db
from app.core.rbac import require_min_role, require_roles
from app.models.company import Company, Department, Facility
from app.models.employee import Employee
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.company import (
    CompanyCreate,
    CompanyRead,
    CompanyUpdate,
    DepartmentCreate,
    DepartmentRead,
    EmployeeCreate,
    EmployeeRead,
    FacilityCreate,
    FacilityRead,
    FacilityUpdate,
)

router = APIRouter()


def _scoped_company_id(current_user: User, company_id: str | None = None) -> str:
    if current_user.role == UserRole.SUPER_ADMIN and company_id:
        return company_id
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is not assigned to a company")
    return current_user.company_id


@router.get("", response_model=list[CompanyRead])
def list_companies(
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db),
):
    return db.query(Company).order_by(Company.name).all()


@router.post("", response_model=CompanyRead, status_code=status.HTTP_201_CREATED)
def create_company(
    payload: CompanyCreate,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db),
):
    company = Company(**payload.model_dump())
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.get("/me", response_model=CompanyRead)
def get_my_company(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    company = db.get(Company, _scoped_company_id(current_user))
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return company


@router.patch("/{company_id}", response_model=CompanyRead)
def update_company(
    company_id: str,
    payload: CompanyUpdate,
    current_user: User = Depends(require_min_role(UserRole.COMPANY_ADMIN)),
    db: Session = Depends(get_db),
):
    if current_user.role != UserRole.SUPER_ADMIN and company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not permitted")
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(company, field, value)
    db.commit()
    db.refresh(company)
    return company


# --- Facilities ---

@router.get("/facilities", response_model=list[FacilityRead])
def list_facilities(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return (
        db.query(Facility)
        .filter(Facility.company_id == _scoped_company_id(current_user))
        .order_by(Facility.name)
        .all()
    )


@router.post("/facilities", response_model=FacilityRead, status_code=status.HTTP_201_CREATED)
def create_facility(
    payload: FacilityCreate,
    current_user: User = Depends(require_min_role(UserRole.COMPANY_ADMIN)),
    db: Session = Depends(get_db),
):
    facility = Facility(company_id=_scoped_company_id(current_user), **payload.model_dump())
    db.add(facility)
    db.commit()
    db.refresh(facility)
    return facility


@router.patch("/facilities/{facility_id}", response_model=FacilityRead)
def update_facility(
    facility_id: str,
    payload: FacilityUpdate,
    current_user: User = Depends(require_min_role(UserRole.COMPANY_ADMIN)),
    db: Session = Depends(get_db),
):
    facility = db.get(Facility, facility_id)
    if not facility or facility.company_id != _scoped_company_id(current_user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facility not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(facility, field, value)
    db.commit()
    db.refresh(facility)
    return facility


# --- Departments ---

@router.get("/facilities/{facility_id}/departments", response_model=list[DepartmentRead])
def list_departments(facility_id: str, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    facility = db.get(Facility, facility_id)
    if not facility or facility.company_id != _scoped_company_id(current_user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facility not found")
    return db.query(Department).filter(Department.facility_id == facility_id).order_by(Department.name).all()


@router.post("/facilities/{facility_id}/departments", response_model=DepartmentRead, status_code=status.HTTP_201_CREATED)
def create_department(
    facility_id: str,
    payload: DepartmentCreate,
    current_user: User = Depends(require_min_role(UserRole.COMPANY_ADMIN)),
    db: Session = Depends(get_db),
):
    facility = db.get(Facility, facility_id)
    if not facility or facility.company_id != _scoped_company_id(current_user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facility not found")
    department = Department(facility_id=facility_id, **payload.model_dump())
    db.add(department)
    db.commit()
    db.refresh(department)
    return department


# --- Employees ---

@router.get("/employees", response_model=list[EmployeeRead])
def list_employees(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return (
        db.query(Employee)
        .filter(Employee.company_id == _scoped_company_id(current_user))
        .order_by(Employee.full_name)
        .all()
    )


@router.post("/employees", response_model=EmployeeRead, status_code=status.HTTP_201_CREATED)
def create_employee(
    payload: EmployeeCreate,
    current_user: User = Depends(require_min_role(UserRole.PRODUCTION_SUPERVISOR)),
    db: Session = Depends(get_db),
):
    employee = Employee(company_id=_scoped_company_id(current_user), **payload.model_dump())
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee
