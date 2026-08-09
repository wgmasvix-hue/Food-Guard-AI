from pydantic import BaseModel, EmailStr, Field

from app.models.enums import UserRole
from app.schemas.common import TimestampedORMModel


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)
    company_name: str | None = Field(default=None, description="Creates a new company if provided")
    # No client-supplied role: the register endpoint always assigns
    # company_admin (new company) or operator (no company) itself. A
    # self-registration endpoint must never let the caller pick their own
    # privilege level — see /users for how roles get changed afterward,
    # gated by require_min_role(COMPANY_ADMIN).


class UserRead(TimestampedORMModel):
    email: EmailStr
    full_name: str
    role: UserRole
    company_id: str | None = None
    facility_id: str | None = None
    phone: str | None = None
    is_active: bool


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: UserRole | None = None
    facility_id: str | None = None
    phone: str | None = None
    is_active: bool | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)
