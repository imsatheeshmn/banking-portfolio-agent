"""Customer Pydantic v2 schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class CustomerCreate(BaseModel):
    """Payload to register a new legal entity customer."""

    legal_name: str = Field(
        ..., min_length=2, max_length=255, description="Full corporate legal name"
    )
    country_code: str = Field(
        ..., min_length=2, max_length=2, description="ISO 3166-1 alpha-2 country code"
    )
    created_by: str = Field(default="api_user", max_length=64)


class CustomerResponse(BaseModel):
    """Customer entity response."""

    customer_id: int
    legal_name: str
    country_code: str
    status: str
    created_at_utc: datetime
    created_by: str

    class Config:
        from_attributes = True
