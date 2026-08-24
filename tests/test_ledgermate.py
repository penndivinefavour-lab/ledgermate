"""LedgerMate tests."""
from __future__ import annotations

import os
from decimal import Decimal
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ledgermate.schema import PaymentMethod, Transaction, TransactionType
from ledgermate.validation import validate_transaction, ValidationError
from ledgermate.ledger import Ledger
from ledgermate.export import export_csv, export_json


def test_positive_transaction():
    data = {
        "transaction_id": "txn-001",
        "date": "2026-08-20",
        "description": "Maize feed purchase",
        "category": "inventory",
        "type": "expense",
        "amount": "180000",
        "currency": "XAF",
        "payment_method": "cash",
        "counterparty": "Bamenda supplier",
        "notes": "15 bags",
    }
    txn = validate_transaction(data)
    assert txn.amount == Decimal("180000")
    assert txn.currency == "XAF"
    assert txn.type == TransactionType.EXPENSE


def test_invalid_amount():
    data = {
        "transaction_id": "txn-002",
        "date": "2026-08-20",
        "description": "Sale",
        "category": "sales",
        "type": "income",
        "amount": "-10",
        "currency": "XAF",
    }
    try:
        validate_transaction(data)
    except ValidationError:
        pass
    else:
        raise AssertionError("Expected ValidationError")


def test_missing_required_field():
    data = {
        "transaction_id": "txn-003",
        # missing date/description/category/type/amount
    }
    try:
        validate_transaction(data)
    except ValidationError:
        pass
    else:
        raise AssertionError("Expected ValidationError")


def test_ledger_persistence():
    with TemporaryDirectory() as tmpdir:
        db = Path(tmpdir) / "ledger.db"
        ledger = Ledger(db)
        txn = Transaction(
            transaction_id="txn-101",
            date=date(2026, 8, 20),
            description="Test sale",
            category="sales",
            type=TransactionType.INCOME,
            amount=Decimal("2500"),
            currency="XAF",
            payment_method=PaymentMethod.MOBILE_MONEY,
        )
        ledger.add_transaction(txn)
        rows = ledger.list_transactions()
        assert len(rows) == 1, f"Expected 1 row, got {len(rows)}"
        assert rows[0]["amount"] == "2500"
        bal = ledger.balance()
        assert Decimal(bal["income"]) == Decimal("2500")


def test_export_csv_and_json():
    with TemporaryDirectory() as tmpdir:
        db = Path(tmpdir) / "ledger.db"
        ledger = Ledger(db)
        txn = Transaction(
            transaction_id="txn-102",
            date=date(2026, 8, 20),
            description="Export test",
            category="test",
            type=TransactionType.INCOME,
            amount=Decimal("500"),
        )
        ledger.add_transaction(txn)
        rows = ledger.list_transactions()
        csv_path = Path(tmpdir) / "out.csv"
        json_path = Path(tmpdir) / "out.json"
        export_csv(rows, csv_path)
        export_json(rows, json_path)
        assert csv_path.exists() and csv_path.stat().st_size > 0
        assert json_path.exists() and json_path.stat().st_size > 0


def test_duplicate_transaction_rejected():
    with TemporaryDirectory() as tmpdir:
        db = Path(tmpdir) / "ledger.db"
        ledger = Ledger(db)
        txn1 = Transaction(
            transaction_id="txn-201",
            date=date(2026, 8, 20),
            description="A",
            category="sales",
            type=TransactionType.INCOME,
            amount=Decimal("100"),
        )
        ledger.add_transaction(txn1)
        try:
            ledger.add_transaction(txn1)
        except Exception:
            pass
        else:
            raise AssertionError("Duplicate should be rejected")


def test_future_date_rejected():
    data = {
        "transaction_id": "txn-future",
        "date": "2099-01-01",
        "description": "Future",
        "category": "test",
        "type": "income",
        "amount": "1000",
        "currency": "XAF",
    }
    try:
        validate_transaction(data)
    except ValidationError:
        pass
    else:
        raise AssertionError("Expected ValidationError")


if __name__ == "__main__":
    test_positive_transaction()
    test_invalid_amount()
    test_missing_required_field()
    test_ledger_persistence()
    test_export_csv_and_json()
    test_duplicate_transaction_rejected()
    test_future_date_rejected()
    print("All tests passed.")
