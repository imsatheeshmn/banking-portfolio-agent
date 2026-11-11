"""Integration tests for FastAPI v1 endpoints and RFC 7807 error contracts."""

import unittest
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app


class TestApiV1Integration(unittest.TestCase):
    """End-to-end operational integration test suite using FastAPI TestClient."""

    def setUp(self) -> None:
        """Create a shared in-memory SQLite database and override get_db dependency."""
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False,
        )
        for table in Base.metadata.tables.values():
            table.schema = None
        Base.metadata.create_all(self.engine)

        self.TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        def override_get_db():
            db = self.TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_health_check_endpoint(self) -> None:
        """Verify GET /health probe returns 200 OK."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")

    def test_end_to_end_operational_flow(self) -> None:
        """Verify complete lifecycle: Customer -> Portfolio -> Security -> Deposit -> Buy -> Sell -> Holdings."""
        # 1. Create Customer
        cust_resp = self.client.post(
            "/api/v1/customers",
            json={
                "legal_name": "Horizon Asset Management AG",
                "country_code": "CH",
                "created_by": "api_test",
            },
        )
        self.assertEqual(cust_resp.status_code, 201)
        customer = cust_resp.json()
        cust_id = customer["customer_id"]
        self.assertEqual(customer["country_code"], "CH")

        # 2. Create Portfolio
        port_resp = self.client.post(
            "/api/v1/portfolios",
            json={
                "portfolio_code": "HORIZON_GLOBAL_EQ",
                "customer_id": cust_id,
                "portfolio_name": "Horizon Global Equity Mandate",
                "base_currency": "USD",
                "inception_date": "2026-01-01",
                "created_by": "api_test",
            },
        )
        self.assertEqual(port_resp.status_code, 201)
        portfolio = port_resp.json()
        port_id = portfolio["portfolio_id"]
        self.assertEqual(portfolio["base_currency"], "USD")
        self.assertEqual(len(portfolio["cash_accounts"]), 1)
        cash_acct_id = portfolio["cash_accounts"][0]["cash_account_id"]

        # 3. Create Security (Apple Inc.) with ISIN identifier
        sec_resp = self.client.post(
            "/api/v1/securities",
            json={
                "ticker": "AAPL",
                "security_name": "Apple Inc.",
                "instrument_type": "EQUITY",
                "primary_exchange": "XNAS",
                "currency": "USD",
                "country_of_risk": "US",
                "identifiers": [
                    {
                        "identifier_type": "ISIN",
                        "identifier_value": "US0378331005",
                        "valid_from": "1980-12-12",
                    }
                ],
            },
        )
        self.assertEqual(sec_resp.status_code, 201)
        sec = sec_resp.json()
        sec_id = sec["security_id"]
        self.assertEqual(sec["ticker"], "AAPL")
        self.assertEqual(sec["identifiers"][0]["identifier_value"], "US0378331005")

        # 4. Book Cash Deposit ($100,000.00 USD)
        dep_resp = self.client.post(
            "/api/v1/transactions",
            json={
                "portfolio_id": port_id,
                "cash_account_id": cash_acct_id,
                "transaction_type": "DEPOSIT",
                "quantity": "0.0",
                "unit_price": "0.0",
                "currency_local": "USD",
                "gross_amount_local": "100000.0000",
                "fx_rate_to_base": "1.0",
                "trade_date": "2026-01-02",
                "correlation_id": "DEP-001",
            },
        )
        self.assertEqual(dep_resp.status_code, 201)

        # 5. Book BUY Transaction (100 shares @ $150.00 = $15,000.00)
        buy_resp = self.client.post(
            "/api/v1/transactions",
            json={
                "portfolio_id": port_id,
                "security_id": sec_id,
                "cash_account_id": cash_acct_id,
                "transaction_type": "BUY",
                "quantity": "100.00000000",
                "unit_price": "150.0000000000",
                "currency_local": "USD",
                "gross_amount_local": "15000.0000",
                "fx_rate_to_base": "1.0",
                "trade_date": "2026-01-05",
                "correlation_id": "BUY-AAPL-001",
            },
        )
        self.assertEqual(buy_resp.status_code, 201)
        tx_buy = buy_resp.json()
        self.assertEqual(tx_buy["settlement_date"], "2026-01-06")  # Auto T+1

        # 6. Verify Initial Position Holdings (100 shares @ $150.00)
        pos_resp = self.client.get(f"/api/v1/portfolios/{port_id}/positions")
        self.assertEqual(pos_resp.status_code, 200)
        pos_data = pos_resp.json()
        self.assertEqual(len(pos_data["positions"]), 1)
        item = pos_data["positions"][0]
        self.assertEqual(Decimal(str(item["quantity"])), Decimal("100.00000000"))
        self.assertEqual(Decimal(str(item["unit_cost_basis"])), Decimal("150.0000000000"))
        self.assertEqual(Decimal(str(item["realized_pnl"])), Decimal("0.0000"))

        # 7. Book Partial SELL (40 shares @ $200.00 = $8,000.00 proceeds)
        # Cost of sold = 40 * $150 = $6,000. Realized P&L = $8,000 - $6,000 = +$2,000.00
        sell_resp = self.client.post(
            "/api/v1/transactions",
            json={
                "portfolio_id": port_id,
                "security_id": sec_id,
                "cash_account_id": cash_acct_id,
                "transaction_type": "SELL",
                "quantity": "40.00000000",
                "unit_price": "200.0000000000",
                "currency_local": "USD",
                "gross_amount_local": "8000.0000",
                "fx_rate_to_base": "1.0",
                "trade_date": "2026-01-10",
                "correlation_id": "SELL-AAPL-001",
            },
        )
        self.assertEqual(sell_resp.status_code, 201)

        # 8. Verify Remaining Holdings & Realized P&L
        pos_resp2 = self.client.get(f"/api/v1/portfolios/{port_id}/positions")
        self.assertEqual(pos_resp2.status_code, 200)
        pos_data2 = pos_resp2.json()
        item2 = pos_data2["positions"][0]
        self.assertEqual(Decimal(str(item2["quantity"])), Decimal("60.00000000"))
        self.assertEqual(
            Decimal(str(item2["unit_cost_basis"])), Decimal("150.0000000000")
        )  # Invariant!
        self.assertEqual(Decimal(str(item2["realized_pnl"])), Decimal("2000.0000"))

        # 9. Verify Cash Account Balance
        cash_resp = self.client.get(f"/api/v1/portfolios/{port_id}/cash")
        self.assertEqual(cash_resp.status_code, 200)
        cash_data = cash_resp.json()
        cash_bal = cash_data["cash_accounts"][0]
        # $100,000 - $15,000 + $8,000 = $93,000.00
        self.assertEqual(
            Decimal(str(cash_bal["committed_trade_date_balance"])), Decimal("93000.0000")
        )

    def test_negative_long_only_insufficient_holdings_rfc7807(self) -> None:
        """Verify that attempting to sell more than held inventory triggers RFC 7807 HTTP 422."""
        # Provision client & portfolio
        cust = self.client.post(
            "/api/v1/customers", json={"legal_name": "Test Cust", "country_code": "US"}
        ).json()
        port = self.client.post(
            "/api/v1/portfolios",
            json={
                "portfolio_code": "PORT_LONG_ONLY",
                "customer_id": cust["customer_id"],
                "portfolio_name": "Test Port",
                "base_currency": "USD",
            },
        ).json()
        cash_id = port["cash_accounts"][0]["cash_account_id"]
        sec = self.client.post(
            "/api/v1/securities",
            json={
                "ticker": "MSFT",
                "security_name": "Microsoft",
                "primary_exchange": "XNAS",
                "currency": "USD",
                "country_of_risk": "US",
            },
        ).json()

        # Buy 50 shares
        self.client.post(
            "/api/v1/transactions",
            json={
                "portfolio_id": port["portfolio_id"],
                "security_id": sec["security_id"],
                "cash_account_id": cash_id,
                "transaction_type": "BUY",
                "quantity": "50.0",
                "unit_price": "300.0",
                "currency_local": "USD",
                "gross_amount_local": "15000.0",
                "correlation_id": "BUY-01",
            },
        )

        # Attempt to SELL 51 shares (1 share too many!)
        illegal_sell = self.client.post(
            "/api/v1/transactions",
            json={
                "portfolio_id": port["portfolio_id"],
                "security_id": sec["security_id"],
                "cash_account_id": cash_id,
                "transaction_type": "SELL",
                "quantity": "51.0",
                "unit_price": "310.0",
                "currency_local": "USD",
                "gross_amount_local": "15810.0",
                "correlation_id": "SELL-ILLEGAL",
            },
        )
        self.assertEqual(illegal_sell.status_code, 422)
        err = illegal_sell.json()
        self.assertEqual(err["code"], "ERR_INSUFFICIENT_HOLDINGS")
        self.assertIn("Requested: 51.0", err["detail"])

    def test_negative_invalid_currency_rfc7807(self) -> None:
        """Verify that lowercase or malformed currency codes trigger RFC 7807 HTTP 422."""
        cust = self.client.post(
            "/api/v1/customers", json={"legal_name": "Test Cust", "country_code": "US"}
        ).json()
        port = self.client.post(
            "/api/v1/portfolios",
            json={
                "portfolio_code": "PORT_CURR_TEST",
                "customer_id": cust["customer_id"],
                "portfolio_name": "Test Port",
                "base_currency": "USD",
            },
        ).json()
        cash_id = port["cash_accounts"][0]["cash_account_id"]

        # Transaction with invalid lowercase currency
        resp = self.client.post(
            "/api/v1/transactions",
            json={
                "portfolio_id": port["portfolio_id"],
                "cash_account_id": cash_id,
                "transaction_type": "DEPOSIT",
                "quantity": "0.0",
                "unit_price": "0.0",
                "currency_local": "usd",  # lowercase -> invalid
                "gross_amount_local": "1000.0",
                "correlation_id": "CORR-BAD-CURR",
            },
        )
        self.assertEqual(resp.status_code, 422)
        err = resp.json()
        self.assertEqual(err["code"], "ERR_INVALID_CURRENCY")


if __name__ == "__main__":
    unittest.main()
