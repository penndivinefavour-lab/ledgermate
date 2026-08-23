"""LedgerMate V2 — provider-neutral AI and STT interfaces."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Transcript:
    raw: str
    current: str
    edited: Optional[str] = None
    final: Optional[str] = None


@dataclass
class ExtractedTransaction:
    transaction_type: str
    amount: str
    currency: str
    date: str
    description: str
    category: str
    counterparty: Optional[str] = None
    payment_method: Optional[str] = None
    notes: Optional[str] = None


class LLMProvider(ABC):
    name: str = "base"
    available: bool = False

    @abstractmethod
    def extract_transaction(self, transcript: str) -> ExtractedTransaction:
        ...


class STTProvider(ABC):
    name: str = "base"
    available: bool = False
    supports_streaming: bool = False

    @abstractmethod
    def transcribe(self, audio_path: Path) -> Transcript:
        ...

    @abstractmethod
    def transcribe_stream(self, audio_path: Path) -> Transcript:
        ...


class ProviderRegistry:
    def __init__(self) -> None:
        self._llm_providers: list[LLMProvider] = []
        self._stt_providers: list[STTProvider] = []

    def register_llm(self, provider: LLMProvider) -> None:
        self._llm_providers.append(provider)

    def register_stt(self, provider: STTProvider) -> None:
        self._stt_providers.append(provider)

    @property
    def llm(self) -> LLMProvider:
        available = [p for p in self._llm_providers if p.available]
        if not available:
            raise RuntimeError("No available LLM provider")
        return available[0]

    @property
    def stt(self) -> STTProvider:
        available = [p for p in self._stt_providers if p.available]
        if not available:
            raise RuntimeError("No available STT provider")
        return available[0]
