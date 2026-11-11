"""Unit tests for transaction state machine, validator, and business calendar."""

import unittest
from datetime import date
from decimal import Decimal

from app.domain.calendar import BusinessCalendar
from app.domain.exceptions import (
    InvalidStateTransitionError,
    ValidationError,
)
from app.domain.state_machine import TransactionStateMachine
from app.domain.validator import TransactionValidator
from app.models.enums import TransactionStatus, TransactionType


class TestDomainStateMachineAndValidator(unittest.TestCase):
    """Tests lifecycle states, transitions, validations, and calendar rules."""

    def test_valid_forward_lifecycle_transitions(self) -> None:
        """Verify normal forward lifecycle from NEW through SETTLED."""
        s1 = TransactionStateMachine.transition(TransactionStatus.NEW, TransactionStatus.VALIDATED)
        self.assertEqual(s1, TransactionStatus.VALIDATED)

        s2 = TransactionStateMachine.transition(s1, TransactionStatus.CONFIRMED)
        self.assertEqual(s2, TransactionStatus.CONFIRMED)

        s3 = TransactionStateMachine.transition(s2, TransactionStatus.SETTLED)
        self.assertEqual(s3, TransactionStatus.SETTLED)

    def test_illegal_lifecycle_transitions(self) -> None:
        """Verify that skipping states or moving backwards raises InvalidStateTransitionError."""
        # Cannot jump directly from NEW to SETTLED
        with self.assertRaises(InvalidStateTransitionError):
            TransactionStateMachine.transition(TransactionStatus.NEW, TransactionStatus.SETTLED)

        # Cannot regress from CONFIRMED back to VALIDATED
        with self.assertRaises(InvalidStateTransitionError):
            TransactionStateMachine.transition(
                TransactionStatus.CONFIRMED, TransactionStatus.VALIDATED
            )

        # Terminal state cannot transition
        with self.assertRaises(InvalidStateTransitionError):
            TransactionStateMachine.transition(
                TransactionStatus.SETTLED, TransactionStatus.VALIDATED
            )

    def test_validator_currency_rules(self) -> None:
        """Enforces 3-letter uppercase ASCII codes."""
        # Valid
        TransactionValidator.validate_currency("USD")
        TransactionValidator.validate_currency("EUR")

        # Invalid
        with self.assertRaises(ValidationError) as ctx:
            TransactionValidator.validate_currency("usd")
        self.assertEqual(ctx.exception.code, "ERR_INVALID_CURRENCY")

        with self.assertRaises(ValidationError):
            TransactionValidator.validate_currency("US1")

        with self.assertRaises(ValidationError):
            TransactionValidator.validate_currency("USDD")

    def test_validator_dates_rules(self) -> None:
        """Enforces settlement date cannot precede trade date."""
        d1 = date(2026, 1, 10)
        d2 = date(2026, 1, 9)
        with self.assertRaises(ValidationError) as ctx:
            TransactionValidator.validate_dates(trade_date=d1, settlement_date=d2)
        self.assertEqual(ctx.exception.code, "ERR_INVALID_DATES")

    def test_validator_economics_rules(self) -> None:
        """Enforces positive quantities, prices, and FX rates."""
        # Negative quantity
        with self.assertRaises(ValidationError) as ctx:
            TransactionValidator.validate_economics(
                tx_type=TransactionType.BUY,
                quantity=Decimal("-10.0"),
                unit_price=Decimal("100.0"),
                fx_rate=Decimal("1.0"),
            )
        self.assertEqual(ctx.exception.code, "ERR_NON_POSITIVE_QUANTITY")

        # Zero unit price
        with self.assertRaises(ValidationError) as ctx:
            TransactionValidator.validate_economics(
                tx_type=TransactionType.BUY,
                quantity=Decimal("10.0"),
                unit_price=Decimal("0.0"),
                fx_rate=Decimal("1.0"),
            )
        self.assertEqual(ctx.exception.code, "ERR_NON_POSITIVE_PRICE")

        # Negative FX rate
        with self.assertRaises(ValidationError) as ctx:
            TransactionValidator.validate_economics(
                tx_type=TransactionType.BUY,
                quantity=Decimal("10.0"),
                unit_price=Decimal("100.0"),
                fx_rate=Decimal("-0.5"),
            )
        self.assertEqual(ctx.exception.code, "ERR_INVALID_FX_RATE")

    def test_business_calendar_weekend_skipping(self) -> None:
        """Verify T+1 settlement rolls Friday to Monday."""
        friday = date(2026, 1, 9)
        settlement = BusinessCalendar.calculate_settlement_date(friday, cycle_offset=1)
        # Next business day must be Monday, Jan 12 (skipping Jan 10 Sat and Jan 11 Sun)
        self.assertEqual(settlement, date(2026, 1, 12))
        self.assertEqual(settlement.weekday(), 0)  # Monday


if __name__ == "__main__":
    unittest.main()
