"""LedgerMate V2 — agent registry."""
from __future__ import annotations

from typing import Any


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: dict[str, Any] = {}

    def register(self, name: str, agent: Any) -> None:
        self._agents[name] = agent

    def get(self, name: str) -> Any:
        return self._agents.get(name)

    @property
    def available(self) -> list[str]:
        return [name for name, agent in self._agents.items() if getattr(agent, "available", False)]
