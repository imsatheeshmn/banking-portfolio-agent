"""Cash account segregation entity in the oltp schema."""

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import AuditMixin, Base
from app.models.enums import AccountType

if TYPE_CHECKING:
    from app.models.portfolio import Portfolio


class CashAccount(Base, AuditMixin):
    """Segregated cash account per currency for a portfolio."""

    __tablename__ = "cash_accounts"
    __table_args__ = (
        UniqueConstraint(
            "portfolio_id", "currency", "account_type", name="uq_cash_accounts_port_curr_type"
        ),
        CheckConstraint("length(currency) = 3", name="ck_cash_accounts_currency_len"),
        CheckConstraint("currency = upper(currency)", name="ck_cash_accounts_currency_upper"),
        {"schema": "oltp"},
    )

    cash_account_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    portfolio_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("oltp.portfolios.portfolio_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        comment="ISO 4217 cash currency code",
    )
    account_type: Mapped[AccountType] = mapped_column(
        String(32),
        default=AccountType.SETTLEMENT.value,
        nullable=False,
    )
    iban_or_account_number: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    # Relationships
    portfolio: Mapped["Portfolio"] = relationship(
        "Portfolio",
        back_populates="cash_accounts",
    )
