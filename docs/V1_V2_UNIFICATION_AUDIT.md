# LedgerMate V1/V2 Unification Audit
## Date: 2026-08-23

## Component Classification

### KEEP V1
- `src/ledgermate/schema.py` — V2 has identical copy
- `src/ledgermate/validation.py` — V2 has identical copy
- `src/ledgermate/ledger.py` — V2 has identical copy
- `src/ledgermate/export.py` — V2 has identical copy
- `src/ledgermate/llm.py` — V1 version is simpler, directly tested
- `src/ledgermate/cli.py` — V1 CLI is competition-critical
- `metadata.json` — V1 version has final email and prompts
- `submission.json` — V1 version is profiler-generated
- `download_model.sh` — V1 version is tested
- `REPORT.md` — V1 version is final
- `BENCHMARKS.md` — V1 version has measured values
- `LICENSE` — Keep as-is
- `MODEL_ATTRIBUTION.md` — Keep as-is
- `.gitignore` — V1 version is hardened
- `requirements.txt` — V1 version is minimal
- `tests/test_ledgermate.py` — V1 core tests
- `tests/test_ledgermate_accuracy.py` — V1 accuracy tests
- `tests/test_deterministic_safety.py` — V1 safety tests

### KEEP V2
- `src/ledgermate/__init__.py` — V2 version defines `__version__`
- `src/ledgermate/__version__.py` — New version module
- `src/ledgermate/providers/base.py` — Provider-neutral interfaces
- `src/ledgermate/providers/llama_cpp.py` — LLM provider abstraction
- `src/ledgermate/providers/local_stt.py` — STT provider abstraction
- `src/ledgermate/providers/mock_providers.py` — Test providers
- `src/ledgermate/providers/registry.py` — Provider registry
- `src/ledgermate/audio/recorder.py` — Audio recording
- `src/ledgermate/audio/states.py` — Voice state machine
- `src/ledgermate/audio/transcript.py` — Transcript editing
- `src/ledgermate/agents/registry.py` — Agent registry
- `src/ledgermate/config.py` — Configuration
- `src/ledgermate/domain/proposal.py` — Transaction proposal
- `src/ledgermate/errors.py` — Error hierarchy
- `tests/test_v2_baseline.py` — V2 baseline tests
- `tests/test_voice_flow.py` — Voice flow tests
- `tests/test_financial_accuracy.py` — Financial accuracy tests

### MERGE
- `src/ledgermate/__main__.py` — V2 has enhanced CLI with voice workflow
- `README.md` — V2 has more detail, keep V1's competition info
- `REPORT.md` — V2 has updated architecture docs
- `.gitignore` — Combine both, remove duplicates

### REMOVE
- No files to remove — V1 and V2 have no conflicting duplicates

### OPTIONAL
- `AUDIT_CURRENT_STATE.md` — V1 artifact, can be removed after merge
- `docs/` directory from V2 — Keep as documentation

## Rationale
V2 provides the architectural foundation with provider-neutral interfaces, voice workflow, and improved testing. V1 provides the competition-critical, battle-tested CLI and profiler integration. The merge preserves both: V2 architecture becomes canonical, V1 CLI/LLM integration remains as the reliable execution path.
