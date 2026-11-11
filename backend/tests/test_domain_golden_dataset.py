"""Golden dataset test verifying exact hand-calculated investment scenarios for Milestone 1b."""

import unittest
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from app.domain.position_engine import PositionEngine
from app.models.enums import TransactionStatus, TransactionType
from app.models.transaction_ledger import TransactionLedger


class TestDomainGoldenDataset(unittest.TestCase):
    """Verifies that ledger-derived positions and WAC P&L match hand calculations exactly."""

    def setUp(self) -> None:
        self.portfolio_id = 101
        self.security_id = 501
        self.cash_account_id = 901

    def _create_tx(
        self,
        tx_type: TransactionType,
        trade_date: date,
        settlement_date: date,
        quantity: Decimal,
        unit_price: Decimal,
        gross_amount: Decimal,
    ) -> TransactionLedger:
        return TransactionLedger(
            transaction_id=uuid.uuid4(),
            run_id="RUN_GOLDEN_001",
            correlation_id=f"CORR_{trade_date.isoformat()}",
            portfolio_id=self.portfolio_id,
            security_id=self.security_id
            if tx_type in {TransactionType.BUY, TransactionType.SELL}
            else None,
            cash_account_id=self.cash_account_id,
            transaction_type=tx_type.value,
            status=TransactionStatus.SETTLED.value,
            trade_date=trade_date,
            settlement_date=settlement_date,
            recorded_at_utc=datetime.now(UTC),
            quantity=quantity,
            unit_price=unit_price,
            currency_local="USD",
            gross_amount_local=gross_amount,
            net_amount_local=gross_amount,
            fx_rate_to_base=Decimal("1.0"),
            currency_base="USD",
            net_amount_base=gross_amount,
            created_by="golden_test",
        )

    def test_complete_golden_lifecycle_scenario(self) -> None:
        """Step-by-step verification of hand-calculated portfolio lifecycle."""
        ledger: list[TransactionLedger] = []

        # Step 0: Cash Deposit ($50,000.00)
        tx_dep = self._create_tx(
            tx_type=TransactionType.DEPOSIT,
            trade_date=date(2026, 1, 2),
            settlement_date=date(2026, 1, 2),
            quantity=Decimal("0.0"),
            unit_price=Decimal("0.0"),
            gross_amount=Decimal("50000.0000"),
        )
        ledger.append(tx_dep)

        cash_v0 = PositionEngine.calculate_cash_balance(
            self.portfolio_id, self.cash_account_id, ledger
        )
        self.assertEqual(cash_v0.settled_balance, Decimal("50000.0000"))

        # Step 1: BUY Lot 1 (100 shares @ $150.00 = $15,000.00)
        tx_buy1 = self._create_tx(
            tx_type=TransactionType.BUY,
            trade_date=date(2026, 1, 5),
            settlement_date=date(2026, 1, 6),
            quantity=Decimal("100.00000000"),
            unit_price=Decimal("150.0000000000"),
            gross_amount=Decimal("15000.0000"),
        )
        ledger.append(tx_buy1)

        pos_v1 = PositionEngine.calculate_security_position(
            self.portfolio_id, self.security_id, ledger
        )
        self.assertEqual(pos_v1.quantity, Decimal("100.00000000"))
        self.assertEqual(pos_v1.total_cost_basis, Decimal("15000.0000"))
        self.assertEqual(pos_v1.unit_cost_basis, Decimal("150.0000000000"))
        self.assertEqual(pos_v1.realized_pnl, Decimal("0.0000"))

        cash_v1 = PositionEngine.calculate_cash_balance(
            self.portfolio_id, self.cash_account_id, ledger
        )
        self.assertEqual(cash_v1.committed_trade_date_balance, Decimal("35000.0000"))

        # Step 2: BUY Lot 2 (50 shares @ $180.00 = $9,000.00)
        tx_buy2 = self._create_tx(
            tx_type=TransactionType.BUY,
            trade_date=date(2026, 1, 10),
            settlement_date=date(2026, 1, 11),
            quantity=Decimal("50.00000000"),
            unit_price=Decimal("180.0000000000"),
            gross_amount=Decimal("9000.0000"),
        )
        ledger.append(tx_buy2)

        pos_v2 = PositionEngine.calculate_security_position(
            self.portfolio_id, self.security_id, ledger
        )
        self.assertEqual(pos_v2.quantity, Decimal("150.00000000"))
        self.assertEqual(pos_v2.total_cost_basis, Decimal("24000.0000"))
        self.assertEqual(
            pos_v2.unit_cost_basis, Decimal("160.0000000000")
        )  # $24,000 / 150 = $160.00

        # Step 3: SELL Partial (60 shares @ $200.00 = $12,000.00 proceeds)
        # Disposed Cost = 60 * $160 = $9,600. Realized P&L = $12,000 - $9,600 = +$2,400.
        # Remaining Qty = 90. Remaining Total Cost = $24,000 - $9,600 = $14,400.
        tx_sell1 = self._create_tx(
            tx_type=TransactionType.SELL,
            trade_date=date(2026, 1, 15),
            settlement_date=date(2026, 1, 16),
            quantity=Decimal("60.00000000"),
            unit_price=Decimal("200.0000000000"),
            gross_amount=Decimal("12000.0000"),
        )
        ledger.append(tx_sell1)

        pos_v3 = PositionEngine.calculate_security_position(
            self.portfolio_id, self.security_id, ledger
        )
        self.assertEqual(pos_v3.quantity, Decimal("90.00000000"))
        self.assertEqual(pos_v3.total_cost_basis, Decimal("14400.0000"))
        self.assertEqual(
            pos_v3.unit_cost_basis, Decimal("160.0000000000")
        )  # INVARIANT: Unit cost unchanged
        self.assertEqual(pos_v3.realized_pnl, Decimal("2400.0000"))

        cash_v3 = PositionEngine.calculate_cash_balance(
            self.portfolio_id, self.cash_account_id, ledger
        )
        self.assertEqual(cash_v3.committed_trade_date_balance, Decimal("38000.0000"))

        # Step 4: BUY Lot 3 (30 shares @ $120.00 = $3,600.00)
        # New Qty = 90 + 30 = 120. New Cost = $14,400 + $3,600 = $18,000.
        # New Avg Cost = $18,000 / 120 = $150.00
        tx_buy3 = self._create_tx(
            tx_type=TransactionType.BUY,
            trade_date=date(2026, 1, 20),
            settlement_date=date(2026, 1, 21),
            quantity=Decimal("30.00000000"),
            unit_price=Decimal("120.0000000000"),
            gross_amount=Decimal("3600.0000"),
        )
        ledger.append(tx_buy3)

        pos_v4 = PositionEngine.calculate_security_position(
            self.portfolio_id, self.security_id, ledger
        )
        self.assertEqual(pos_v4.quantity, Decimal("120.00000000"))
        self.assertEqual(pos_v4.total_cost_basis, Decimal("18000.0000"))
        self.assertEqual(pos_v4.unit_cost_basis, Decimal("150.0000000000"))

        # Step 5: SELL Full Remaining Position (120 shares @ $170.00 = $20,400.00)
        # Disposed Cost = 120 * $150.00 = $18,000.00
        # Realized P&L on step 5 = $20,400.00 - $18,000.00 = +$2,400.00
        # Cumulative Realized P&L = $2,400 (from step 3) + $2,400 (from step 5) = +$4,800.00
        # Ending cash = $34,400 + $20,400 = $54,800.00 (Net Gain: $4,800 over initial $50k)
        tx_sell2 = self._create_tx(
            tx_type=TransactionType.SELL,
            trade_date=date(2026, 1, 25),
            settlement_date=date(2026, 1, 26),
            quantity=Decimal("120.00000000"),
            unit_price=Decimal("170.0000000000"),
            gross_amount=Decimal("20400.0000"),
        )
        ledger.append(tx_sell2)

        pos_v5 = PositionEngine.calculate_security_position(
            self.portfolio_id, self.security_id, ledger
        )
        self.assertEqual(pos_v5.quantity, Decimal("0.00000000"))
        self.assertEqual(pos_v5.total_cost_basis, Decimal("0.0000"))
        self.assertEqual(pos_v5.unit_cost_basis, Decimal("0.0000000000"))
        self.assertEqual(pos_v5.realized_pnl, Decimal("4800.0000"))

        cash_v5 = PositionEngine.calculate_cash_balance(
            self.portfolio_id, self.cash_account_id, ledger
        )
        self.assertEqual(cash_v5.committed_trade_date_balance, Decimal("54800.0000"))


if __name__ == "__main__":
    unittest.main()
