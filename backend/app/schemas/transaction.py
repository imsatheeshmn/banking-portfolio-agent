"""Transaction booking and retrieval schemas with exact Decimal precision."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import TransactionType


class TransactionCreate(BaseModel):
    """Payload to book an immutable ledger transaction."""

    portfolio_id: int
    security_id: int | None = Field(default=None, description="Null for pure cash movements")
    cash_account_id: int
    transaction_type: TransactionType
    quantity: Decimal = Field(default=Decimal("0.0"), description="NUMERIC(24,8)")
    unit_price: Decimal = Field(default=Decimal("0.0"), description="NUMERIC(20,10)")
    currency_local: str = Field(..., min_length=3, max_length=3)
    gross_amount_local: Decimal = Field(..., description="NUMERIC(20,4)")
    net_amount_local: Decimal | None = None
    fx_rate_to_base: Decimal = Field(default=Decimal("1.0"), description="NUMERIC(20,10)")
    trade_date: date = Field(default_factory=date.today)
    settlement_date: date | None = None
    run_id: str = Field(default="API_POSTING_001", max_length=64)
    correlation_id: str = Field(..., max_length=64, description="Broker or external execution ref")
    created_by: str = Field(default="api_user", max_length=64)


class TransactionResponse(BaseModel):
    """Immutable ledger transaction response."""

    transaction_id: uuid.UUID
    original_transaction_id: uuid.UUID | None = None
    run_id: str
    correlation_id: str
    portfolio_id: int
    security_id: int | None = None
    cash_account_id: int
    transaction_type: str
    status: str
    trade_date: date
    settlement_date: date
    recorded_at_utc: datetime
    quantity: Decimal
    unit_price: Decimal
    currency_local: str
    gross_amount_local: Decimal
    net_amount_local: Decimal
    fx_rate_to_base: Decimal
    currency_base: str
    net_amount_base: Decimal
    created_by: str
    approved_by: str | None = None
    approved_at_utc: datetime | None = None

    class Config:
        from_attributes = True
