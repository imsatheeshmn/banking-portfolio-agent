"""Security master entity in the oltp schema."""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import AuditMixin, Base
from app.models.enums import InstrumentType

if TYPE_CHECKING:
    from app.models.security_identifier import SecurityIdentifier
    from app.models.transaction_ledger import TransactionLedger


class Security(Base, AuditMixin):
    """Financial instrument / Security master record."""

    __tablename__ = "securities"
    __table_args__ = (
        CheckConstraint("length(currency) = 3", name="ck_securities_currency_len"),
        CheckConstraint("currency = upper(currency)", name="ck_securities_currency_upper"),
        {"schema": "oltp"},
    )

    security_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    ticker: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )
    security_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    instrument_type: Mapped[InstrumentType] = mapped_column(
        String(32),
        default=InstrumentType.EQUITY.value,
        nullable=False,
    )
    primary_exchange: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        comment="MIC code (ISO 10383) e.g. XNYS, XNAS, XLON",
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        comment="ISO 4217 trading currency",
    )
    country_of_risk: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
        comment="ISO 3166-1 alpha-2 country code",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Relationships
    identifiers: Mapped[list["SecurityIdentifier"]] = relationship(
        "SecurityIdentifier",
        back_populates="security",
        cascade="all, delete-orphan",
    )
    transactions: Mapped[list["TransactionLedger"]] = relationship(
        "TransactionLedger",
        back_populates="security",
    )
