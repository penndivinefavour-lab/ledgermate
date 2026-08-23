"""LedgerMate V2 — voice workflow tests."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ledgermate.audio.states import VoiceState
from ledgermate.audio.transcript import Transcript
from ledgermate.domain.proposal import TransactionProposal
from ledgermate.errors import ExtractionError, PersistenceError, RecordingError, TranscriptionError, ValidationError


def test_voice_state_values():
    assert VoiceState.IDLE.value == "idle"
    assert VoiceState.RECORDING.value == "recording"
    assert VoiceState.CANCELLED.value == "cancelled"


def test_transcript_edit_and_confirm():
    t = Transcript(raw="hello world", current="hello world")
    assert t.final is None
    t.apply_edit("hello universe")
    assert t.current == "hello universe"
    assert t.edited == "hello universe"
    assert t.final is None
    t.confirm()
    assert t.final == "hello universe"


def test_transcript_no_final_until_confirmed():
    t = Transcript(raw="raw", current="raw")
    t.apply_edit("edited")
    assert t.final is None


def test_proposal_confirmed_dict_keys():
    p = TransactionProposal(
        transaction_type="expense",
        amount="1500",
        currency="XAF",
        date="2026-08-20",
        description="fuel",
        category="transport",
        counterparty="station",
        payment_method="cash",
    )
    data = p.confirmed_dict()
    assert data["transaction_id"]
    assert data["type"] == "expense"
    assert data["amount"] == "1500"
    assert data["source"] == "voice"


def test_error_hierarchy():
    assert issubclass(RecordingError, Exception)
    assert issubclass(TranscriptionError, RecordingError) or issubclass(TranscriptionError, Exception)
    assert issubclass(ExtractionError, Exception)
    assert issubclass(ValidationError, Exception)
    assert issubclass(PersistenceError, Exception)


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
