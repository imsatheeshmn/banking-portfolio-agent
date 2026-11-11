"""Holdings and Cash projection endpoints (IBOR & ABOR views)."""

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domain.position_engine import PositionEngine
from app.models.cash_account import CashAccount
from app.models.portfolio import Portfolio
from app.models.security import Security
from app.models.transaction_ledger import TransactionLedger
from app.schemas.position import (
    CashBalanceItemResponse,
    PortfolioCashResponse,
    PortfolioPositionsResponse,
    PositionItemResponse,
)

router = APIRouter(prefix="/portfolios", tags=["Positions & Cash"])


@router.get("/{portfolio_id}/positions", response_model=PortfolioPositionsResponse)
def get_portfolio_positions(
    portfolio_id: int,
    as_of_date: date | None = Query(
        default=None, description="Trade-date as-of valuation cut (IBOR view)"
    ),
    db: Session = Depends(get_db),
) -> PortfolioPositionsResponse:
    """Project portfolio holdings, weighted average cost basis, and realized P&L directly from the ledger."""
    portfolio = db.query(Portfolio).filter_by(portfolio_id=portfolio_id).first()
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio with ID {portfolio_id} not found.",
        )

    # Fetch all ledger transactions for this portfolio
    transactions = db.query(TransactionLedger).filter_by(portfolio_id=portfolio_id).all()

    # Distinct security IDs
    security_ids = {tx.security_id for tx in transactions if tx.security_id is not None}
    position_items: list[PositionItemResponse] = []

    for sec_id in sorted(security_ids):
        pos_view = PositionEngine.calculate_security_position(
            portfolio_id=portfolio_id,
            security_id=sec_id,
            transactions=transactions,
            as_of_date=as_of_date,
        )
        # Include if holding quantity > 0 or has realized P&L
        if pos_view.quantity > Decimal("0.0") or pos_view.realized_pnl != Decimal("0.0"):
            sec = db.query(Security).filter_by(security_id=sec_id).first()
            ticker = sec.ticker if sec else "UNKNOWN"
            sec_name = sec.security_name if sec else "Unknown Security"

            position_items.append(
                PositionItemResponse(
                    portfolio_id=portfolio_id,
                    security_id=sec_id,
                    ticker=ticker,
                    security_name=sec_name,
                    quantity=pos_view.quantity,
                    total_cost_basis=pos_view.total_cost_basis,
                    unit_cost_basis=pos_view.unit_cost_basis,
                    realized_pnl=pos_view.realized_pnl,
                    currency=pos_view.currency or portfolio.base_currency,
                )
            )

    return PortfolioPositionsResponse(
        portfolio_id=portfolio_id,
        as_of_date=(as_of_date or date.today()).isoformat(),
        positions=position_items,
    )


@router.get("/{portfolio_id}/cash", response_model=PortfolioCashResponse)
def get_portfolio_cash(
    portfolio_id: int,
    as_of_date: date | None = Query(default=None, description="Valuation cut date"),
    db: Session = Depends(get_db),
) -> PortfolioCashResponse:
    """Project committed trade-date cash and settled cash balances across all accounts."""
    portfolio = db.query(Portfolio).filter_by(portfolio_id=portfolio_id).first()
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio with ID {portfolio_id} not found.",
        )

    cash_accounts = db.query(CashAccount).filter_by(portfolio_id=portfolio_id).all()
    transactions = db.query(TransactionLedger).filter_by(portfolio_id=portfolio_id).all()

    cash_items: list[CashBalanceItemResponse] = []
    for acct in cash_accounts:
        bal_view = PositionEngine.calculate_cash_balance(
            portfolio_id=portfolio_id,
            cash_account_id=acct.cash_account_id,
            transactions=transactions,
            as_of_date=as_of_date,
        )
        cash_items.append(
            CashBalanceItemResponse(
                cash_account_id=acct.cash_account_id,
                currency=acct.currency,
                settled_balance=bal_view.settled_balance,
                committed_trade_date_balance=bal_view.committed_trade_date_balance,
            )
        )

    return PortfolioCashResponse(
        portfolio_id=portfolio_id,
        as_of_date=(as_of_date or date.today()).isoformat(),
        cash_accounts=cash_items,
    )
