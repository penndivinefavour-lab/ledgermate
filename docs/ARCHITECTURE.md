# LedgerMate V2 — Architecture

## Stack
- Python 3.11+
- SQLite for persistence
- Rich for TUI
- sounddevice + numpy for audio capture
- whisper.cpp or openai-whisper for local STT
- llama.cpp for local LLM

## Layers
1. CLI/TUI layer
2. Audio capture layer
3. STT provider layer
4. LLM provider layer
5. Financial validation layer
6. Ledger persistence layer
7. Export layer

## Data flow
Voice → AudioRecorder → STTProvider → Transcript → User edits → LLMProvider → ExtractedTransaction → validate_transaction → User confirms → Ledger.add_transaction → Audit log → Export

## Provider abstraction
All AI providers implement base interfaces in `providers/base.py`.
Registry selects first available provider.
Mock providers for testing.
Local providers preferred.
Cloud providers optional and not included by default.

## Deterministic boundary
LLM output is never trusted for arithmetic.
Python Decimal engine validates amounts, balances, and totals.
Audit log is append-only.
