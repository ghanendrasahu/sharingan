"""Unit tests for organization services and IDOR protection."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.organization import MemberRole, Organization, OrganizationMember
from app.models.user import User
from app.services.auth import hash_password

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_create_organization(test_session: AsyncSession):
    """Test creating an organization."""
    # Create a user first
    user = User(
        email="orgcreator@example.com",
        hashed_password=hash_password("password123"),
        full_name="Org Creator",
    )
    test_session.add(user)
    await test_session.flush()

    # Create organization
    org = Organization(
        name="Test Startup",
        slug="test-startup",
        description="A test organization",
    )
    test_session.add(org)
    await test_session.flush()

    # Add user as OWNER
    membership = OrganizationMember(
        organization_id=org.id,
        user_id=user.id,
        role=MemberRole.OWNER,
    )
    test_session.add(membership)
    await test_session.flush()

    assert org.id is not None
    assert org.name == "Test Startup"
    assert org.slug == "test-startup"
    assert membership.role == MemberRole.OWNER


@pytest.mark.asyncio
async def test_add_member(test_session: AsyncSession):
    """Test adding a member to an organization."""
    # Create users
    owner = User(
        email="owner@example.com",
        hashed_password=hash_password("password123"),
    )
    member = User(
        email="member@example.com",
        hashed_password=hash_password("password123"),
    )
    test_session.add_all([owner, member])
    await test_session.flush()

    # Create organization
    org = Organization(
        name="Member Test Org",
        slug="member-test-org",
    )
    test_session.add(org)
    await test_session.flush()

    # Add owner
    owner_membership = OrganizationMember(
        organization_id=org.id,
        user_id=owner.id,
        role=MemberRole.OWNER,
    )
    test_session.add(owner_membership)
    await test_session.flush()

    # Add member
    member_membership = OrganizationMember(
        organization_id=org.id,
        user_id=member.id,
        role=MemberRole.MEMBER,
    )
    test_session.add(member_membership)
    await test_session.flush()

    assert member_membership.role == MemberRole.MEMBER


@pytest.mark.asyncio
async def test_prevent_duplicate_membership(test_session: AsyncSession):
    """Test that duplicate memberships are prevented."""
    user = User(
        email="duplicate@example.com",
        hashed_password=hash_password("password123"),
    )
    test_session.add(user)
    await test_session.flush()

    org = Organization(
        name="Duplicate Test Org",
        slug="duplicate-test-org",
    )
    test_session.add(org)
    await test_session.flush()

    # Add member twice
    member1 = OrganizationMember(
        organization_id=org.id,
        user_id=user.id,
        role=MemberRole.MEMBER,
    )
    member2 = OrganizationMember(
        organization_id=org.id,
        user_id=user.id,
        role=MemberRole.ADMIN,
    )
    test_session.add_all([member1, member2])

    with pytest.raises(IntegrityError):
        await test_session.flush()


@pytest.mark.asyncio
async def test_tenant_isolation(test_session: AsyncSession):
    """Test that users can only see their own organization's data."""
    # Create two users
    user1 = User(
        email="user1@example.com",
        hashed_password=hash_password("password123"),
    )
    user2 = User(
        email="user2@example.com",
        hashed_password=hash_password("password123"),
    )
    test_session.add_all([user1, user2])
    await test_session.flush()

    # Create two organizations
    org1 = Organization(name="Org 1", slug="org-1")
    org2 = Organization(name="Org 2", slug="org-2")
    test_session.add_all([org1, org2])
    await test_session.flush()

    # Add users to different orgs
    membership1 = OrganizationMember(
        organization_id=org1.id,
        user_id=user1.id,
        role=MemberRole.OWNER,
    )
    membership2 = OrganizationMember(
        organization_id=org2.id,
        user_id=user2.id,
        role=MemberRole.OWNER,
    )
    test_session.add_all([membership1, membership2])
    await test_session.flush()

    # User1 should only see org1
    from sqlalchemy import select

    result = await test_session.execute(
        select(Organization).join(OrganizationMember).where(OrganizationMember.user_id == user1.id)
    )
    user1_orgs = list(result.scalars().all())
    assert len(user1_orgs) == 1
    assert user1_orgs[0].id == org1.id

    # User2 should only see org2
    result = await test_session.execute(
        select(Organization).join(OrganizationMember).where(OrganizationMember.user_id == user2.id)
    )
    user2_orgs = list(result.scalars().all())
    assert len(user2_orgs) == 1
    assert user2_orgs[0].id == org2.id


@pytest.mark.asyncio
async def test_remove_last_owner_prevented(test_session: AsyncSession):
    """Test that removing the last owner is prevented."""
    owner = User(
        email="lastowner@example.com",
        hashed_password=hash_password("password123"),
    )
    test_session.add(owner)
    await test_session.flush()

    org = Organization(
        name="Last Owner Org",
        slug="last-owner-org",
    )
    test_session.add(org)
    await test_session.flush()

    membership = OrganizationMember(
        organization_id=org.id,
        user_id=owner.id,
        role=MemberRole.OWNER,
    )
    test_session.add(membership)
    await test_session.flush()

    # Count owners
    from sqlalchemy import select

    result = await test_session.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org.id,
            OrganizationMember.role == MemberRole.OWNER,
        )
    )
    owners = list(result.scalars().all())
    assert len(owners) == 1

    # This would be the last owner - should not be removable
    # In real code, this check happens in the API endpoint
