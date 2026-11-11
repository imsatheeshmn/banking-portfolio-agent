"""Ledger-derived position, cost basis, and P&L calculation engine (ADR-002, ADR-003)."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from app.domain.exceptions import InsufficientHoldingsError
from app.models.enums import TransactionStatus, TransactionType
from app.models.transaction_ledger import TransactionLedger


@dataclass(frozen=True)
class PositionView:
    """Immutable view of a security position derived from the ledger."""

    portfolio_id: int
    security_id: int
    quantity: Decimal
    total_cost_basis: Decimal
    unit_cost_basis: Decimal
    realized_pnl: Decimal
    currency: str


@dataclass(frozen=True)
class CashBalanceView:
    """Immutable view of a cash account balance derived from the ledger."""

    portfolio_id: int
    cash_account_id: int
    currency: str
    settled_balance: Decimal
    committed_trade_date_balance: Decimal


class PositionEngine:
    """Calculates position holdings, weighted average cost basis, and cash balances from the ledger."""

    # Precision quantizers
    _QTY_QUANTIZE = Decimal("0.00000001")
    _PRICE_QUANTIZE = Decimal("0.0000000001")
    _AMT_QUANTIZE = Decimal("0.0001")

    @classmethod
    def calculate_security_position(
        cls,
        portfolio_id: int,
        security_id: int,
        transactions: Sequence[TransactionLedger],
        as_of_date: date | None = None,
    ) -> PositionView:
        """Projects current position and weighted average cost for a specific security.

        Evaluated along Trade Date (IBOR view). Replays chronological transactions.
        Cancelled reversal pairs are excluded from cumulative inventory.
        """
        # Filter transactions for target portfolio and security up to as_of_date
        relevant_txs = [
            tx
            for tx in transactions
            if tx.portfolio_id == portfolio_id
            and tx.security_id == security_id
            and tx.status != TransactionStatus.REJECTED.value
            and (as_of_date is None or tx.trade_date <= as_of_date)
        ]

        # Identify cancelled transactions to omit them and their paired reversals
        cancelled_ids = {
            tx.original_transaction_id
            for tx in relevant_txs
            if tx.status == TransactionStatus.CANCELLED.value
            and tx.original_transaction_id is not None
        }

        active_txs = [
            tx
            for tx in relevant_txs
            if tx.transaction_id not in cancelled_ids
            and tx.status != TransactionStatus.CANCELLED.value
        ]

        # Sort chronologically by trade_date, then recorded_at_utc
        active_txs.sort(key=lambda t: (t.trade_date, t.recorded_at_utc))

        current_qty = Decimal("0.0")
        current_total_cost = Decimal("0.0")
        current_unit_cost = Decimal("0.0")
        cumulative_realized_pnl = Decimal("0.0")
        currency = ""

        for tx in active_txs:
            currency = tx.currency_local
            if tx.transaction_type == TransactionType.BUY.value:
                # Acquisition: increase quantity and total cost
                trade_gross = tx.gross_amount_local
                new_qty = current_qty + tx.quantity
                new_total_cost = current_total_cost + trade_gross

                current_qty = new_qty
                current_total_cost = new_total_cost
                if current_qty > Decimal("0.0"):
                    current_unit_cost = (current_total_cost / current_qty).quantize(
                        cls._PRICE_QUANTIZE, rounding=ROUND_HALF_UP
                    )

            elif tx.transaction_type == TransactionType.SELL.value:
                # Long-only validation check (ADR-003)
                if tx.quantity > current_qty:
                    raise InsufficientHoldingsError(
                        portfolio_id=portfolio_id,
                        security_id=security_id,
                        requested_qty=str(tx.quantity),
                        available_qty=str(current_qty),
                    )

                # Disposal at current weighted average cost (ADR-002)
                cost_of_sold_shares = (tx.quantity * current_unit_cost).quantize(
                    cls._AMT_QUANTIZE, rounding=ROUND_HALF_UP
                )
                trade_proceeds = tx.gross_amount_local

                realized_pnl = (trade_proceeds - cost_of_sold_shares).quantize(
                    cls._AMT_QUANTIZE, rounding=ROUND_HALF_UP
                )
                cumulative_realized_pnl += realized_pnl

                current_qty -= tx.quantity
                current_total_cost -= cost_of_sold_shares

                if current_qty == Decimal("0.0"):
                    current_total_cost = Decimal("0.0")
                    current_unit_cost = Decimal("0.0")
                else:
                    # Unit cost remains invariant on disposal
                    current_total_cost = (current_qty * current_unit_cost).quantize(
                        cls._AMT_QUANTIZE, rounding=ROUND_HALF_UP
                    )

        return PositionView(
            portfolio_id=portfolio_id,
            security_id=security_id,
            quantity=current_qty.quantize(cls._QTY_QUANTIZE),
            total_cost_basis=current_total_cost.quantize(cls._AMT_QUANTIZE),
            unit_cost_basis=current_unit_cost.quantize(cls._PRICE_QUANTIZE),
            realized_pnl=cumulative_realized_pnl.quantize(cls._AMT_QUANTIZE),
            currency=currency,
        )

    @classmethod
    def calculate_cash_balance(
        cls,
        portfolio_id: int,
        cash_account_id: int,
        transactions: Sequence[TransactionLedger],
        as_of_date: date | None = None,
    ) -> CashBalanceView:
        """Projects settled and committed trade-date cash balances (ADR-005)."""
        relevant_txs = [
            tx
            for tx in transactions
            if tx.portfolio_id == portfolio_id
            and tx.cash_account_id == cash_account_id
            and tx.status != TransactionStatus.REJECTED.value
        ]

        # Identify cancellations
        cancelled_ids = {
            tx.original_transaction_id
            for tx in relevant_txs
            if tx.status == TransactionStatus.CANCELLED.value
            and tx.original_transaction_id is not None
        }

        active_txs = [
            tx
            for tx in relevant_txs
            if tx.transaction_id not in cancelled_ids
            and tx.status != TransactionStatus.CANCELLED.value
        ]

        settled_balance = Decimal("0.0")
        committed_balance = Decimal("0.0")
        currency = ""

        for tx in active_txs:
            currency = tx.currency_local

            # Determine cash flow sign
            if tx.transaction_type in {
                TransactionType.DEPOSIT.value,
                TransactionType.SELL.value,
                TransactionType.DIVIDEND.value,
            }:
                cash_delta = tx.net_amount_local
            elif tx.transaction_type in {
                TransactionType.WITHDRAWAL.value,
                TransactionType.BUY.value,
                TransactionType.FEE.value,
            }:
                cash_delta = -tx.net_amount_local
            else:
                cash_delta = Decimal("0.0")

            # Trade date view (IBOR committed cash)
            if as_of_date is None or tx.trade_date <= as_of_date:
                committed_balance += cash_delta

            # Settlement date view (ABOR settled cash)
            if tx.status == TransactionStatus.SETTLED.value and (
                as_of_date is None or tx.settlement_date <= as_of_date
            ):
                settled_balance += cash_delta

        return CashBalanceView(
            portfolio_id=portfolio_id,
            cash_account_id=cash_account_id,
            currency=currency,
            settled_balance=settled_balance.quantize(cls._AMT_QUANTIZE),
            committed_trade_date_balance=committed_balance.quantize(cls._AMT_QUANTIZE),
        )
