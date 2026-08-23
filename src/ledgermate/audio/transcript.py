"""LedgerMate V2 — transcript editing and persistence."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Transcript:
    raw: str
    current: str
    edited: Optional[str] = None
    final: Optional[str] = None

    def apply_edit(self, edited: str) -> None:
        self.edited = edited
        self.current = edited
        self.final = None

    def confirm(self) -> None:
        self.final = self.current
