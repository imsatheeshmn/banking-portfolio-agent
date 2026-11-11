"""Transaction lifecycle state machine and allowed transitions."""

from typing import ClassVar

from app.domain.exceptions import InvalidStateTransitionError
from app.models.enums import TransactionStatus


class TransactionStateMachine:
    """Enforces allowed lifecycle state transitions for financial transactions."""

    # Explicit allowed state transition map
    _ALLOWED_TRANSITIONS: ClassVar[dict[TransactionStatus, set[TransactionStatus]]] = {
        TransactionStatus.NEW: {
            TransactionStatus.VALIDATED,
            TransactionStatus.REJECTED,
        },
        TransactionStatus.VALIDATED: {
            TransactionStatus.CONFIRMED,
            TransactionStatus.REJECTED,
        },
        TransactionStatus.CONFIRMED: {
            TransactionStatus.SETTLED,
            TransactionStatus.REJECTED,
        },
        TransactionStatus.SETTLED: set(),
        TransactionStatus.CANCELLED: set(),
        TransactionStatus.REJECTED: set(),
    }

    @classmethod
    def can_transition(cls, from_status: TransactionStatus, to_status: TransactionStatus) -> bool:
        """Checks if a transition between two statuses is permitted."""
        return to_status in cls._ALLOWED_TRANSITIONS.get(from_status, set())

    @classmethod
    def transition(
        cls, current_status: TransactionStatus, next_status: TransactionStatus
    ) -> TransactionStatus:
        """Transitions state or raises InvalidStateTransitionError."""
        if not cls.can_transition(current_status, next_status):
            raise InvalidStateTransitionError(current_status.value, next_status.value)
        return next_status
