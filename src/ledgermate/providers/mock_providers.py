"""LedgerMate V2 — mock providers for tests."""
from __future__ import annotations

from pathlib import Path

from ledgermate.providers.base import ExtractedTransaction, LLMProvider, STTProvider, Transcript


class MockLLMProvider(LLMProvider):
    name = "mock_llm"
    available = True

    def extract_transaction(self, transcript: str) -> ExtractedTransaction:
        lowered = transcript.lower()
        txn_type = "expense" if "spent" in lowered or "paid" in lowered else "income"
        return ExtractedTransaction(
            transaction_type=txn_type,
            amount="0",
            currency="XAF",
            date="",
            description=transcript[:120],
            category="general",
            counterparty=None,
            payment_method=None,
            notes="mock",
        )


class MockSTTProvider(STTProvider):
    name = "mock_stt"
    available = True
    supports_streaming = False

    def transcribe(self, audio_path: Path) -> Transcript:
        return Transcript(raw="mock transcript", current="mock transcript", edited=None, final=None)

    def transcribe_stream(self, audio_path: Path) -> Transcript:
        return self.transcribe(audio_path)
