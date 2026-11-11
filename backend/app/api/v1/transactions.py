"""Transaction ledger booking and retrieval endpoints."""

import uuid
from decimal import ROUND_HALF_UP, Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domain.calendar import BusinessCalendar
from app.domain.exceptions import InsufficientHoldingsError, ValidationError
from app.domain.position_engine import PositionEngine
from app.domain.validator import TransactionValidator
from app.models.cash_account import CashAccount
from app.models.enums import TransactionStatus, TransactionType
from app.models.portfolio import Portfolio
from app.models.security import Security
from app.models.transaction_ledger import TransactionLedger
from app.schemas.transaction import TransactionCreate, TransactionResponse

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def book_transaction(
    payload: TransactionCreate, db: Session = Depends(get_db)
) -> TransactionLedger:
    """Book a validated, immutable ledger transaction.

    Enforces in-flight schema validation, long-only position inventory checks (ADR-003),
    business calendar settlement rolling (ADR-005), and multi-currency conversion (ADR-004).
    """
    # 1. Verify Portfolio and Cash Account exist
    portfolio = db.query(Portfolio).filter_by(portfolio_id=payload.portfolio_id).first()
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio with ID {payload.portfolio_id} does not exist.",
        )

    cash_acct = db.query(CashAccount).filter_by(cash_account_id=payload.cash_account_id).first()
    if not cash_acct or cash_acct.portfolio_id != payload.portfolio_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cash account {payload.cash_account_id} not found in portfolio {payload.portfolio_id}.",
        )

    # 2. Verify Security if applicable
    if payload.transaction_type in {TransactionType.BUY, TransactionType.SELL}:
        if not payload.security_id:
            raise ValidationError(
                "security_id is mandatory for BUY/SELL transactions.", code="ERR_MISSING_SECURITY"
            )
        sec = db.query(Security).filter_by(security_id=payload.security_id).first()
        if not sec:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Security with ID {payload.security_id} not found.",
            )

    # 3. Calculate Settlement Date if not explicitly provided
    settlement_date = payload.settlement_date or BusinessCalendar.calculate_settlement_date(
        trade_date=payload.trade_date, cycle_offset=1
    )

    # 4. In-flight Domain Validation (ADR-001, ADR-005)
    validation = TransactionValidator.validate_transaction(
        tx_type=payload.transaction_type,
        quantity=payload.quantity,
        unit_price=payload.unit_price,
        currency_local=payload.currency_local,
        currency_base=portfolio.base_currency,
        fx_rate_to_base=payload.fx_rate_to_base,
        trade_date=payload.trade_date,
        settlement_date=settlement_date,
    )
    if not validation.is_valid:
        raise ValidationError(
            validation.error_message or "Validation failed",
            code=validation.error_code or "ERR_VALIDATION",
        )

    # 5. Long-Only Position Check on SELL (ADR-003)
    if payload.transaction_type == TransactionType.SELL and payload.security_id:
        historical_txs = (
            db.query(TransactionLedger)
            .filter_by(portfolio_id=payload.portfolio_id, security_id=payload.security_id)
            .all()
        )
        current_pos = PositionEngine.calculate_security_position(
            portfolio_id=payload.portfolio_id,
            security_id=payload.security_id,
            transactions=historical_txs,
            as_of_date=payload.trade_date,
        )
        if payload.quantity > current_pos.quantity:
            raise InsufficientHoldingsError(
                portfolio_id=payload.portfolio_id,
                security_id=payload.security_id,
                requested_qty=str(payload.quantity),
                available_qty=str(current_pos.quantity),
            )

    # 6. Exact Monetary Quantization (ADR-001, ADR-004)
    amt_quantize = Decimal("0.0001")
    gross_amount = payload.gross_amount_local.quantize(amt_quantize)
    net_local = (
        payload.net_amount_local.quantize(amt_quantize)
        if payload.net_amount_local is not None
        else gross_amount
    )
    net_base = (net_local / payload.fx_rate_to_base).quantize(amt_quantize, rounding=ROUND_HALF_UP)

    # 7. Create Immutable Ledger Entry
    ledger_entry = TransactionLedger(
        transaction_id=uuid.uuid4(),
        run_id=payload.run_id,
        correlation_id=payload.correlation_id,
        portfolio_id=payload.portfolio_id,
        security_id=payload.security_id,
        cash_account_id=payload.cash_account_id,
        transaction_type=payload.transaction_type.value,
        status=TransactionStatus.SETTLED.value,  # Settled or validated
        trade_date=payload.trade_date,
        settlement_date=settlement_date,
        quantity=payload.quantity,
        unit_price=payload.unit_price,
        currency_local=payload.currency_local.upper(),
        gross_amount_local=gross_amount,
        net_amount_local=net_local,
        fx_rate_to_base=payload.fx_rate_to_base,
        currency_base=portfolio.base_currency,
        net_amount_base=net_base,
        created_by=payload.created_by,
    )
    db.add(ledger_entry)
    db.commit()
    db.refresh(ledger_entry)
    return ledger_entry


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(transaction_id: uuid.UUID, db: Session = Depends(get_db)) -> TransactionLedger:
    """Retrieve an immutable transaction record by UUID."""
    tx = db.query(TransactionLedger).filter_by(transaction_id=transaction_id).first()
    if not tx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with ID {transaction_id} not found.",
        )
    return tx


@router.get("", response_model=list[TransactionResponse])
def list_transactions(
    portfolio_id: int = Query(..., description="Target portfolio ID"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> list[TransactionLedger]:
    """List ledger transactions for a portfolio."""
    return (
        db.query(TransactionLedger)
        .filter_by(portfolio_id=portfolio_id)
        .order_by(TransactionLedger.trade_date.asc(), TransactionLedger.recorded_at_utc.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )
