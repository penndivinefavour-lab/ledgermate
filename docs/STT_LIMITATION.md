# LedgerMate V2 — STT Limitation
## Date: 2026-08-23
## Status: WHISPER UNUSABLE ON WINDOWS — LOCAL STT BLOCKED

## Verified findings
1. `pip install openai-whisper` — SUCCESS
2. `import whisper` — SUCCESS
3. `whisper --help` — HANGS indefinitely
4. `whisper --version` — HANGS indefinitely
5. `subprocess.run(["whisper", ...], capture_output=True, timeout=300)` — HANGS
6. `whisper.load_model("tiny")` — FAILS with `RuntimeError: Model has been downloaded but the SHA256 checksum does not match. Please retry loading the model.`

## Root cause
Whisper tiny model download from HuggingFace is corrupt/incomplete on this Windows machine. The cached file fails SHA256 verification. Re-download also fails checksum. This is a network/download integrity issue, not a code bug.

## Impact
- LocalSTTProvider cannot function on this Windows machine
- Voice workflow stops at transcription step
- Core text workflow remains fully functional
- ADTC competition build does not require voice/STT

## Decision
- Keep LocalSTTProvider interface intact for future hardware/OS
- Document limitation clearly
- Do NOT claim voice transcription works
- Continue V2 without verified STT
- Consider alternative lighter STT or different hardware/OS in future

## Next action
- If STT becomes available on different hardware, test and integrate
- For now, isolate STT as optional/unavailable
