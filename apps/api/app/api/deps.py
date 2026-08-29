"""API dependencies for authentication and authorization."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select

from app.core.database import get_db
from app.models.organization import MemberRole, OrganizationMember
from app.models.user import User
from app.services.auth import decode_token

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> User:
    """Get the current authenticated user from JWT token."""
    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    try:
        uuid_user_id = UUID(user_id)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
        ) from err

    result = await db.execute(select(User).where(User.id == uuid_user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


class RequireRole:
    """Dependency that requires the user to have a specific role in an organization."""

    def __init__(self, *allowed_roles: MemberRole) -> None:
        self.allowed_roles = allowed_roles

    async def __call__(
        self,
        organization_id: UUID,
        current_user: CurrentUser,
        db: AsyncSession = Depends(get_db),  # noqa: B008
    ) -> OrganizationMember:
        """Check if user has the required role in the organization."""
        result = await db.execute(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.user_id == current_user.id,
            )
        )
        membership = result.scalar_one_or_none()

        if membership is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a member of this organization",
            )

        if membership.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {', '.join(r.value for r in self.allowed_roles)}",
            )

        return membership


def require_owner_or_admin() -> RequireRole:
    """Require OWNER or ADMIN role."""
    return RequireRole(MemberRole.OWNER, MemberRole.ADMIN)


def require_any_role() -> RequireRole:
    """Require any role (just needs to be a member)."""
    return RequireRole(MemberRole.OWNER, MemberRole.ADMIN, MemberRole.MEMBER, MemberRole.VIEWER)
