"""Object storage service - S3/MinIO abstraction."""

from __future__ import annotations

import hashlib
import mimetypes
from datetime import UTC
from pathlib import Path
from typing import Any
from uuid import uuid4

import boto3
from botocore.config import Config

from app.core.config import get_settings

settings = get_settings()


def get_s3_client() -> Any:
    """Create an S3-compatible client."""
    return boto3.client(
        "s3",
        endpoint_url=settings.OBJECT_STORAGE_ENDPOINT,
        aws_access_key_id=settings.OBJECT_STORAGE_ACCESS_KEY,
        aws_secret_access_key=settings.OBJECT_STORAGE_SECRET_KEY,
        region_name=settings.OBJECT_STORAGE_REGION,
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
        ),
    )


def ensure_bucket_exists() -> None:
    """Ensure the storage bucket exists, create if not."""
    client = get_s3_client()
    try:
        client.head_bucket(Bucket=settings.OBJECT_STORAGE_BUCKET)
    except Exception:
        client.create_bucket(
            Bucket=settings.OBJECT_STORAGE_BUCKET,
            CreateBucketConfiguration={
                "LocationConstraint": settings.OBJECT_STORAGE_REGION,
            }
            if settings.OBJECT_STORAGE_REGION != "us-east-1"
            else {},
        )


def generate_storage_key(
    organization_id: str,
    filename: str,
    content_type: str | None = None,
) -> str:
    """Generate a secure storage key for a file."""
    # Sanitize filename - extract only the basename
    safe_filename = Path(filename).name

    # Remove any path traversal attempts
    safe_filename = safe_filename.replace("..", "").replace("/", "").replace("\\", "")

    # Remove any non-ASCII characters and keep only safe characters
    safe_filename = "".join(c for c in safe_filename if c.isascii() and (c.isalnum() or c in "._-"))

    # If filename is empty after sanitization, use default
    if not safe_filename:
        safe_filename = "document"

    # Generate unique prefix
    unique_id = uuid4().hex[:12]
    Path(safe_filename).suffix.lower()

    # Determine content type if not provided
    if content_type is None:
        content_type = mimetypes.guess_type(safe_filename)[0] or "application/octet-stream"

    # Build key: org_id/date_prefix/filename
    from datetime import datetime

    date_prefix = datetime.now(UTC).strftime("%Y/%m/%d")
    return f"{organization_id}/{date_prefix}/{unique_id}_{safe_filename}"


def calculate_file_hash(data: bytes, algorithm: str = "sha256") -> str:
    """Calculate file hash for integrity verification."""
    hasher = hashlib.new(algorithm)
    hasher.update(data)
    return hasher.hexdigest()


async def upload_file(
    data: bytes,
    storage_key: str,
    content_type: str = "application/octet-stream",
    metadata: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Upload a file to object storage."""
    client = get_s3_client()

    extra_args = {
        "ContentType": content_type,
    }
    if metadata:
        extra_args["Metadata"] = metadata

    client.put_object(
        Bucket=settings.OBJECT_STORAGE_BUCKET,
        Key=storage_key,
        Body=data,
        **extra_args,
    )

    return {
        "storage_key": storage_key,
        "bucket": settings.OBJECT_STORAGE_BUCKET,
        "size": len(data),
        "content_type": content_type,
    }


async def download_file(storage_key: str) -> bytes:
    """Download a file from object storage."""
    client = get_s3_client()

    response = client.get_object(
        Bucket=settings.OBJECT_STORAGE_BUCKET,
        Key=storage_key,
    )

    return response["Body"].read()


async def delete_file(storage_key: str) -> bool:
    """Delete a file from object storage."""
    client = get_s3_client()

    try:
        client.delete_object(
            Bucket=settings.OBJECT_STORAGE_BUCKET,
            Key=storage_key,
        )
        return True
    except Exception:
        return False


def generate_presigned_url(
    storage_key: str,
    expiration: int = 3600,
) -> str:
    """Generate a presigned URL for file access."""
    client = get_s3_client()

    url = client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": settings.OBJECT_STORAGE_BUCKET,
            "Key": storage_key,
        },
        ExpiresIn=expiration,
    )

    return url


async def file_exists(storage_key: str) -> bool:
    """Check if a file exists in object storage."""
    client = get_s3_client()

    try:
        client.head_object(
            Bucket=settings.OBJECT_STORAGE_BUCKET,
            Key=storage_key,
        )
        return True
    except Exception:
        return False
