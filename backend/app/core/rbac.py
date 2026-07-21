"""Role-based access control helpers."""
from fastapi import Depends, HTTPException, status

from app.core.deps import get_current_active_user
from app.models.enums import UserRole
from app.models.user import User

# Role hierarchy used for simple "at least" checks in a couple of spots.
ROLE_RANK = {
    UserRole.OPERATOR: 0,
    UserRole.AUDITOR: 1,
    UserRole.PRODUCTION_SUPERVISOR: 2,
    UserRole.FOOD_SAFETY_OFFICER: 3,
    UserRole.QA_MANAGER: 4,
    UserRole.COMPANY_ADMIN: 5,
    UserRole.SUPER_ADMIN: 6,
}


def require_roles(*roles: UserRole):
    """Dependency factory: raises 403 unless the current user has one of `roles`
    or is a super admin (who can always act)."""

    def dependency(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role == UserRole.SUPER_ADMIN:
            return current_user
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )
        return current_user

    return dependency


def require_min_role(min_role: UserRole):
    """Dependency factory: requires role rank >= min_role's rank."""

    def dependency(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role == UserRole.SUPER_ADMIN:
            return current_user
        if ROLE_RANK.get(current_user.role, -1) < ROLE_RANK.get(min_role, 99):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )
        return current_user

    return dependency
