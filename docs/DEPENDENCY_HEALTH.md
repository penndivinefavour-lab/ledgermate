# LedgerMate V2 — Dependency Health

## Production dependencies
| Component | Purpose | Required? | Status | Version | License | Risk | Action |
|---|---|---|---|---|---|---|---|
| Python 3.11+ | Runtime | Yes | OK | 3.11.16 | PSF | Low | None |
| SQLite | Persistence | Yes | OK | stdlib | Public domain | Low | None |
| llama.cpp | LLM inference | Yes | OK | 0.1.2-dev build 10507 | MIT | Low | None |
| Llama 3.2 1B GGUF | Model weights | Yes | OK | Q4_K_M | Llama Community | Low | Attribution present |
| sounddevice | Audio capture | Optional | Unverified | — | MIT | Low | Verify install |
| numpy | Audio arrays | Optional | Unverified | — | BSD | Low | Verify install |
| rich | TUI | Optional | OK | 13.x | MIT | Low | None |
| pydantic | Validation | Optional | OK | 2.x | MIT | Low | None |
| python-dotenv | Config | Optional | OK | 1.x | BSD | Low | None |
| whisper | Local STT | Optional | Not installed | — | MIT | Medium | Install only if needed |

## Test dependencies
| Component | Purpose | Required? | Status | Action |
|---|---|---|---|---|
| pytest / unittest | Tests | Yes | Using stdlib unittest | None |
| Mock providers | Tests | Yes | Implemented | None |

## Broken/obsolete components
- None identified in V2 workspace

## Cleanup actions needed
- Verify sounddevice and numpy installation before enabling audio capture
- Do not add cloud STT/LLM dependencies
