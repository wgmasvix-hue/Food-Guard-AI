from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_active_user, get_db
from app.core.logging import log_action
from app.core.rate_limit import limiter
from app.core.security import (
    create_access_token,
    create_password_reset_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.billing import Subscription, SubscriptionPlan
from app.models.company import Company
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    PasswordChange,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshRequest,
    TokenPair,
    UserCreate,
    UserRead,
)
from app.schemas.common import Msg

router = APIRouter()


def _issue_tokens(user: User) -> TokenPair:
    return TokenPair(
        access_token=create_access_token(user.id, extra={"role": user.role, "company_id": user.company_id}),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
@limiter.limit(f"{settings.AUTH_RATE_LIMIT_PER_MINUTE}/minute")
def register(request: Request, payload: UserCreate, db: Session = Depends(get_db)):
    """Register the first user of a new company (multi-company support)."""
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    company = None
    if payload.company_name:
        company = Company(name=payload.company_name)
        db.add(company)
        db.flush()

        free_plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.code == "free").first()
        if free_plan:
            db.add(Subscription(company_id=company.id, plan_id=free_plan.id))

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role if company else UserRole.OPERATOR,
        company_id=company.id if company else None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    log_action(db, user_id=user.id, action="register", entity="user", entity_id=user.id,
               ip_address=request.client.host if request.client else None)
    return user


@router.post("/login", response_model=TokenPair)
@limiter.limit(f"{settings.AUTH_RATE_LIMIT_PER_MINUTE}/minute")
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")

    from datetime import datetime, timezone
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    log_action(db, user_id=user.id, action="login", entity="user", entity_id=user.id,
               ip_address=request.client.host if request.client else None)
    return _issue_tokens(user)


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    token_data = decode_token(payload.refresh_token, expected_type="refresh")
    if not token_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    user = db.get(User, token_data.get("sub"))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    return _issue_tokens(user)


@router.post("/password-reset/request", response_model=Msg)
@limiter.limit(f"{settings.AUTH_RATE_LIMIT_PER_MINUTE}/minute")
def request_password_reset(request: Request, payload: PasswordResetRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if user:
        token = create_password_reset_token(user.email)
        # SMTP is optional in dev; log the token so it can be used/tested without email infra.
        if not settings.SMTP_HOST:
            print(f"[password-reset] token for {user.email}: {token}")
        log_action(db, user_id=user.id, action="password_reset_requested", entity="user", entity_id=user.id)
    # Always return 200 to avoid leaking whether an email is registered.
    return Msg(message="If that email is registered, a reset link has been sent.")


@router.post("/password-reset/confirm", response_model=Msg)
def confirm_password_reset(payload: PasswordResetConfirm, db: Session = Depends(get_db)):
    token_data = decode_token(payload.token, expected_type="password_reset")
    if not token_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")
    user = db.query(User).filter(User.email == token_data.get("sub")).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")
    user.hashed_password = hash_password(payload.new_password)
    db.commit()
    log_action(db, user_id=user.id, action="password_reset_confirmed", entity="user", entity_id=user.id)
    return Msg(message="Password has been reset.")


@router.post("/password-change", response_model=Msg)
def change_password(
    payload: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    current_user.hashed_password = hash_password(payload.new_password)
    db.commit()
    log_action(db, user_id=current_user.id, action="password_changed", entity="user", entity_id=current_user.id)
    return Msg(message="Password updated.")


@router.get("/me", response_model=UserRead)
def read_me(current_user: User = Depends(get_current_active_user)):
    return current_user
