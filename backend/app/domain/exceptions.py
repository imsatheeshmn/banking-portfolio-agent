"""Domain exceptions and financial error reason codes."""


class DomainError(Exception):
    """Base class for all investment domain exceptions."""

    def __init__(self, message: str, code: str) -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class InsufficientHoldingsError(DomainError):
    """Raised when a SELL transaction exceeds current long-only position holdings (ADR-003)."""

    def __init__(
        self, portfolio_id: int, security_id: int, requested_qty: str, available_qty: str
    ) -> None:
        super().__init__(
            f"Insufficient holdings in portfolio {portfolio_id} for security {security_id}. "
            f"Requested: {requested_qty}, Available: {available_qty}.",
            code="ERR_INSUFFICIENT_HOLDINGS",
        )
        self.portfolio_id = portfolio_id
        self.security_id = security_id


class InvalidStateTransitionError(DomainError):
    """Raised when an illegal transaction state transition is attempted."""

    def __init__(self, from_status: str, to_status: str) -> None:
        super().__init__(
            f"Illegal transaction state transition from {from_status} to {to_status}.",
            code="ERR_ILLEGAL_STATE_TRANSITION",
        )


class ValidationError(DomainError):
    """Raised when transaction attributes violate domain invariants."""

    def __init__(self, message: str, code: str = "ERR_VALIDATION_FAILURE") -> None:
        super().__init__(message, code=code)


class StalePriceError(DomainError):
    """Raised when pricing is older than allowed staleness threshold."""

    def __init__(self, security_id: int, staleness_days: int) -> None:
        super().__init__(
            f"Market price for security {security_id} is stale by {staleness_days} days. Exceeds max tolerance.",
            code="ERR_STALE_PRICE",
        )
