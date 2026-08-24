"""LedgerMate V2 — extended API and bug regression tests."""
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


def test_nl_sale_maps_to_income():
    r = client.post("/api/transactions/nl", json={"text": "I sold 5 bags of rice for 100000 XAF"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["proposal"]["type"] == "income"
    assert int(body["proposal"]["amount"]) > 0


def test_nl_expense_math():
    r = client.post("/api/transactions/nl", json={"text": "I bought fish for 3000 XAF and tomato for 500"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["proposal"]["type"] == "expense"
    assert body["proposal"]["currency"] == "XAF"
    assert int(body["proposal"]["amount"]) > 0


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


def test_invoices_endpoint():
    r = client.get("/api/invoices")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_create_invoice():
    r = client.post("/api/invoices", json={"customer_name": "Test", "items": [], "total": "1000"})
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_customers_endpoint():
    r = client.get("/api/customers")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_create_customer():
    r = client.post("/api/customers", json={"name": "Test"})
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_products_endpoint():
    r = client.get("/api/products")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_create_product():
    r = client.post("/api/products", json={"name": "Test"})
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_trash_endpoint():
    r = client.get("/api/trash")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_offline_audit_no_runtime_external_dependencies():
    files = ["src/ledgermate/api.py", "src/ledgermate/llm.py", "static/index.html"]
    # Deny real external network targets/runtimes; allow local fetch/HTTP only when scoped to localhost/127.0.0.1.
    external_http_patterns = ["http://", "https://"]
    local_api_prefixes = ("/api", "/static", "127.0.0.1", "localhost")
    forbidden_runtime = ["axios", "XMLHttpRequest"]
    for path in files:
        text = Path(path).read_text(encoding="utf-8")
        for token in forbidden_runtime:
            assert token not in text, f"forbidden runtime token {token} in {path}"
        if "fetch(" in text:
            # Ensure no fetch targets external origins
            for line in text.splitlines():
                if "fetch(" in line:
                    lowered = line.lower()
                    if any(lowered.startswith(p) for p in local_api_prefixes):
                        continue
                    for prefix in external_http_patterns:
                        if prefix in lowered:
                            assert False, f"external fetch target in {path}: {line.strip()}"


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
