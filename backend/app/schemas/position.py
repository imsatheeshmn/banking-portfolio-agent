"""Holdings and Cash Balance projection schemas."""

from decimal import Decimal

from pydantic import BaseModel


class PositionItemResponse(BaseModel):
    """Holding position item projected from the ledger."""

    portfolio_id: int
    security_id: int
    ticker: str
    security_name: str
    quantity: Decimal
    total_cost_basis: Decimal
    unit_cost_basis: Decimal
    realized_pnl: Decimal
    currency: str


class PortfolioPositionsResponse(BaseModel):
    """Complete portfolio positions response."""

    portfolio_id: int
    as_of_date: str
    positions: list[PositionItemResponse]


class CashBalanceItemResponse(BaseModel):
    """Cash balance item projected from the ledger."""

    cash_account_id: int
    currency: str
    settled_balance: Decimal
    committed_trade_date_balance: Decimal


class PortfolioCashResponse(BaseModel):
    """Complete portfolio cash accounts response."""

    portfolio_id: int
    as_of_date: str
    cash_accounts: list[CashBalanceItemResponse]
