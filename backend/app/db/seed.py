"""Deterministic seed data loader for development and testing environments."""

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.cash_account import CashAccount
from app.models.customer import Customer
from app.models.enums import (
    AccountType,
    IdentifierType,
    InstrumentType,
    TransactionStatus,
    TransactionType,
)
from app.models.portfolio import Portfolio
from app.models.security import Security
from app.models.security_identifier import SecurityIdentifier
from app.models.transaction_ledger import TransactionLedger


def seed_database(session: Session) -> dict[str, int]:
    """Deterministically populates master records and initial transactions.

    Idempotent: skips seeding if customer already exists.
    """
    # 1. Seed Customer
    existing_cust = (
        session.query(Customer).filter_by(legal_name="Apex Global Wealth Management").first()
    )
    if existing_cust:
        return {"status": 0, "message": "Already seeded"}

    customer = Customer(
        legal_name="Apex Global Wealth Management",
        country_code="US",
        status="ACTIVE",
        created_by="seed_script",
    )
    session.add(customer)
    session.flush()

    # 2. Seed Portfolio
    portfolio = Portfolio(
        portfolio_code="APEX_GLOBAL_EQ",
        customer_id=customer.customer_id,
        portfolio_name="Apex Global Equity Strategy",
        base_currency="USD",
        inception_date=date(2026, 1, 1),
        status="ACTIVE",
        created_by="seed_script",
    )
    session.add(portfolio)
    session.flush()

    # 3. Seed Cash Account
    cash_account = CashAccount(
        portfolio_id=portfolio.portfolio_id,
        currency="USD",
        account_type=AccountType.SETTLEMENT.value,
        iban_or_account_number="US99APEX000123456789",
        created_by="seed_script",
    )
    session.add(cash_account)
    session.flush()

    # 4. Seed Securities
    sec_aapl = Security(
        ticker="AAPL",
        security_name="Apple Inc.",
        instrument_type=InstrumentType.EQUITY.value,
        primary_exchange="XNAS",
        currency="USD",
        country_of_risk="US",
        created_by="seed_script",
    )
    sec_msft = Security(
        ticker="MSFT",
        security_name="Microsoft Corporation",
        instrument_type=InstrumentType.EQUITY.value,
        primary_exchange="XNAS",
        currency="USD",
        country_of_risk="US",
        created_by="seed_script",
    )
    session.add_all([sec_aapl, sec_msft])
    session.flush()

    # 5. Seed Identifiers
    id_aapl = SecurityIdentifier(
        security_id=sec_aapl.security_id,
        identifier_type=IdentifierType.ISIN.value,
        identifier_value="US0378331005",
        created_by="seed_script",
    )
    id_msft = SecurityIdentifier(
        security_id=sec_msft.security_id,
        identifier_type=IdentifierType.ISIN.value,
        identifier_value="US5949181045",
        created_by="seed_script",
    )
    session.add_all([id_aapl, id_msft])
    session.flush()

    # 6. Seed Initial Transactions
    # Tx 1: Cash Deposit ($1,000,000.00 USD)
    tx_deposit = TransactionLedger(
        transaction_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        run_id="RUN_SEED_001",
        correlation_id="CORR_DEP_001",
        portfolio_id=portfolio.portfolio_id,
        security_id=None,
        cash_account_id=cash_account.cash_account_id,
        transaction_type=TransactionType.DEPOSIT.value,
        status=TransactionStatus.SETTLED.value,
        trade_date=date(2026, 1, 2),
        settlement_date=date(2026, 1, 2),
        recorded_at_utc=datetime(2026, 1, 2, 9, 0, 0, tzinfo=UTC),
        quantity=Decimal("0.0"),
        unit_price=Decimal("0.0"),
        currency_local="USD",
        gross_amount_local=Decimal("1000000.0000"),
        net_amount_local=Decimal("1000000.0000"),
        fx_rate_to_base=Decimal("1.0000000000"),
        currency_base="USD",
        net_amount_base=Decimal("1000000.0000"),
        created_by="seed_script",
        approved_by="maker_checker_admin",
        approved_at_utc=datetime(2026, 1, 2, 9, 5, 0, tzinfo=UTC),
    )

    # Tx 2: Buy AAPL (1,000 shares @ $185.5000000000)
    tx_buy_aapl = TransactionLedger(
        transaction_id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
        run_id="RUN_SEED_001",
        correlation_id="CORR_BUY_AAPL_001",
        portfolio_id=portfolio.portfolio_id,
        security_id=sec_aapl.security_id,
        cash_account_id=cash_account.cash_account_id,
        transaction_type=TransactionType.BUY.value,
        status=TransactionStatus.SETTLED.value,
        trade_date=date(2026, 1, 3),
        settlement_date=date(2026, 1, 4),
        recorded_at_utc=datetime(2026, 1, 3, 14, 30, 0, tzinfo=UTC),
        quantity=Decimal("1000.00000000"),
        unit_price=Decimal("185.5000000000"),
        currency_local="USD",
        gross_amount_local=Decimal("185500.0000"),
        net_amount_local=Decimal("185500.0000"),
        fx_rate_to_base=Decimal("1.0000000000"),
        currency_base="USD",
        net_amount_base=Decimal("185500.0000"),
        created_by="seed_script",
        approved_by="maker_checker_admin",
        approved_at_utc=datetime(2026, 1, 3, 14, 35, 0, tzinfo=UTC),
    )

    session.add_all([tx_deposit, tx_buy_aapl])
    session.commit()

    return {
        "customers": 1,
        "portfolios": 1,
        "cash_accounts": 1,
        "securities": 2,
        "identifiers": 2,
        "transactions": 2,
    }
