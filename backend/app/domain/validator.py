"""In-flight trade and transaction validator."""

import re
from datetime import date
from decimal import Decimal
from typing import NamedTuple

from app.domain.exceptions import ValidationError
from app.models.enums import TransactionType


class ValidationResult(NamedTuple):
    is_valid: bool
    error_code: str | None = None
    error_message: str | None = None


class TransactionValidator:
    """Validates transactional inputs against investment domain invariants."""

    _CURRENCY_PATTERN = re.compile(r"^[A-Z]{3}$")

    @classmethod
    def validate_currency(cls, currency: str) -> None:
        """Enforces ISO 4217 standard 3-letter uppercase currency."""
        if not currency or not cls._CURRENCY_PATTERN.match(currency):
            raise ValidationError(
                f"Invalid currency code '{currency}'. Must be 3 uppercase ASCII letters.",
                code="ERR_INVALID_CURRENCY",
            )

    @classmethod
    def validate_dates(cls, trade_date: date, settlement_date: date) -> None:
        """Enforces settlement date cannot precede trade date."""
        if settlement_date < trade_date:
            raise ValidationError(
                f"Settlement date ({settlement_date}) cannot precede trade date ({trade_date}).",
                code="ERR_INVALID_DATES",
            )

    @classmethod
    def validate_economics(
        cls,
        tx_type: TransactionType,
        quantity: Decimal,
        unit_price: Decimal,
        fx_rate: Decimal,
    ) -> None:
        """Enforces mathematical invariants on quantities and prices."""
        if fx_rate <= Decimal("0"):
            raise ValidationError(
                f"FX conversion rate must be strictly positive (> 0). Provided: {fx_rate}.",
                code="ERR_INVALID_FX_RATE",
            )

        if tx_type in {TransactionType.BUY, TransactionType.SELL}:
            if quantity <= Decimal("0"):
                raise ValidationError(
                    f"Quantity for {tx_type.value} must be strictly positive (> 0). Provided: {quantity}.",
                    code="ERR_NON_POSITIVE_QUANTITY",
                )
            if unit_price <= Decimal("0"):
                raise ValidationError(
                    f"Unit price for {tx_type.value} must be strictly positive (> 0). Provided: {unit_price}.",
                    code="ERR_NON_POSITIVE_PRICE",
                )
        elif tx_type in {
            TransactionType.DEPOSIT,
            TransactionType.WITHDRAWAL,
            TransactionType.DIVIDEND,
            TransactionType.FEE,
        } and quantity < Decimal("0"):
            raise ValidationError(
                f"Quantity cannot be negative for {tx_type.value}.",
                code="ERR_NEGATIVE_QUANTITY",
            )

    @classmethod
    def validate_transaction(
        cls,
        tx_type: TransactionType,
        quantity: Decimal,
        unit_price: Decimal,
        currency_local: str,
        currency_base: str,
        fx_rate_to_base: Decimal,
        trade_date: date,
        settlement_date: date,
    ) -> ValidationResult:
        """Validates all inputs, returning a safe ValidationResult."""
        try:
            cls.validate_currency(currency_local)
            cls.validate_currency(currency_base)
            cls.validate_dates(trade_date, settlement_date)
            cls.validate_economics(tx_type, quantity, unit_price, fx_rate_to_base)
            return ValidationResult(is_valid=True)
        except ValidationError as e:
            return ValidationResult(is_valid=False, error_code=e.code, error_message=e.message)
