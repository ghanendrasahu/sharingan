"""Organization API endpoints."""

from __future__ import annotations

from datetime import UTC
from typing import TYPE_CHECKING
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, RequireRole
from app.core.database import get_db
from app.models.organization import MemberRole, Organization, OrganizationMember
from app.schemas.organization import (
    AddMemberRequest,
    CreateOrganizationRequest,
    OrganizationMemberResponse,
    OrganizationResponse,
    UpdateMemberRoleRequest,
    UpdateOrganizationRequest,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.post(
    "",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_organization(
    request: CreateOrganizationRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> Organization:
    """Create a new organization and add creator as OWNER."""
    # Check slug uniqueness
    result = await db.execute(select(Organization).where(Organization.slug == request.slug))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Organization slug already exists",
        )

    # Create organization
    org = Organization(
        name=request.name,
        slug=request.slug,
        description=request.description,
    )
    db.add(org)
    await db.flush()

    # Add creator as OWNER
    membership = OrganizationMember(
        organization_id=org.id,
        user_id=current_user.id,
        role=MemberRole.OWNER,
    )
    db.add(membership)
    await db.flush()
    await db.refresh(org)

    return org


@router.get(
    "",
    response_model=list[OrganizationResponse],
)
async def list_organizations(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> list[Organization]:
    """List all organizations the current user is a member of."""
    result = await db.execute(
        select(Organization)
        .join(OrganizationMember)
        .where(OrganizationMember.user_id == current_user.id)
        .where(Organization.deleted_at.is_(None))
    )
    return list(result.scalars().all())


@router.get(
    "/{organization_id}",
    response_model=OrganizationResponse,
)
async def get_organization(
    organization_id: UUID,
    current_user: CurrentUser,
    _membership: OrganizationMember = Depends(  # noqa: B008
        RequireRole(MemberRole.OWNER, MemberRole.ADMIN, MemberRole.MEMBER, MemberRole.VIEWER)  # noqa: B008
    ),
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> Organization:
    """Get organization details (requires membership)."""
    result = await db.execute(select(Organization).where(Organization.id == organization_id))
    org = result.scalar_one_or_none()

    if org is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    return org


@router.patch(
    "/{organization_id}",
    response_model=OrganizationResponse,
)
async def update_organization(
    organization_id: UUID,
    request: UpdateOrganizationRequest,
    _membership: OrganizationMember = Depends(RequireRole(MemberRole.OWNER, MemberRole.ADMIN)),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> Organization:
    """Update organization (OWNER or ADMIN only)."""
    result = await db.execute(select(Organization).where(Organization.id == organization_id))
    org = result.scalar_one_or_none()

    if org is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    if request.name is not None:
        org.name = request.name
    if request.description is not None:
        org.description = request.description

    await db.flush()
    await db.refresh(org)
    return org


@router.delete(
    "/{organization_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_organization(
    organization_id: UUID,
    _membership: OrganizationMember = Depends(RequireRole(MemberRole.OWNER)),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> None:
    """Delete organization (OWNER only). Soft deletes the organization."""
    result = await db.execute(select(Organization).where(Organization.id == organization_id))
    org = result.scalar_one_or_none()

    if org is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    from datetime import datetime

    org.deleted_at = datetime.now(UTC)
    await db.flush()


# Member management endpoints


@router.get(
    "/{organization_id}/members",
    response_model=list[OrganizationMemberResponse],
)
async def list_members(
    organization_id: UUID,
    _membership: OrganizationMember = Depends(  # noqa: B008
        RequireRole(MemberRole.OWNER, MemberRole.ADMIN, MemberRole.MEMBER, MemberRole.VIEWER)  # noqa: B008
    ),
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> list[OrganizationMember]:
    """List all members of an organization."""
    result = await db.execute(
        select(OrganizationMember).where(OrganizationMember.organization_id == organization_id)
    )
    return list(result.scalars().all())


@router.post(
    "/{organization_id}/members",
    response_model=OrganizationMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_member(
    organization_id: UUID,
    request: AddMemberRequest,
    _membership: OrganizationMember = Depends(RequireRole(MemberRole.OWNER, MemberRole.ADMIN)),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> OrganizationMember:
    """Add a member to the organization (OWNER or ADMIN only)."""
    # Check if user is already a member
    result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == UUID(request.user_id),
        )
    )
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member of this organization",
        )

    member = OrganizationMember(
        organization_id=organization_id,
        user_id=UUID(request.user_id),
        role=MemberRole(request.role),
    )
    db.add(member)
    await db.flush()
    await db.refresh(member)

    return member


@router.patch(
    "/{organization_id}/members/{member_id}",
    response_model=OrganizationMemberResponse,
)
async def update_member_role(
    organization_id: UUID,
    member_id: UUID,
    request: UpdateMemberRoleRequest,
    _membership: OrganizationMember = Depends(RequireRole(MemberRole.OWNER)),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> OrganizationMember:
    """Update member role (OWNER only)."""
    result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.id == member_id,
            OrganizationMember.organization_id == organization_id,
        )
    )
    member = result.scalar_one_or_none()

    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )

    member.role = MemberRole(request.role)
    await db.flush()
    await db.refresh(member)

    return member


@router.delete(
    "/{organization_id}/members/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_member(
    organization_id: UUID,
    member_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> None:
    """Remove a member from the organization.

    OWNER or ADMIN can remove others. Users can remove themselves.
    """
    result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.id == member_id,
            OrganizationMember.organization_id == organization_id,
        )
    )
    member = result.scalar_one_or_none()

    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )

    # Check if user is removing themselves or has permission
    if member.user_id != current_user.id:
        # Check if current user has permission
        perm_result = await db.execute(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.user_id == current_user.id,
            )
        )
        perm_member = perm_result.scalar_one_or_none()
        if perm_member is None or perm_member.role not in (
            MemberRole.OWNER,
            MemberRole.ADMIN,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

    # Prevent removing the last OWNER
    if member.role == MemberRole.OWNER:
        owner_count_result = await db.execute(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.role == MemberRole.OWNER,
            )
        )
        owner_count = len(owner_count_result.scalars().all())
        if owner_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last owner",
            )

    await db.delete(member)
    await db.flush()
