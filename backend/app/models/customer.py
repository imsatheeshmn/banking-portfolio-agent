"""Customer entity model in the oltp schema."""

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import AuditMixin, Base

if TYPE_CHECKING:
    from app.models.portfolio import Portfolio


class Customer(Base, AuditMixin):
    """Client / Account owner entity."""

    __tablename__ = "customers"
    __table_args__ = (
        CheckConstraint("length(country_code) = 2", name="ck_customers_country_code_len"),
        CheckConstraint(
            "country_code = upper(country_code)", name="ck_customers_country_code_upper"
        ),
        {"schema": "oltp"},
    )

    customer_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    legal_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    country_code: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
        comment="ISO 3166-1 alpha-2 country code",
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default="ACTIVE",
        nullable=False,
    )

    # Relationships
    portfolios: Mapped[list["Portfolio"]] = relationship(
        "Portfolio",
        back_populates="customer",
        cascade="all, delete-orphan",
    )
