"""Portfolio and Cash Account Pydantic schemas."""

from datetime import date, datetime

from pydantic import BaseModel, Field


class CashAccountResponse(BaseModel):
    """Cash account detail response."""

    cash_account_id: int
    portfolio_id: int
    currency: str
    account_type: str
    iban_or_account_number: str | None = None
    created_at_utc: datetime

    class Config:
        from_attributes = True


class PortfolioCreate(BaseModel):
    """Payload to create a new investment portfolio."""

    portfolio_code: str = Field(
        ..., min_length=2, max_length=32, description="Unique account identifier"
    )
    customer_id: int = Field(..., description="Foreign key to customer owner")
    portfolio_name: str = Field(..., min_length=2, max_length=255)
    base_currency: str = Field(
        ..., min_length=3, max_length=3, description="ISO 4217 reporting currency"
    )
    inception_date: date = Field(default_factory=date.today)
    created_by: str = Field(default="api_user", max_length=64)


class PortfolioResponse(BaseModel):
    """Portfolio master response."""

    portfolio_id: int
    portfolio_code: str
    customer_id: int
    portfolio_name: str
    base_currency: str
    inception_date: date
    status: str
    created_at_utc: datetime
    cash_accounts: list[CashAccountResponse] = []

    class Config:
        from_attributes = True
