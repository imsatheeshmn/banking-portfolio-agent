"""Create master entities and bitemporal transaction ledger

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-11 20:35:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. oltp.customers
    op.create_table(
        "customers",
        sa.Column("customer_id", sa.Integer(), sa.Identity(always=True), nullable=False),
        sa.Column("legal_name", sa.String(length=255), nullable=False),
        sa.Column("country_code", sa.String(length=2), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="ACTIVE", nullable=False),
        sa.Column("created_at_utc", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", sa.String(length=64), server_default="system_migration", nullable=False),
        sa.Column("updated_at_utc", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_by", sa.String(length=64), server_default="system_migration", nullable=False),
        sa.PrimaryKeyConstraint("customer_id", name="pk_customers"),
        sa.CheckConstraint("length(country_code) = 2", name="ck_customers_country_code_len"),
        sa.CheckConstraint("country_code = upper(country_code)", name="ck_customers_country_code_upper"),
        schema="oltp",
    )

    # 2. oltp.portfolios
    op.create_table(
        "portfolios",
        sa.Column("portfolio_id", sa.Integer(), sa.Identity(always=True), nullable=False),
        sa.Column("portfolio_code", sa.String(length=32), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("portfolio_name", sa.String(length=255), nullable=False),
        sa.Column("base_currency", sa.String(length=3), nullable=False),
        sa.Column("inception_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="ACTIVE", nullable=False),
        sa.Column("created_at_utc", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", sa.String(length=64), server_default="system_migration", nullable=False),
        sa.Column("updated_at_utc", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_by", sa.String(length=64), server_default="system_migration", nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["oltp.customers.customer_id"], name="fk_portfolios_customer_id", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("portfolio_id", name="pk_portfolios"),
        sa.UniqueConstraint("portfolio_code", name="uq_portfolios_portfolio_code"),
        sa.CheckConstraint("length(base_currency) = 3", name="ck_portfolios_currency_len"),
        sa.CheckConstraint("base_currency = upper(base_currency)", name="ck_portfolios_currency_upper"),
        schema="oltp",
    )
    op.create_index("ix_portfolios_portfolio_code", "portfolios", ["portfolio_code"], schema="oltp")
    op.create_index("ix_portfolios_customer_id", "portfolios", ["customer_id"], schema="oltp")

    # 3. oltp.cash_accounts
    op.create_table(
        "cash_accounts",
        sa.Column("cash_account_id", sa.Integer(), sa.Identity(always=True), nullable=False),
        sa.Column("portfolio_id", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("account_type", sa.String(length=32), server_default="SETTLEMENT", nullable=False),
        sa.Column("iban_or_account_number", sa.String(length=64), nullable=True),
        sa.Column("created_at_utc", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", sa.String(length=64), server_default="system_migration", nullable=False),
        sa.Column("updated_at_utc", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_by", sa.String(length=64), server_default="system_migration", nullable=False),
        sa.ForeignKeyConstraint(["portfolio_id"], ["oltp.portfolios.portfolio_id"], name="fk_cash_accounts_portfolio_id", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("cash_account_id", name="pk_cash_accounts"),
        sa.UniqueConstraint("portfolio_id", "currency", "account_type", name="uq_cash_accounts_port_curr_type"),
        sa.CheckConstraint("length(currency) = 3", name="ck_cash_accounts_currency_len"),
        sa.CheckConstraint("currency = upper(currency)", name="ck_cash_accounts_currency_upper"),
        schema="oltp",
    )
    op.create_index("ix_cash_accounts_portfolio_id", "cash_accounts", ["portfolio_id"], schema="oltp")

    # 4. oltp.securities
    op.create_table(
        "securities",
        sa.Column("security_id", sa.Integer(), sa.Identity(always=True), nullable=False),
        sa.Column("ticker", sa.String(length=32), nullable=False),
        sa.Column("security_name", sa.String(length=255), nullable=False),
        sa.Column("instrument_type", sa.String(length=32), server_default="EQUITY", nullable=False),
        sa.Column("primary_exchange", sa.String(length=16), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("country_of_risk", sa.String(length=2), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at_utc", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", sa.String(length=64), server_default="system_migration", nullable=False),
        sa.Column("updated_at_utc", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_by", sa.String(length=64), server_default="system_migration", nullable=False),
        sa.PrimaryKeyConstraint("security_id", name="pk_securities"),
        sa.CheckConstraint("length(currency) = 3", name="ck_securities_currency_len"),
        sa.CheckConstraint("currency = upper(currency)", name="ck_securities_currency_upper"),
        schema="oltp",
    )
    op.create_index("ix_securities_ticker", "securities", ["ticker"], schema="oltp")

    # 5. oltp.security_identifiers
    op.create_table(
        "security_identifiers",
        sa.Column("identifier_id", sa.Integer(), sa.Identity(always=True), nullable=False),
        sa.Column("security_id", sa.Integer(), nullable=False),
        sa.Column("identifier_type", sa.String(length=16), nullable=False),
        sa.Column("identifier_value", sa.String(length=32), nullable=False),
        sa.Column("valid_from", sa.Date(), server_default=sa.text("'1970-01-01'"), nullable=False),
        sa.Column("valid_to", sa.Date(), nullable=True),
        sa.Column("created_at_utc", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", sa.String(length=64), server_default="system_migration", nullable=False),
        sa.Column("updated_at_utc", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_by", sa.String(length=64), server_default="system_migration", nullable=False),
        sa.ForeignKeyConstraint(["security_id"], ["oltp.securities.security_id"], name="fk_sec_id_security_id", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("identifier_id", name="pk_security_identifiers"),
        sa.UniqueConstraint("identifier_type", "identifier_value", name="uq_sec_id_type_val"),
        sa.CheckConstraint("identifier_value = upper(identifier_value)", name="ck_sec_id_val_upper"),
        schema="oltp",
    )
    op.create_index("ix_sec_id_security_id", "security_identifiers", ["security_id"], schema="oltp")
    op.create_index("ix_sec_id_identifier_value", "security_identifiers", ["identifier_value"], schema="oltp")

    # 6. oltp.transaction_ledger
    op.create_table(
        "transaction_ledger",
        sa.Column("transaction_id", sa.Uuid(), nullable=False),
        sa.Column("original_transaction_id", sa.Uuid(), nullable=True),
        sa.Column("run_id", sa.String(length=64), nullable=False),
        sa.Column("correlation_id", sa.String(length=64), nullable=False),
        sa.Column("portfolio_id", sa.Integer(), nullable=False),
        sa.Column("security_id", sa.Integer(), nullable=True),
        sa.Column("cash_account_id", sa.Integer(), nullable=False),
        sa.Column("transaction_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="NEW", nullable=False),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("settlement_date", sa.Date(), nullable=False),
        sa.Column("recorded_at_utc", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=24, scale=8), server_default="0.0", nullable=False),
        sa.Column("unit_price", sa.Numeric(precision=20, scale=10), server_default="0.0", nullable=False),
        sa.Column("currency_local", sa.String(length=3), nullable=False),
        sa.Column("gross_amount_local", sa.Numeric(precision=20, scale=4), nullable=False),
        sa.Column("net_amount_local", sa.Numeric(precision=20, scale=4), nullable=False),
        sa.Column("fx_rate_to_base", sa.Numeric(precision=20, scale=10), server_default="1.0", nullable=False),
        sa.Column("currency_base", sa.String(length=3), nullable=False),
        sa.Column("net_amount_base", sa.Numeric(precision=20, scale=4), nullable=False),
        sa.Column("created_by", sa.String(length=64), nullable=False),
        sa.Column("approved_by", sa.String(length=64), nullable=True),
        sa.Column("approved_at_utc", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["original_transaction_id"], ["oltp.transaction_ledger.transaction_id"], name="fk_tx_ledger_orig_tx_id", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["portfolio_id"], ["oltp.portfolios.portfolio_id"], name="fk_tx_ledger_portfolio_id", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["security_id"], ["oltp.securities.security_id"], name="fk_tx_ledger_security_id", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["cash_account_id"], ["oltp.cash_accounts.cash_account_id"], name="fk_tx_ledger_cash_account_id", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("transaction_id", name="pk_transaction_ledger"),
        sa.CheckConstraint("quantity >= 0", name="ck_tx_ledger_quantity_pos"),
        sa.CheckConstraint("unit_price >= 0", name="ck_tx_ledger_price_pos"),
        sa.CheckConstraint("fx_rate_to_base > 0", name="ck_tx_ledger_fx_rate_pos"),
        sa.CheckConstraint("length(currency_local) = 3", name="ck_tx_ledger_curr_local_len"),
        sa.CheckConstraint("length(currency_base) = 3", name="ck_tx_ledger_curr_base_len"),
        schema="oltp",
    )
    op.create_index("ix_tx_ledger_bitemporal_scan", "transaction_ledger", ["portfolio_id", "trade_date", "recorded_at_utc"], schema="oltp")
    op.create_index("ix_tx_ledger_settlement_scan", "transaction_ledger", ["portfolio_id", "settlement_date", "status"], schema="oltp")
    op.create_index("ix_tx_ledger_run_id", "transaction_ledger", ["run_id"], schema="oltp")
    op.create_index("ix_tx_ledger_correlation_id", "transaction_ledger", ["correlation_id"], schema="oltp")


def downgrade() -> None:
    op.drop_table("transaction_ledger", schema="oltp")
    op.drop_table("security_identifiers", schema="oltp")
    op.drop_table("securities", schema="oltp")
    op.drop_table("cash_accounts", schema="oltp")
    op.drop_table("portfolios", schema="oltp")
    op.drop_table("customers", schema="oltp")
