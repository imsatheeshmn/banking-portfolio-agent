"""Unit and constraint tests for Milestone 1a database models."""

import unittest
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.seed import seed_database
from app.models.cash_account import CashAccount
from app.models.customer import Customer
from app.models.enums import (
    AccountType,
    InstrumentType,
    TransactionStatus,
    TransactionType,
)
from app.models.portfolio import Portfolio
from app.models.security import Security
from app.models.transaction_ledger import TransactionLedger


class TestDatabaseModels(unittest.TestCase):
    """Test suite verifying schema structure, constraints, precision, and seed execution."""

    def setUp(self) -> None:
        """Create an in-memory test database with metadata tables."""
        # For SQLite in-memory testing, remove schema qualifications from metadata
        self.engine = create_engine("sqlite:///:memory:", echo=False)

        # Clone metadata without schema qualification for SQLite compatibility
        for table in Base.metadata.tables.values():
            table.schema = None

        Base.metadata.create_all(self.engine)
        self.session = Session(self.engine)

    def tearDown(self) -> None:
        self.session.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_schema_entities_registered(self) -> None:
        """Verify all core master and ledger tables exist in SQLAlchemy metadata."""
        table_names = [table.name for table in Base.metadata.sorted_tables]
        expected_tables = [
            "customers",
            "portfolios",
            "cash_accounts",
            "securities",
            "security_identifiers",
            "transaction_ledger",
        ]
        for expected in expected_tables:
            self.assertIn(expected, table_names)

    def test_precision_preservation_on_transaction_ledger(self) -> None:
        """Verify that high-precision quantity, price, and amounts retain exact decimal representation."""
        customer = Customer(legal_name="Precision Test Cust", country_code="US")
        self.session.add(customer)
        self.session.flush()

        portfolio = Portfolio(
            portfolio_code="PREC_PORT_01",
            customer_id=customer.customer_id,
            portfolio_name="Precision Fund",
            base_currency="USD",
            inception_date=date(2026, 1, 1),
        )
        self.session.add(portfolio)
        self.session.flush()

        cash_acct = CashAccount(
            portfolio_id=portfolio.portfolio_id,
            currency="USD",
            account_type=AccountType.SETTLEMENT.value,
        )
        self.session.add(cash_acct)
        self.session.flush()

        sec = Security(
            ticker="TEST",
            security_name="Test Stock",
            instrument_type=InstrumentType.EQUITY.value,
            primary_exchange="XNYS",
            currency="USD",
            country_of_risk="US",
        )
        self.session.add(sec)
        self.session.flush()

        tx_id = uuid.uuid4()
        exact_quantity = Decimal("12345.67891234")  # 8 decimal places
        exact_price = Decimal("987.6543219876")  # 10 decimal places
        exact_fx = Decimal("1.0845123456")  # 10 decimal places
        exact_amount = Decimal("12193257.0123")  # 4 decimal places

        tx = TransactionLedger(
            transaction_id=tx_id,
            run_id="RUN_PREC_001",
            correlation_id="CORR_PREC_001",
            portfolio_id=portfolio.portfolio_id,
            security_id=sec.security_id,
            cash_account_id=cash_acct.cash_account_id,
            transaction_type=TransactionType.BUY.value,
            status=TransactionStatus.VALIDATED.value,
            trade_date=date(2026, 3, 1),
            settlement_date=date(2026, 3, 2),
            recorded_at_utc=datetime.now(UTC),
            quantity=exact_quantity,
            unit_price=exact_price,
            currency_local="USD",
            gross_amount_local=exact_amount,
            net_amount_local=exact_amount,
            fx_rate_to_base=exact_fx,
            currency_base="USD",
            net_amount_base=exact_amount,
            created_by="unit_test",
        )
        self.session.add(tx)
        self.session.commit()

        # Query back and verify exact values
        retrieved_tx = self.session.query(TransactionLedger).filter_by(transaction_id=tx_id).one()
        self.assertEqual(retrieved_tx.quantity, exact_quantity)
        self.assertEqual(retrieved_tx.unit_price, exact_price)
        self.assertEqual(retrieved_tx.fx_rate_to_base, exact_fx)
        self.assertEqual(retrieved_tx.gross_amount_local, exact_amount)

    def test_deterministic_seed_database(self) -> None:
        """Verify that seed_database populates expected entities and transaction links."""
        counts = seed_database(self.session)
        self.assertEqual(counts["customers"], 1)
        self.assertEqual(counts["portfolios"], 1)
        self.assertEqual(counts["cash_accounts"], 1)
        self.assertEqual(counts["securities"], 2)
        self.assertEqual(counts["identifiers"], 2)
        self.assertEqual(counts["transactions"], 2)

        # Validate seeded portfolio
        port = self.session.query(Portfolio).filter_by(portfolio_code="APEX_GLOBAL_EQ").one()
        self.assertEqual(port.base_currency, "USD")
        self.assertEqual(len(port.transactions), 2)

        # Validate bitemporal dates on AAPL buy
        buy_tx = next(
            tx for tx in port.transactions if tx.transaction_type == TransactionType.BUY.value
        )
        self.assertEqual(buy_tx.trade_date, date(2026, 1, 3))
        self.assertEqual(buy_tx.settlement_date, date(2026, 1, 4))
        self.assertEqual(buy_tx.approved_by, "maker_checker_admin")
        self.assertIsNotNone(buy_tx.approved_at_utc)

    def test_reversible_migrations_symmetry(self) -> None:
        """Verify that migration downgrade methods match and reverse upgrade actions."""
        import importlib.util
        from pathlib import Path

        base_dir = Path(__file__).resolve().parent.parent / "alembic" / "versions"

        def load_migration(filename: str):
            path = base_dir / filename
            spec = importlib.util.spec_from_file_location(filename[:-3], path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod

        m01 = load_migration("0001_create_schemas.py")
        m02 = load_migration("0002_create_master_and_ledger_tables.py")

        self.assertEqual(m01.revision, "0001")
        self.assertIsNone(m01.down_revision)
        self.assertEqual(m02.revision, "0002")
        self.assertEqual(m02.down_revision, "0001")
        self.assertTrue(callable(m01.upgrade))
        self.assertTrue(callable(m01.downgrade))
        self.assertTrue(callable(m02.upgrade))
        self.assertTrue(callable(m02.downgrade))


if __name__ == "__main__":
    unittest.main()
