"""Immutable bitemporal transaction ledger in the oltp schema."""

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import TransactionStatus, TransactionType

if TYPE_CHECKING:
    from app.models.portfolio import Portfolio
    from app.models.security import Security


class TransactionLedger(Base):
    """Immutable bitemporal transaction ledger.

    Append-only: UPDATE and DELETE are strictly disallowed on this table.
    Cancellations and amendments are handled via linked reversal entries.
    """

    __tablename__ = "transaction_ledger"
    __table_args__ = (
        CheckConstraint("quantity >= 0", name="ck_tx_ledger_quantity_pos"),
        CheckConstraint("unit_price >= 0", name="ck_tx_ledger_price_pos"),
        CheckConstraint("fx_rate_to_base > 0", name="ck_tx_ledger_fx_rate_pos"),
        CheckConstraint("length(currency_local) = 3", name="ck_tx_ledger_curr_local_len"),
        CheckConstraint("length(currency_base) = 3", name="ck_tx_ledger_curr_base_len"),
        Index("ix_tx_ledger_bitemporal_scan", "portfolio_id", "trade_date", "recorded_at_utc"),
        Index("ix_tx_ledger_settlement_scan", "portfolio_id", "settlement_date", "status"),
        {"schema": "oltp"},
    )

    # Immutable Unique Primary Key (UUIDv4 for distributed idempotency)
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Reversal and replacement tracking
    original_transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("oltp.transaction_ledger.transaction_id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
        comment="Points to parent transaction if this row is a cancellation or replacement",
    )

    # Audit, Lineage & Pipeline Correlation
    run_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="Ingestion or execution batch run identifier",
    )
    correlation_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="External trade reference or broker execution ID",
    )

    # Operational Entities
    portfolio_id: Mapped[int] = mapped_column(
        ForeignKey("oltp.portfolios.portfolio_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    security_id: Mapped[int | None] = mapped_column(
        ForeignKey("oltp.securities.security_id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
        comment="Null for pure cash movements (e.g. deposit, fee, cash dividend)",
    )
    cash_account_id: Mapped[int] = mapped_column(
        ForeignKey("oltp.cash_accounts.cash_account_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Transaction Classification & State Machine
    transaction_type: Mapped[TransactionType] = mapped_column(
        String(32),
        nullable=False,
    )
    status: Mapped[TransactionStatus] = mapped_column(
        String(32),
        default=TransactionStatus.NEW.value,
        nullable=False,
        index=True,
    )

    # Bitemporal Axes
    trade_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="Valid Time: Economic commitment date (drives IBOR)",
    )
    settlement_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="Settlement Time: Cash exchange date (drives ABOR)",
    )
    recorded_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        index=True,
        comment="System Time: When the platform committed this record",
    )

    # Economics & Exact Precision Numbers (ADR-001)
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(24, 8),
        default=Decimal("0.0"),
        nullable=False,
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(20, 10),
        default=Decimal("0.0"),
        nullable=False,
    )
    currency_local: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        comment="Trade currency",
    )
    gross_amount_local: Mapped[Decimal] = mapped_column(
        Numeric(20, 4),
        nullable=False,
    )
    net_amount_local: Mapped[Decimal] = mapped_column(
        Numeric(20, 4),
        nullable=False,
        comment="Gross amount minus fees/taxes",
    )
    fx_rate_to_base: Mapped[Decimal] = mapped_column(
        Numeric(20, 10),
        default=Decimal("1.0"),
        nullable=False,
        comment="Exchange rate: Quote Currency per 1 Base Currency (ADR-004)",
    )
    currency_base: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        comment="Portfolio reporting currency",
    )
    net_amount_base: Mapped[Decimal] = mapped_column(
        Numeric(20, 4),
        nullable=False,
        comment="Converted monetary value in portfolio base currency",
    )

    # Maker-Checker & Governance (BCBS 239)
    created_by: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    approved_by: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )
    approved_at_utc: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    portfolio: Mapped["Portfolio"] = relationship(
        "Portfolio",
        back_populates="transactions",
    )
    security: Mapped["Security | None"] = relationship(
        "Security",
        back_populates="transactions",
    )
