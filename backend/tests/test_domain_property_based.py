"""Property-based tests verifying ledger invariants using Hypothesis for Milestone 1b."""

import unittest
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from hypothesis import given, settings
from hypothesis import strategies as st

from app.domain.exceptions import InsufficientHoldingsError
from app.domain.position_engine import PositionEngine
from app.models.enums import TransactionStatus, TransactionType
from app.models.transaction_ledger import TransactionLedger


class TestDomainPropertyBased(unittest.TestCase):
    """Hypothesis property tests proving mathematical and accounting invariants."""

    def _make_ledger_tx(
        self,
        tx_id: uuid.UUID,
        tx_type: TransactionType,
        quantity: Decimal,
        unit_price: Decimal,
        trade_date: date,
        status: TransactionStatus = TransactionStatus.SETTLED,
        original_tx_id: uuid.UUID | None = None,
    ) -> TransactionLedger:
        gross = (quantity * unit_price).quantize(Decimal("0.0001"))
        return TransactionLedger(
            transaction_id=tx_id,
            original_transaction_id=original_tx_id,
            run_id="RUN_PROP_001",
            correlation_id=f"CORR_{tx_id}",
            portfolio_id=1,
            security_id=10,
            cash_account_id=100,
            transaction_type=tx_type.value,
            status=status.value,
            trade_date=trade_date,
            settlement_date=trade_date,
            recorded_at_utc=datetime.now(UTC),
            quantity=quantity,
            unit_price=unit_price,
            currency_local="USD",
            gross_amount_local=gross,
            net_amount_local=gross,
            fx_rate_to_base=Decimal("1.0"),
            currency_base="USD",
            net_amount_base=gross,
            created_by="hypothesis_test",
        )

    @given(
        st.lists(
            st.tuples(
                st.integers(min_value=1, max_value=500),  # Buy quantity
                st.integers(min_value=10, max_value=1000),  # Buy price
            ),
            min_size=1,
            max_size=15,
        )
    )
    @settings(max_examples=50)
    def test_property_buys_cumulative_quantity_invariant(
        self, buy_lots: list[tuple[int, int]]
    ) -> None:
        """Property: Total closing quantity must equal exact arithmetic sum of buy quantities."""
        ledger: list[TransactionLedger] = []
        expected_total_qty = Decimal("0")
        expected_total_cost = Decimal("0")

        for idx, (qty_int, price_int) in enumerate(buy_lots):
            qty = Decimal(str(qty_int))
            price = Decimal(str(price_int))
            expected_total_qty += qty
            expected_total_cost += qty * price

            tx = self._make_ledger_tx(
                tx_id=uuid.uuid4(),
                tx_type=TransactionType.BUY,
                quantity=qty,
                unit_price=price,
                trade_date=date(2026, 1, 1 + idx),
            )
            ledger.append(tx)

        pos = PositionEngine.calculate_security_position(
            portfolio_id=1, security_id=10, transactions=ledger
        )
        self.assertEqual(pos.quantity, expected_total_qty.quantize(Decimal("0.00000001")))
        self.assertEqual(pos.total_cost_basis, expected_total_cost.quantize(Decimal("0.0001")))

    @given(
        buy_qty=st.integers(min_value=50, max_value=1000),
        buy_price=st.integers(min_value=50, max_value=500),
        sell_qty=st.integers(min_value=1, max_value=49),
        sell_price=st.integers(min_value=50, max_value=600),
    )
    @settings(max_examples=40)
    def test_property_unit_cost_invariant_on_sell(
        self, buy_qty: int, buy_price: int, sell_qty: int, sell_price: int
    ) -> None:
        """Property: Executing a partial SELL never alters the unit cost basis of remaining shares."""
        b_qty = Decimal(str(buy_qty))
        b_price = Decimal(str(buy_price))
        s_qty = Decimal(str(sell_qty))
        s_price = Decimal(str(sell_price))

        tx_buy = self._make_ledger_tx(
            tx_id=uuid.uuid4(),
            tx_type=TransactionType.BUY,
            quantity=b_qty,
            unit_price=b_price,
            trade_date=date(2026, 1, 1),
        )
        pos_before_sell = PositionEngine.calculate_security_position(
            portfolio_id=1, security_id=10, transactions=[tx_buy]
        )
        unit_cost_before = pos_before_sell.unit_cost_basis

        tx_sell = self._make_ledger_tx(
            tx_id=uuid.uuid4(),
            tx_type=TransactionType.SELL,
            quantity=s_qty,
            unit_price=s_price,
            trade_date=date(2026, 1, 2),
        )
        pos_after_sell = PositionEngine.calculate_security_position(
            portfolio_id=1, security_id=10, transactions=[tx_buy, tx_sell]
        )

        # Invariant: unit cost basis remains identical
        self.assertEqual(pos_after_sell.unit_cost_basis, unit_cost_before)
        # Invariant: quantity decreased by exact sell quantity
        self.assertEqual(pos_after_sell.quantity, b_qty - s_qty)

    def test_property_reversal_identity_invariant(self) -> None:
        """Property: Appending an exact cancelling reversal restores state to net zero."""
        tx_orig_id = uuid.uuid4()
        tx_buy = self._make_ledger_tx(
            tx_id=tx_orig_id,
            tx_type=TransactionType.BUY,
            quantity=Decimal("100"),
            unit_price=Decimal("150"),
            trade_date=date(2026, 1, 5),
        )

        # Position before cancellation: 100 shares
        pos_before = PositionEngine.calculate_security_position(
            portfolio_id=1, security_id=10, transactions=[tx_buy]
        )
        self.assertEqual(pos_before.quantity, Decimal("100.00000000"))

        # Add reversal record
        tx_reversal = self._make_ledger_tx(
            tx_id=uuid.uuid4(),
            tx_type=TransactionType.BUY,
            quantity=Decimal("100"),
            unit_price=Decimal("150"),
            trade_date=date(2026, 1, 5),
            status=TransactionStatus.CANCELLED,
            original_tx_id=tx_orig_id,
        )

        # Position after cancellation: 0 shares
        pos_after = PositionEngine.calculate_security_position(
            portfolio_id=1, security_id=10, transactions=[tx_buy, tx_reversal]
        )
        self.assertEqual(pos_after.quantity, Decimal("0.00000000"))
        self.assertEqual(pos_after.total_cost_basis, Decimal("0.0000"))

    def test_property_long_only_insufficient_holdings_rejected(self) -> None:
        """Property: Sells exceeding available inventory strictly raise InsufficientHoldingsError."""
        tx_buy = self._make_ledger_tx(
            tx_id=uuid.uuid4(),
            tx_type=TransactionType.BUY,
            quantity=Decimal("50"),
            unit_price=Decimal("100"),
            trade_date=date(2026, 1, 1),
        )
        tx_illegal_sell = self._make_ledger_tx(
            tx_id=uuid.uuid4(),
            tx_type=TransactionType.SELL,
            quantity=Decimal("51"),  # Exceeds 50
            unit_price=Decimal("110"),
            trade_date=date(2026, 1, 2),
        )

        with self.assertRaises(InsufficientHoldingsError):
            PositionEngine.calculate_security_position(
                portfolio_id=1, security_id=10, transactions=[tx_buy, tx_illegal_sell]
            )


if __name__ == "__main__":
    unittest.main()
