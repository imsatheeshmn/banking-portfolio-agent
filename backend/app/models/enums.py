"""Domain enumerations for financial transactions and instruments."""

from enum import StrEnum


class TransactionType(StrEnum):
    """Core transaction types supported in Phase A."""

    BUY = "BUY"
    SELL = "SELL"
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    DIVIDEND = "DIVIDEND"
    FEE = "FEE"


class TransactionStatus(StrEnum):
    """Lifecycle status states for transaction processing."""

    NEW = "NEW"
    VALIDATED = "VALIDATED"
    CONFIRMED = "CONFIRMED"
    SETTLED = "SETTLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class InstrumentType(StrEnum):
    """Asset classes supported in platform phases."""

    EQUITY = "EQUITY"
    CASH = "CASH"
    BOND = "BOND"  # Phase B extension


class IdentifierType(StrEnum):
    """Security reference identifier standards."""

    ISIN = "ISIN"
    CUSIP = "CUSIP"
    SEDOL = "SEDOL"
    FIGI = "FIGI"
    TICKER = "TICKER"


class AccountType(StrEnum):
    """Cash account segregation types."""

    SETTLEMENT = "SETTLEMENT"
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"
