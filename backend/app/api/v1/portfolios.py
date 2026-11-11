"""Portfolio master endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.cash_account import CashAccount
from app.models.customer import Customer
from app.models.enums import AccountType
from app.models.portfolio import Portfolio
from app.schemas.portfolio import CashAccountResponse, PortfolioCreate, PortfolioResponse

router = APIRouter(prefix="/portfolios", tags=["Portfolios"])


@router.post("", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
def create_portfolio(payload: PortfolioCreate, db: Session = Depends(get_db)) -> Portfolio:
    """Create a new portfolio and provision its default settlement cash account."""
    # Verify customer exists
    customer = db.query(Customer).filter_by(customer_id=payload.customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID {payload.customer_id} does not exist.",
        )

    # Verify unique portfolio_code
    existing = db.query(Portfolio).filter_by(portfolio_code=payload.portfolio_code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Portfolio code '{payload.portfolio_code}' already exists.",
        )

    portfolio = Portfolio(
        portfolio_code=payload.portfolio_code,
        customer_id=payload.customer_id,
        portfolio_name=payload.portfolio_name,
        base_currency=payload.base_currency.upper(),
        inception_date=payload.inception_date,
        created_by=payload.created_by,
        status="ACTIVE",
    )
    db.add(portfolio)
    db.flush()

    # Auto-provision primary settlement cash account in portfolio base currency
    default_cash = CashAccount(
        portfolio_id=portfolio.portfolio_id,
        currency=portfolio.base_currency,
        account_type=AccountType.SETTLEMENT.value,
        iban_or_account_number=f"SETTLE-{portfolio.portfolio_code}-{portfolio.base_currency}",
        created_by=payload.created_by,
    )
    db.add(default_cash)
    db.commit()
    db.refresh(portfolio)
    return portfolio


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
def get_portfolio(portfolio_id: int, db: Session = Depends(get_db)) -> Portfolio:
    """Retrieve portfolio master record by ID."""
    portfolio = db.query(Portfolio).filter_by(portfolio_id=portfolio_id).first()
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio with ID {portfolio_id} not found.",
        )
    return portfolio


@router.get("/{portfolio_id}/cash-accounts", response_model=list[CashAccountResponse])
def get_portfolio_cash_accounts(
    portfolio_id: int, db: Session = Depends(get_db)
) -> list[CashAccount]:
    """Retrieve all segregated cash accounts for a portfolio."""
    portfolio = db.query(Portfolio).filter_by(portfolio_id=portfolio_id).first()
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio with ID {portfolio_id} not found.",
        )
    return portfolio.cash_accounts
