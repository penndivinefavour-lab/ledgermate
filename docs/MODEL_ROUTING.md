# LedgerMate V2 — Model Routing

## Local providers
- LLM: llama.cpp with Llama 3.2 1B GGUF
- STT: openai-whisper local (optional)

## Remote providers
- None configured
- Cloud providers remain optional and not included by default

## Fallback rules
1. If local LLM unavailable, fall back to mock provider for tests
2. If local STT unavailable, voice workflow stops at transcription with error
3. Core text workflow continues without voice/agents

## Constraints
- No paid APIs
- No cloud inference during evaluation
- No credentials stored in repo
