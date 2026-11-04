"""Organization schemas."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 - Pydantic resolves this annotation at runtime
from uuid import UUID  # noqa: TC003 - Pydantic resolves this annotation at runtime

from pydantic import BaseModel, Field


class CreateOrganizationRequest(BaseModel):
    """Create organization request."""

    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255, pattern=r"^[a-z0-9-]+$")
    description: str | None = Field(None, max_length=1000)


class UpdateOrganizationRequest(BaseModel):
    """Update organization request."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)


class OrganizationResponse(BaseModel):
    """Organization response."""

    id: UUID
    name: str
    slug: str
    description: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class OrganizationMemberResponse(BaseModel):
    """Organization member response."""

    id: UUID
    user_id: UUID
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AddMemberRequest(BaseModel):
    """Add member to organization request."""

    user_id: str
    role: str = Field(default="MEMBER", pattern=r"^(OWNER|ADMIN|MEMBER|VIEWER)$")


class UpdateMemberRoleRequest(BaseModel):
    """Update member role request."""

    role: str = Field(..., pattern=r"^(OWNER|ADMIN|MEMBER|VIEWER)$")
