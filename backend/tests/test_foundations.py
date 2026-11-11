"""Foundations smoke test for Milestone 0.

Compatible with both unittest (standard library) and pytest (CI/CD).
Verifies decimal precision requirements and basic test harness.
"""
import unittest
from decimal import Decimal, ROUND_HALF_UP


class TestFoundations(unittest.TestCase):
    def test_python_foundations_baseline(self) -> None:
        """Validate baseline Python execution and arithmetic guarantees."""
        self.assertEqual(1 + 1, 2)

    def test_financial_decimal_precision_invariants(self) -> None:
        """Verify that financial precision invariants follow Decimal rules rather than float.
        
        IEEE 754 floats have representation drift (0.1 + 0.2 != 0.3).
        Financial decimals must maintain exact base-10 representation.
        """
        f1 = 0.1
        f2 = 0.2
        self.assertNotEqual(f1 + f2, 0.3)  # Demonstrates why float is forbidden for money

        d1 = Decimal("0.1")
        d2 = Decimal("0.2")
        self.assertEqual(d1 + d2, Decimal("0.3"))

    def test_rounding_half_up_behavior(self) -> None:
        """Verify standard financial ROUND_HALF_UP behavior on currency amounts."""
        amount_up = Decimal("100.555").quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        self.assertEqual(amount_up, Decimal("100.56"))

        amount_down = Decimal("100.554").quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        self.assertEqual(amount_down, Decimal("100.55"))


if __name__ == "__main__":
    unittest.main()
