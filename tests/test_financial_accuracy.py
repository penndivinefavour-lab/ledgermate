"""LedgerMate V2 — financial accuracy and safety tests."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from decimal import Decimal
from ledgermate.validation import validate_transaction, ValidationError
from ledgermate.domain.proposal import TransactionProposal
from ledgermate.providers.base import ExtractedTransaction


def test_xaf_amount_preserved():
    proposal = TransactionProposal(
        transaction_type="expense",
        amount="1500",
        currency="XAF",
        date="2026-08-20",
        description="fuel",
        category="transport",
    )
    validated = validate_transaction(proposal.confirmed_dict())
    assert validated.amount == Decimal("1500")
    assert validated.currency == "XAF"


def test_large_amount():
    proposal = TransactionProposal(
        transaction_type="expense",
        amount="15000",
        currency="XAF",
        date="2026-08-20",
        description="rent",
        category="housing",
    )
    validated = validate_transaction(proposal.confirmed_dict())
    assert validated.amount == Decimal("15000")


def test_negative_amount_rejected():
    try:
        validate_transaction({
            "transaction_id": "txn-neg",
            "date": "2026-08-20",
            "description": "test",
            "category": "general",
            "type": "expense",
            "amount": "-100",
            "currency": "XAF",
            "payment_method": "cash",
        })
        assert False, "Should have rejected negative amount"
    except ValidationError:
        pass


def test_zero_amount_rejected():
    try:
        validate_transaction({
            "transaction_id": "txn-zero",
            "date": "2026-08-20",
            "description": "test",
            "category": "general",
            "type": "expense",
            "amount": "0",
            "currency": "XAF",
            "payment_method": "cash",
        })
        assert False, "Should have rejected zero amount"
    except ValidationError:
        pass


def test_missing_amount_rejected():
    try:
        validate_transaction({
            "transaction_id": "txn-missing",
            "date": "2026-08-20",
            "description": "test",
            "category": "general",
            "type": "expense",
            "currency": "XAF",
            "payment_method": "cash",
        })
        assert False, "Should have rejected missing amount"
    except ValidationError:
        pass


def test_invalid_date_rejected():
    try:
        validate_transaction({
            "transaction_id": "txn-date",
            "date": "not-a-date",
            "description": "test",
            "category": "general",
            "type": "expense",
            "amount": "100",
            "currency": "XAF",
            "payment_method": "cash",
        })
        assert False, "Should have rejected invalid date"
    except ValidationError:
        pass


def test_unknown_type_rejected():
    try:
        validate_transaction({
            "transaction_id": "txn-type",
            "date": "2026-08-20",
            "description": "test",
            "category": "general",
            "type": "unknown_type",
            "amount": "100",
            "currency": "XAF",
            "payment_method": "cash",
        })
        assert False, "Should have rejected unknown type"
    except ValidationError:
        pass


def test_extracted_transaction_defaults():
    ext = ExtractedTransaction(
        transaction_type="income",
        amount="2500",
        currency="XAF",
        date="2026-08-20",
        description="sale",
        category="sales",
    )
    assert ext.transaction_type == "income"
    assert ext.amount == "2500"
    assert ext.currency == "XAF"
    assert ext.date == "2026-08-20"


def test_user_edit_overrides_model():
    proposal = TransactionProposal(
        transaction_type="expense",
        amount="5000",
        currency="XAF",
        date="2026-08-20",
        description="model guess",
        category="general",
    )
    data = proposal.confirmed_dict()
    data["amount"] = "6000"
    data["description"] = "user corrected"
    validated = validate_transaction(data)
    assert validated.amount == Decimal("6000")
    assert validated.description == "user corrected"


if __name__ == "__main__":
    tests = [v for k, v in sorted(locals().items()) if k.startswith("test_") and callable(v)]
    failures = 0
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
        except Exception as exc:
            print(f"FAIL {test.__name__}: {exc}")
            failures += 1
    print(f"Results: {len(tests) - failures}/{len(tests)} passed")
    raise SystemExit(1 if failures else 0)
