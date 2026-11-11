"""Common and RFC 7807 problem details schemas."""

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class ProblemDetails(BaseModel):
    """RFC 7807 standard error payload."""

    type: str = Field(..., description="URI identifier of problem type")
    title: str = Field(..., description="Short human-readable summary")
    status: int = Field(..., description="HTTP status code")
    code: str = Field(..., description="Domain machine-readable error code")
    detail: str = Field(..., description="Human-readable explanation specific to this occurrence")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="UTC timestamp of the error",
    )
