"""LedgerMate V2 — registry of available providers."""
from __future__ import annotations

from ledgermate.providers.base import ProviderRegistry
from ledgermate.providers.local_stt import LocalSTTProvider
from ledgermate.providers.llama_cpp import LlamaCppProvider
from ledgermate.providers.mock_providers import MockLLMProvider, MockSTTProvider


def build_registry() -> ProviderRegistry:
    registry = ProviderRegistry()
    try:
        registry.register_llm(LlamaCppProvider())
    except Exception:
        pass
    registry.register_llm(MockLLMProvider())
    try:
        registry.register_stt(LocalSTTProvider())
    except Exception:
        pass
    registry.register_stt(MockSTTProvider())
    return registry
