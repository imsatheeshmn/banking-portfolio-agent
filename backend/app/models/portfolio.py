"""Portfolio master entity in the oltp schema."""

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import AuditMixin, Base

if TYPE_CHECKING:
    from app.models.cash_account import CashAccount
    from app.models.customer import Customer
    from app.models.transaction_ledger import TransactionLedger


class Portfolio(Base, AuditMixin):
    """Investment portfolio account master."""

    __tablename__ = "portfolios"
    __table_args__ = (
        CheckConstraint("length(base_currency) = 3", name="ck_portfolios_currency_len"),
        CheckConstraint(
            "base_currency = upper(base_currency)", name="ck_portfolios_currency_upper"
        ),
        {"schema": "oltp"},
    )

    portfolio_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    portfolio_code: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False,
        index=True,
    )
    customer_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("oltp.customers.customer_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    portfolio_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    base_currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        comment="ISO 4217 reporting currency",
    )
    inception_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default="ACTIVE",
        nullable=False,
    )

    # Relationships
    customer: Mapped["Customer"] = relationship(
        "Customer",
        back_populates="portfolios",
    )
    cash_accounts: Mapped[list["CashAccount"]] = relationship(
        "CashAccount",
        back_populates="portfolio",
        cascade="all, delete-orphan",
    )
    transactions: Mapped[list["TransactionLedger"]] = relationship(
        "TransactionLedger",
        back_populates="portfolio",
    )
