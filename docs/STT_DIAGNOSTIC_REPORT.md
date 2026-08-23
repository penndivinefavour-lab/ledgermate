# LedgerMate V2 — STT Diagnostic Report
## Date: 2026-08-23

## Problem
Whisper Python API is importable, but CLI hangs and Python API model download fails SHA256 verification on Windows.

## Root cause
Whisper tiny model download from HuggingFace is corrupt/incomplete. Cached file fails checksum. Network download reliability issue.

## Tests performed
1. `pip install openai-whisper` — SUCCESS
2. `import whisper` — SUCCESS
3. `whisper --help` — HANGS
4. `whisper --version` — HANGS
5. `subprocess.run(["whisper", ...], capture_output=True, timeout=300)` — HANGS
6. `whisper.load_model("tiny")` — FAILS: SHA256 checksum mismatch
7. Direct Python API transcription — BLOCKED by model download failure

## Fix attempted
- Changed default model from `small` to `tiny`
- Added timeout to subprocess call
- Both attempts still fail

## Final decision
- LocalSTTProvider is a valid wrapper but cannot function on this Windows machine
- Keep interface intact for future hardware/OS
- Document limitation clearly
- Do NOT claim voice transcription works
- Isolate STT as optional/unavailable

## Dependencies retained
- openai-whisper
- torch
- numpy

## Dependencies removed
- None

## Blocked
- Real voice end-to-end test
- Real STT transcription test
