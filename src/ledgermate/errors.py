"""LedgerMate V2 — voice workflow exceptions."""
from __future__ import annotations


class LedgerMateError(Exception):
    pass


class RecordingError(LedgerMateError):
    pass


class TranscriptionError(LedgerMateError):
    pass


class ExtractionError(LedgerMateError):
    pass


class ValidationError(LedgerMateError):
    pass


class PersistenceError(LedgerMateError):
    pass
