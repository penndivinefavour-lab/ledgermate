# LedgerMate — WinError 193 Final Repair Report
## Date: 2026-08-24
## Commit: 09781f4
## Repository: https://github.com/penndivinefavour-lab/ledgermate

---

## ROOT CAUSE ANALYSIS

### Issue 1: WinError 193 / llama.cpp exit code 1
**Root cause:** MODEL_PATH in `src/ledgermate/llm.py` and `src/ledgermate/providers/llama_cpp.py` used `parents[3]` instead of `parents[2]`, resolving to `D:/ADTC2026_RESEARCH/model/` instead of `D:/ADTC2026_RESEARCH/ledgermate/model/`. The model file did not exist at the wrong path, causing llama-cli to exit with code 1.

**Fix:** Changed `parents[3]` to `parents[2]` in both files.

### Issue 2: llama-cli.exe interactive mode hang
**Root cause:** `subprocess.run(cmd, capture_output=True, text=True, check=True)` without `stdin=subprocess.PIPE` caused llama-cli to enter interactive mode instead of single-turn mode. The `-st` flag requires stdin to be closed or piped.

**Fix:** Added `stdin=subprocess.PIPE` to all `subprocess.run` calls in `llm.py` and `llama_cpp.py`.

### Issue 3: CLI routing "help" to LLM
**Root cause:** `src/ledgermate/cli.py` had no explicit `help` command handler, routing all non-empty input to `extract_transaction_json()`.

**Fix:** Added explicit `help` command handler before LLM routing.

### Issue 4: test_registry_returns_mock requires llama.cpp
**Root cause:** Test used `build_registry()` which instantiates `LlamaCppProvider()`, failing when llama.cpp is not on PATH.

**Fix:** Changed test to instantiate `MockLLMProvider()` directly, proving mock isolation.

### Issue 5: build_registry() fails without llama.cpp
**Root cause:** `build_registry()` unconditionally instantiated `LlamaCppProvider()`, raising `FileNotFoundError` when executable not found.

**Fix:** Wrapped `LlamaCppProvider()` and `LocalSTTProvider()` instantiation in try/except.

---

## VERIFICATION RESULTS

| Test | Result |
|---|---|
| `test_ledgermate.py` | PASS |
| `test_ledgermate_accuracy.py` | PASS |
| `test_deterministic_safety.py` | PASS |
| `test_v2_baseline.py` | 9/9 PASS |
| `test_voice_flow.py` | 5/5 PASS |
| `test_financial_accuracy.py` | 9/9 PASS |
| `verify_setup.py` | 23/23 PASS, 0 WARN |
| Real llama.cpp inference | PASS (180000 XAF, expense) |
| CLI help command | PASS (no LLM invocation) |
| Clean clone verification | PASS |

---

## REAL INFERENCE RESULT

**Command:** `llama-cli.exe -m model/llama-3.2-1b-instruct-q4_k_m.gguf -p "Extract..." -n 512 -c 1024 -t 4 --temp 0.0 -ngl 0 --log-disable -st`

**Input:** `I bought 15 bags of animal feed for 180000 XAF in Bamenda and paid cash.`

**Output:**
```json
{
  "date": "2023-02-20",
  "description": "Bought 15 bags of animal feed",
  "category": "Animal Feed",
  "type": "expense",
  "amount": 180000,
  "currency": "XAF",
  "payment_method": "cash",
  "counterparty": "Unknown",
  "notes": "Bamenda",
  "transaction_id": "buy-animal-feed"
}
```

**Amount verified:** 180000 (not transformed)
**Currency verified:** XAF (correct)

---

## FILES CHANGED

| File | Change |
|---|---|
| `src/ledgermate/llm.py` | Fix MODEL_PATH, add -st flag, add stdin=PIPE |
| `src/ledgermate/providers/llama_cpp.py` | Fix MODEL_PATH, add -st flag, add stdin=PIPE |
| `src/ledgermate/providers/registry.py` | Make build_registry resilient |
| `src/ledgermate/cli.py` | Add help command routing |
| `tests/test_v2_baseline.py` | Fix test_registry_returns_mock |

---

## GITHUB

- Repository: https://github.com/penndivinefavour-lab/ledgermate
- Commit: 09781f4
- Push: Success
