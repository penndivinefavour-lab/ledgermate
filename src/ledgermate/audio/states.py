"""LedgerMate V2 — voice workflow states."""
from __future__ import annotations

from enum import Enum


class VoiceState(str, Enum):
    IDLE = "idle"
    RECORDING = "recording"
    PAUSED = "paused"
    TRANSCRIBING = "transcribing"
    EDITING = "editing"
    PROCESSING = "processing"
    CONFIRMATION = "confirmation"
    SAVED = "saved"
    FAILED = "failed"
    CANCELLED = "cancelled"
