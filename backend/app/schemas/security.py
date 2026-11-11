"""Security Master and Identifier cross-reference schemas."""

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.enums import IdentifierType, InstrumentType


class SecurityIdentifierCreate(BaseModel):
    """Payload to register an identifier cross-reference (ISIN, CUSIP, etc.)."""

    identifier_type: IdentifierType
    identifier_value: str = Field(..., min_length=2, max_length=32)
    valid_from: date = Field(default=date(1970, 1, 1))
    valid_to: date | None = None
    created_by: str = Field(default="api_user", max_length=64)


class SecurityIdentifierResponse(BaseModel):
    """Security identifier response."""

    identifier_id: int
    security_id: int
    identifier_type: str
    identifier_value: str
    valid_from: date
    valid_to: date | None = None

    class Config:
        from_attributes = True


class SecurityCreate(BaseModel):
    """Payload to register a new instrument in security master."""

    ticker: str = Field(..., min_length=1, max_length=32)
    security_name: str = Field(..., min_length=2, max_length=255)
    instrument_type: InstrumentType = InstrumentType.EQUITY
    primary_exchange: str = Field(
        ..., min_length=4, max_length=16, description="ISO 10383 MIC exchange code"
    )
    currency: str = Field(..., min_length=3, max_length=3, description="ISO 4217 trade currency")
    country_of_risk: str = Field(
        ..., min_length=2, max_length=2, description="ISO 3166-1 alpha-2 code"
    )
    created_by: str = Field(default="api_user", max_length=64)
    identifiers: list[SecurityIdentifierCreate] = []


class SecurityResponse(BaseModel):
    """Security master response."""

    security_id: int
    ticker: str
    security_name: str
    instrument_type: str
    primary_exchange: str
    currency: str
    country_of_risk: str
    is_active: bool
    created_at_utc: datetime
    identifiers: list[SecurityIdentifierResponse] = []

    class Config:
        from_attributes = True
