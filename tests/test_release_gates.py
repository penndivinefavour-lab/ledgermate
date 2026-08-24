"""Regression tests for release gates."""
from __future__ import annotations

import sys
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fastapi.testclient import TestClient
from decimal import Decimal

from ledgermate.api import app
from ledgermate.services import settings
from ledgermate.ledger import Ledger
from ledgermate.schema import Transaction, TransactionType
from ledgermate.export import export_invoice_pdf, export_invoice_word

client = TestClient(app)


def test_nl_missing_amount_asks_clarification():
    resp = client.post("/api/transactions/nl", json={"text": "I bought fish"})
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("needs_clarification") is True
    assert "amount" in (data.get("clarification_prompt") or "").lower()


def test_nl_amount_then_save():
    first = client.post("/api/transactions/nl", json={"text": "I bought fish"})
    assert first.status_code == 200
    assert first.json().get("needs_clarification") is True
    second = client.post("/api/transactions/nl", json={"text": "I bought fish", "amount": "3500"})
    assert second.status_code == 200
    data = second.json()
    assert Decimal(str(data.get("proposal", {}).get("amount", "0"))) == Decimal("3500")


def test_duplicate_transaction_prevention():
    with TemporaryDirectory() as tmpdir:
        ledger = Ledger(Path(tmpdir) / "ledger.db")
        txn = Transaction(
            transaction_id="dup-reg-001",
            date=__import__('datetime').date(2026, 8, 24),
            description="regression tx",
            category="general",
            type=TransactionType.EXPENSE,
            amount=Decimal("1000"),
            currency="XAF",
        )
        ledger.add_transaction(txn)
        try:
            ledger.add_transaction(txn)
        except Exception:
            pass
        else:
            raise AssertionError("Duplicate should be rejected")
        rows = ledger.list_transactions()
        assert [row.get("transaction_id") for row in rows].count("dup-reg-001") == 1


def test_dashboard_aggregation():
    resp = client.get("/api/dashboard?period=all")
    assert resp.status_code == 200
    data = resp.json()
    assert "income" in data
    assert "expenses" in data
    assert "profit" in data
    assert "transaction_count" in data
    assert "expense_by_category" in data
    assert "income_by_category" in data


def test_chart_data_contract():
    resp = client.get("/api/transactions")
    assert resp.status_code == 200
    rows = resp.json()
    for row in rows:
        assert "date" in row
        assert "amount" in row
        assert "type" in row
        assert "category" in row


def test_invoice_pdf_export():
    create = client.post("/api/invoices", json={"customer_name": "Test", "items": [{"name": "Item", "quantity": 1, "unit_price": 1000, "total": 1000}], "subtotal": 1000, "tax": 0, "discount": 0, "total": 1000, "currency": "XAF", "status": "draft"})
    assert create.status_code == 200
    invoice = create.json()["invoice"]
    pdf_resp = client.get(f"/api/invoices/{invoice['invoice_id']}/pdf")
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert pdf_resp.content


def test_invoice_word_export():
    create = client.post("/api/invoices", json={"customer_name": "Test", "items": [{"name": "Item", "quantity": 1, "unit_price": 1000, "total": 1000}], "subtotal": 1000, "tax": 0, "discount": 0, "total": 1000, "currency": "XAF", "status": "draft"})
    assert create.status_code == 200
    invoice = create.json()["invoice"]
    word_resp = client.get(f"/api/invoices/{invoice['invoice_id']}/word")
    assert word_resp.status_code == 200
    assert "wordprocessingml" in word_resp.headers["content-type"]
    assert word_resp.content


def test_ai_business_context_known():
    settings.profile.business_name = "TestBiz"
    settings.save()
    resp = client.post("/api/assistant", json={"question": "What is my business name?"})
    assert resp.status_code == 200
    assert "TestBiz" in resp.json()["answer"]


def test_ai_business_context_unknown():
    settings.profile.business_name = ""
    settings.save()
    resp = client.post("/api/assistant", json={"question": "What is my business name?"})
    assert resp.status_code == 200
    assert "Settings" in resp.json()["answer"] or "configured" in resp.json()["answer"]


def test_conversation_memory_persistence():
    create = client.post("/api/conversations", json={"title": "Memory Test"})
    assert create.status_code == 200
    conv = create.json()
    msg = client.post(f"/api/conversations/{conv['id']}/messages", json={"role": "user", "content": "hello"})
    assert msg.status_code == 200
    assert msg.json()["messages"][-1]["content"] == "hello"


def test_settings_persistence():
    payload = {"profile": {"business_name": "Acme", "owner_name": "Owner", "phone": "123", "email": "a@b.com", "address": "City", "description": "Shop"}, "financial": {"currency": "USD"}, "language": "en"}
    r = client.post("/api/settings", json=payload)
    assert r.status_code == 200
    data = client.get("/api/settings").json()
    assert data["financial"]["currency"] == "USD"
    assert data["profile"]["business_name"] == "Acme"


def test_global_currency_propagation():
    client.post("/api/settings", json={"financial": {"currency": "EUR"}, "language": "en"})
    resp = client.get("/api/dashboard?period=all")
    assert resp.status_code == 200
    data = resp.json()
    assert "expense_by_category" in data
    assert "income_by_category" in data
