"""Unit tests for database models."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import MemberRole, Organization, OrganizationMember, User


@pytest.mark.asyncio
async def test_create_user(test_session: AsyncSession):
    """Test creating a user."""
    user = User(
        email="test@example.com",
        hashed_password="hashed_password_123",
        full_name="Test User",
    )
    test_session.add(user)
    await test_session.flush()

    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.is_active is True
    assert user.is_verified is False


@pytest.mark.asyncio
async def test_create_organization(test_session: AsyncSession):
    """Test creating an organization."""
    org = Organization(
        name="Test Startup",
        slug="test-startup",
        description="A test organization",
    )
    test_session.add(org)
    await test_session.flush()

    assert org.id is not None
    assert org.name == "Test Startup"
    assert org.slug == "test-startup"


@pytest.mark.asyncio
async def test_organization_member_relationship(test_session: AsyncSession):
    """Test organization membership."""
    user = User(
        email="member@example.com",
        hashed_password="hashed_password_123",
    )
    org = Organization(
        name="Test Org",
        slug="test-org-membership",
    )
    test_session.add_all([user, org])
    await test_session.flush()

    member = OrganizationMember(
        organization_id=org.id,
        user_id=user.id,
        role=MemberRole.OWNER,
    )
    test_session.add(member)
    await test_session.flush()

    assert member.id is not None
    assert member.role == MemberRole.OWNER


@pytest.mark.asyncio
async def test_user_repr():
    """Test user string representation."""
    user = User(
        email="repr@example.com",
        hashed_password="hashed_password_123",
    )
    assert "repr@example.com" in repr(user)


@pytest.mark.asyncio
async def test_organization_repr():
    """Test organization string representation."""
    org = Organization(
        name="Repr Org",
        slug="repr-org",
    )
    assert "Repr Org" in repr(org)
