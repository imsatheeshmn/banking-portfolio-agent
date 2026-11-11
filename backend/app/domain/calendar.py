"""Business day calendar and settlement cycle utilities (ADR-005)."""

from datetime import date, timedelta


class BusinessCalendar:
    """Standard financial business day calendar with weekday settlement rolling."""

    @staticmethod
    def is_business_day(check_date: date) -> bool:
        """Determines if a date falls on a Monday through Friday business day."""
        return check_date.weekday() < 5

    @classmethod
    def add_business_days(cls, start_date: date, offset_days: int) -> date:
        """Adds business days, skipping Saturday and Sunday (Modified Following)."""
        current_date = start_date
        added = 0
        step = 1 if offset_days >= 0 else -1
        target = abs(offset_days)

        while added < target:
            current_date += timedelta(days=step)
            if cls.is_business_day(current_date):
                added += 1

        return current_date

    @classmethod
    def calculate_settlement_date(cls, trade_date: date, cycle_offset: int = 1) -> date:
        """Calculates standard T+n settlement date from trade date (default: T+1)."""
        if not cls.is_business_day(trade_date):
            # Roll forward to next business day first
            while not cls.is_business_day(trade_date):
                trade_date += timedelta(days=1)
        return cls.add_business_days(trade_date, cycle_offset)
