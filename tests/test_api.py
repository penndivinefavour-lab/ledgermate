"""LedgerMate V2 — API tests."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fastapi.testclient import TestClient
from ledgermate.api import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_dashboard():
    r = client.get("/api/dashboard")
    assert r.status_code == 200
    data = r.json()
    assert "income" in data
    assert "expenses" in data
    assert "profit" in data


def test_transactions_list():
    r = client.get("/api/transactions")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_create_transaction():
    txn = {
        "description": "Test transaction",
        "amount": "1000",
        "currency": "XAF",
        "type": "expense",
        "category": "test",
    }
    r = client.post("/api/transactions", json=txn)
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_assistant_balance():
    r = client.post("/api/assistant", json={"question": "What is my balance?"})
    assert r.status_code == 200
    assert "answer" in r.json()


def test_assistant_summary():
    r = client.post("/api/assistant", json={"question": "How is my business doing?"})
    assert r.status_code == 200
    assert "answer" in r.json()


def test_categories():
    r = client.get("/api/analytics/categories")
    assert r.status_code == 200
    assert "expense_by_category" in r.json()


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
