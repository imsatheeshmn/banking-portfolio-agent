"""Local execution runner for Investment Data Engineering & Portfolio Intelligence Platform.

Usage:
    python scripts/run_local.py [--serve] [--port 8000]
"""
import argparse
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

# Add backend directory to sys.path
root_dir = Path(__file__).resolve().parent.parent
backend_dir = root_dir / "backend"
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.db.base import Base
from app.db.seed import seed_database
from app.models import Portfolio, TransactionLedger


def print_banner() -> None:
    print("=" * 80)
    print(" INVESTMENT DATA ENGINEERING & PORTFOLIO INTELLIGENCE PLATFORM")
    print(" Local Runner & Integrity Verification Engine")
    print(f" Timestamp: {datetime.now(timezone.utc).isoformat()} (UTC)")
    print("=" * 80)


def run_unit_tests() -> bool:
    print("\n[Step 1/3] Running Foundations and Database Test Suites...")
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=str(backend_dir / "tests"), pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if result.wasSuccessful():
        print(">>> SUCCESS: All tests passed cleanly.")
        return True
    else:
        print(">>> FAILURE: Tests encountered errors or failures.")
        return False


def verify_database_and_seed() -> bool:
    print("\n[Step 2/3] Verifying In-Memory Database Schema & Deterministic Seeding...")
    try:
        engine = create_engine("sqlite:///:memory:", echo=False)
        for table in Base.metadata.tables.values():
            table.schema = None
        Base.metadata.create_all(engine)

        with Session(engine) as session:
            stats = seed_database(session)
            print(f"  * Seeded entities: {stats}")

            port = session.query(Portfolio).filter_by(portfolio_code="APEX_GLOBAL_EQ").first()
            if not port:
                raise ValueError("Seeded portfolio APEX_GLOBAL_EQ not found.")

            txs = session.query(TransactionLedger).all()
            print(f"  * Total posted ledger transactions: {len(txs)}")
            for tx in txs:
                print(f"    - Tx {tx.transaction_id}: {tx.transaction_type} | Qty: {tx.quantity} | Amount: ${tx.gross_amount_local:,.2f} {tx.currency_local} | Status: {tx.status}")

        print(">>> SUCCESS: Database models, constraints, and seed logic verified.")
        return True
    except Exception as e:
        print(f">>> ERROR during database verification: {e}")
        return False


def start_documentation_server(port: int = 8000) -> None:
    import http.server
    import socketserver
    import webbrowser

    docs_dir = root_dir / "docs"
    print(f"\n[Step 3/3] Serving Documentation and Architecture Portal at http://localhost:{port}")
    print("Press Ctrl+C to stop the server.")

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(docs_dir), **kwargs)

    webbrowser.open(f"http://localhost:{port}")
    with socketserver.TCPServer(("", port), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down local server.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Platform Local Runner")
    parser.add_argument("--serve", action="store_true", help="Start local documentation and architecture portal server")
    parser.add_argument("--port", type=int, default=8000, help="Port for local server (default: 8000)")
    args = parser.parse_args()

    print_banner()
    tests_ok = run_unit_tests()
    db_ok = verify_database_and_seed()

    if not (tests_ok and db_ok):
        print("\n[!] Platform integrity check FAILED. Please review the errors above.")
        sys.exit(1)

    print("\n[✓] ALL LOCAL CHECKS PASSED: Platform is fully operational.")

    if args.serve:
        start_documentation_server(port=args.port)


if __name__ == "__main__":
    main()
