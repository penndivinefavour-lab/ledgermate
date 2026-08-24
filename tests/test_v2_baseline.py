"""LedgerMate V2 — baseline tests for core modules."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ledgermate.schema import Transaction, TransactionType
from ledgermate.validation import validate_transaction
from ledgermate.ledger import Ledger
from ledgermate.export import export_csv, export_json
from ledgermate.providers.base import ProviderRegistry, ExtractedTransaction
from ledgermate.providers.mock_providers import MockLLMProvider, MockSTTProvider
from ledgermate.providers.registry import build_registry
from ledgermate.audio.recorder import AudioRecorder
from ledgermate.agents.registry import AgentRegistry
from ledgermate.config import Config


def test_schema_creation():
    txn = Transaction(
        transaction_id="txn-001",
        date="2026-08-20",
        description="test",
        category="general",
        type=TransactionType.INCOME,
        amount="1000",
        currency="XAF",
        payment_method="cash",
        counterparty=None,
        notes=None,
    )
    assert txn.amount == "1000"
    assert txn.currency == "XAF"
    assert txn.type == TransactionType.INCOME


def test_validation_success():
    txn = validate_transaction({
        "transaction_id": "txn-002",
        "date": "2026-08-20",
        "description": "sale",
        "category": "general",
        "type": "income",
        "amount": "2500",
        "currency": "XAF",
        "payment_method": "cash",
        "counterparty": "Alpha",
        "notes": None,
    })
    assert str(txn.amount) == "2500"
    assert txn.date.isoformat() == "2026-08-20"


def test_ledger_persistence():
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        db = Path(tmpdir) / "test.db"
        ledger = Ledger(db)
        txn = validate_transaction({
            "transaction_id": "txn-003",
            "date": "2026-08-20",
            "description": "test",
            "category": "general",
            "type": "expense",
            "amount": "500",
            "currency": "XAF",
            "payment_method": "cash",
            "counterparty": None,
            "notes": None,
        })
        ledger.add_transaction(txn)
        rows = ledger.list_transactions()
        assert len(rows) == 1
        bal = ledger.balance()
        assert bal["expense"] == "500"


def test_export_roundtrip():
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        db = Path(tmpdir) / "test.db"
        ledger = Ledger(db)
        txn = validate_transaction({
            "transaction_id": "txn-004",
            "date": "2026-08-20",
            "description": "export test",
            "category": "general",
            "type": "income",
            "amount": "1000",
            "currency": "XAF",
            "payment_method": "cash",
            "counterparty": None,
            "notes": None,
        })
        ledger.add_transaction(txn)
        rows = ledger.list_transactions()
        csv_path = export_csv(rows, Path(tmpdir) / "out.csv")
        json_path = export_json(rows, Path(tmpdir) / "out.json")
        assert csv_path.exists()
        assert json_path.exists()
        assert csv_path.read_text().count("\n") >= 2
        assert '"transaction_id"' in json_path.read_text()


def test_mock_llm_provider():
    provider = MockLLMProvider()
    assert provider.available is True
    result = provider.extract_transaction("I spent 1500 XAF on fuel")
    assert result.transaction_type == "expense"
    assert result.amount == "0"


def test_registry_returns_mock():
    from ledgermate.providers.mock_providers import MockLLMProvider
    provider = MockLLMProvider()
    assert provider.available is True
    result = provider.extract_transaction("I spent 1500 XAF on fuel")
    assert result.transaction_type == "expense"
    assert result.amount == "0"


def test_audio_recorder_unavailable():
    recorder = AudioRecorder()
    assert recorder.available in {True, False}


def test_agent_registry():
    registry = AgentRegistry()
    registry.register("test", object())
    assert registry.get("test") is not None


def test_config_dirs():
    config = Config()
    config.ensure_dirs()
    assert config.data_dir.exists()
    assert config.exports_dir.exists()
    assert config.audio_dir.exists()


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
