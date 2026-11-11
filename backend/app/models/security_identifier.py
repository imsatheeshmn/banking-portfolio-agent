"""Security identifier cross-reference entity in the oltp schema."""

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import AuditMixin, Base
from app.models.enums import IdentifierType

if TYPE_CHECKING:
    from app.models.security import Security


class SecurityIdentifier(Base, AuditMixin):
    """Identifier cross-reference table mapping ISIN, CUSIP, SEDOL, FIGI to security master."""

    __tablename__ = "security_identifiers"
    __table_args__ = (
        UniqueConstraint("identifier_type", "identifier_value", name="uq_sec_id_type_val"),
        CheckConstraint("identifier_value = upper(identifier_value)", name="ck_sec_id_val_upper"),
        {"schema": "oltp"},
    )

    identifier_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    security_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("oltp.securities.security_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    identifier_type: Mapped[IdentifierType] = mapped_column(
        String(16),
        nullable=False,
    )
    identifier_value: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )
    valid_from: Mapped[date] = mapped_column(
        Date,
        default=date(1970, 1, 1),
        nullable=False,
    )
    valid_to: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # Relationships
    security: Mapped["Security"] = relationship(
        "Security",
        back_populates="identifiers",
    )
