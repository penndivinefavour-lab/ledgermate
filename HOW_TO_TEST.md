# LedgerMate — How to Test and Verify
## Date: 2026-08-23
## Repository: https://github.com/penndivinefavour-lab/ledgermate

---

## QUICK START TESTING

### 1. Clone or use local copy
```bash
# Option A: Clone from GitHub
git clone https://github.com/penndivinefavour-lab/ledgermate.git
cd ledgermate

# Option B: Use local copy (already at D:/ADTC2026_RESEARCH/ledgermate/)
cd D:/ADTC2026_RESEARCH/ledgermate
```

### 2. Download model weights
```bash
bash download_model.sh
```
**Expected output:**
```
Downloading https://huggingface.co/hugging-quants/Llama-3.2-1B-Instruct-Q4_K_M-GGUF/resolve/main/llama-3.2-1b-instruct-q4_k_m.gguf ...
Downloaded to model/llama-3.2-1b-instruct-q4_k_m.gguf
Verifying file...
Model file ready.
```

**Verify:**
```bash
ls -lh model/llama-3.2-1b-instruct-q4_k_m.gguf
# Expected: ~771 MB file
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

**Expected:** Installation completes without errors.

### 4. Run the test suite
```bash
# Set PYTHONPATH to include src/
set PYTHONPATH=src

# Run all tests
python tests/test_ledgermate.py
python tests/test_ledgermate_accuracy.py
python tests/test_deterministic_safety.py
python tests/test_v2_baseline.py
python tests/test_voice_flow.py
python tests/test_financial_accuracy.py
```

**Expected output:**
```
All tests passed.
All LedgerMate-specific accuracy tests passed.
All deterministic safety boundary tests passed.
Results: 9/9 passed
Results: 5/5 passed
Results: 9/9 passed
```

**Total: 51/51 tests passing**

### 5. Run the CLI
```bash
python src/cli.py
```

**Expected:** Interactive CLI starts with prompt `ledgermate>`

**Try these commands:**
```
ledgermate> help
ledgermate> balance
ledgermate> list
ledgermate> add
ledgermate> export csv
ledgermate> exit
```

### 6. Test natural-language transaction (manual)
```bash
python src/cli.py
```

Then in the CLI:
```
ledgermate> add
Enter transaction description: I bought 15 bags of feed for 180,000 XAF from a Bamenda supplier, paid 80,000 XAF cash
```

**Expected:** Transaction is parsed, validated, and saved to SQLite ledger.

### 7. Run the ADTC profiler
```bash
# Install profiler
pip install "git+https://github.com/Africa-Deep-Tech-Foundation/adtc-profiler.git"

# Run participant mode
adtc-profiler run \
  --submission . \
  --mode participant \
  --output submission.json \
  --skip-accuracy
```

**Expected:** `submission.json` is generated/updated with measured metrics.

**Verify:**
```bash
python -c "import json; print(json.load(open('submission.json'))['throughput']['tokens_per_second_generation'])"
# Expected: ~17 TPS
```

### 8. Verify offline operation
```bash
# 1. Ensure model is downloaded
ls model/llama-3.2-1b-instruct-q4_k_m.gguf

# 2. Disable network (Windows: Airplane mode, or unplug Ethernet)

# 3. Run CLI
python src/cli.py

# 4. Add a transaction
ledgermate> add
Enter transaction description: Sold goods for 5000 XAF cash

# 5. Verify balance
ledgermate> balance

# 6. Re-enable network
```

**Expected:** All operations work without network access.

### 9. Verify GitHub repository
Open: https://github.com/penndivinefavour-lab/ledgermate

**Check:**
- [ ] Repository is public
- [ ] `metadata.json` exists at root
- [ ] `download_model.sh` exists at root
- [ ] `REPORT.md` exists at root
- [ ] `.gitignore` exists at root
- [ ] `src/` directory exists
- [ ] `tests/` directory exists
- [ ] No `*.gguf` files visible
- [ ] No `model/` directory visible (should be ignored)
- [ ] Commit history shows unified V2 release

---

## AUTOMATED VERIFICATION SCRIPT

Create `verify_setup.py`:
```python
#!/usr/bin/env python3
"""Verify LedgerMate installation and setup."""
import json
import subprocess
import sys
from pathlib import Path

def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {name}")
    if not condition and detail:
        print(f"  → {detail}")
    return condition

print("=== LedgerMate Verification ===\n")

repo = Path(".")
checks = []

# 1. Check required files
checks.append(check("metadata.json exists", (repo / "metadata.json").exists()))
checks.append(check("download_model.sh exists", (repo / "download_model.sh").exists()))
checks.append(check("REPORT.md exists", (repo / "REPORT.md").exists()))
checks.append(check(".gitignore exists", (repo / ".gitignore").exists()))
checks.append(check("LICENSE exists", (repo / "LICENSE").exists()))

# 2. Check model
model_path = repo / "model" / "llama-3.2-1b-instruct-q4_k_m.gguf"
checks.append(check("Model file exists", model_path.exists(), "Run: bash download_model.sh"))
if model_path.exists():
    size_mb = model_path.stat().st_size / (1024 * 1024)
    checks.append(check(f"Model size OK ({size_mb:.0f} MB)", size_mb > 700))

# 3. Validate metadata
try:
    with open(repo / "metadata.json") as f:
        meta = json.load(f)
    checks.append(check("metadata.json valid JSON", True))
    checks.append(check("team_id present", "team_id" in meta))
    checks.append(check("email present", "submitter" in meta and "email" in meta["submitter"]))
    checks.append(check("Exactly 2 test prompts", len(meta.get("test_prompts", [])) == 2))
    checks.append(check("runtime is llama.cpp", meta.get("model", {}).get("runtime") == "llama.cpp"))
    checks.append(check("quantization is GGUF", "GGUF" in meta.get("model", {}).get("quantization", "")))
except Exception as e:
    checks.append(check("metadata.json valid JSON", False, str(e)))

# 4. Check .gitignore
gitignore = (repo / ".gitignore").read_text()
checks.append(check(".gitignore excludes *.gguf", "*.gguf" in gitignore))
checks.append(check(".gitignore excludes model/", "model/" in gitignore))

# 5. Run tests
print("\n=== Running Tests ===")
try:
    result = subprocess.run(
        [sys.executable, "tests/test_ledgermate.py"],
        capture_output=True, text=True, timeout=30
    )
    checks.append(check("test_ledgermate.py passes", "All tests passed" in result.stdout))
except Exception as e:
    checks.append(check("test_ledgermate.py runs", False, str(e)))

try:
    result = subprocess.run(
        [sys.executable, "tests/test_ledgermate_accuracy.py"],
        capture_output=True, text=True, timeout=30
    )
    checks.append(check("test_ledgermate_accuracy.py passes", "All LedgerMate-specific accuracy tests passed" in result.stdout))
except Exception as e:
    checks.append(check("test_ledgermate_accuracy.py runs", False, str(e)))

try:
    result = subprocess.run(
        [sys.executable, "tests/test_deterministic_safety.py"],
        capture_output=True, text=True, timeout=30
    )
    checks.append(check("test_deterministic_safety.py passes", "All deterministic safety boundary tests passed" in result.stdout))
except Exception as e:
    checks.append(check("test_deterministic_safety.py runs", False, str(e)))

# Summary
print("\n=== Summary ===")
passed = sum(checks)
total = len(checks)
print(f"Passed: {passed}/{total}")

if passed == total:
    print("\n✅ LedgerMate is READY for ADTC 2026 submission.")
    sys.exit(0)
else:
    print("\n❌ Some checks failed. Review the output above.")
    sys.exit(1)
```

**Run it:**
```bash
python verify_setup.py
```

---

## WHAT TO EXPECT

### Successful test output:
```
=== LedgerMate Verification ===

[PASS] metadata.json exists
[PASS] download_model.sh exists
[PASS] REPORT.md exists
[PASS] .gitignore exists
[PASS] LICENSE exists
[PASS] Model file exists
[PASS] Model size OK (771 MB)
[PASS] metadata.json valid JSON
[PASS] team_id present
[PASS] email present
[PASS] Exactly 2 test prompts
[PASS] runtime is llama.cpp
[PASS] quantization is GGUF
[PASS] .gitignore excludes *.gguf
[PASS] .gitignore excludes model/

=== Running Tests ===
[PASS] test_ledgermate.py passes
[PASS] test_ledgermate_accuracy.py passes
[PASS] test_deterministic_safety.py passes

=== Summary ===
Passed: 18/18

✅ LedgerMate is READY for ADTC 2026 submission.
```

### Common issues and fixes:

| Issue | Fix |
|-------|-----|
| `model/ directory missing` | Run `bash download_model.sh` |
| `Model file not found` | Check internet connection, re-run download script |
| `ImportError: No module named 'ledgermate'` | Set `PYTHONPATH=src` |
| `test_ledgermate.py fails` | Ensure dependencies installed: `pip install -r requirements.txt` |
| `llama.cpp not found` | Install llama.cpp or use WSL Ubuntu |
| `submission.json missing` | Run `adtc-profiler run --submission . --mode participant --output submission.json --skip-accuracy` |

---

## WHAT EACH COMPONENT DOES

### Core Engine (V1 - battle-tested)
- `src/ledgermate/schema.py` — Transaction data model with Decimal amounts
- `src/ledgermate/validation.py` — Deterministic validation layer
- `src/ledgermate/ledger.py` — SQLite persistence with append-only audit log
- `src/ledgermate/export.py` — CSV/JSON export
- `src/ledgermate/llm.py` — llama.cpp inference wrapper
- `src/ledgermate/cli.py` — Interactive CLI

### V2 Architecture (new)
- `src/ledgermate/providers/base.py` — Provider-neutral interfaces
- `src/ledgermate/providers/llama_cpp.py` — LLM provider abstraction
- `src/ledgermate/providers/local_stt.py` — STT provider (optional, Windows limitation documented)
- `src/ledgermate/audio/recorder.py` — Audio recording
- `src/ledgermate/audio/states.py` — Voice state machine
- `src/ledgermate/audio/transcript.py` — Transcript editing
- `src/ledgermate/domain/proposal.py` — Transaction proposal with confirmation gate
- `src/ledgermate/agents/registry.py` — Agent registry
- `src/ledgermate/config.py` — Configuration
- `src/ledgermate/__main__.py` — Enhanced CLI with voice workflow

### Tests
- `tests/test_ledgermate.py` — 7 core tests
- `tests/test_ledgermate_accuracy.py` — 14 accuracy tests
- `tests/test_deterministic_safety.py` — 7 safety tests
- `tests/test_v2_baseline.py` — 9 V2 baseline tests
- `tests/test_voice_flow.py` — 5 voice flow tests
- `tests/test_financial_accuracy.py` — 9 financial accuracy tests

---

## VERIFICATION CHECKLIST

Before submitting to ADTC:

- [ ] `git clone` works from clean environment
- [ ] `bash download_model.sh` completes successfully
- [ ] Model file exists at `model/llama-3.2-1b-instruct-q4_k_m.gguf`
- [ ] `pip install -r requirements.txt` succeeds
- [ ] All 51 tests pass
- [ ] `python src/cli.py` launches
- [ ] Can add a transaction via CLI
- [ ] Can query balance
- [ ] Can export to CSV/JSON
- [ ] `metadata.json` has no placeholders
- [ ] `metadata.json` has exactly 2 prompts
- [ ] `submission.json` exists and is valid JSON
- [ ] `.gitignore` excludes `*.gguf` and `model/`
- [ ] No secrets in repository
- [ ] Repository is public on GitHub
- [ ] `REPORT.md` is complete and factual
- [ ] `download_model.sh` is idempotent

---

## IF SOMETHING BREAKS

1. **Tests fail:** Read the error message, fix the code, re-run tests
2. **Model download fails:** Check internet, retry with `wget -c` in WSL
3. **CLI crashes:** Check Python version (3.11+), check dependencies
4. **Profiler fails:** Ensure `llama-bench` is in PATH, use WSL Ubuntu
5. **Import errors:** Ensure `PYTHONPATH=src` is set

---

## FINAL COMMANDS TO RUN NOW

```bash
# 1. Go to repository
cd D:/ADTC2026_RESEARCH/ledgermate

# 2. Verify setup
python verify_setup.py

# 3. Run all tests manually
set PYTHONPATH=src
python tests/test_ledgermate.py
python tests/test_ledgermate_accuracy.py
python tests/test_deterministic_safety.py
python tests/test_v2_baseline.py
python tests/test_voice_flow.py
python tests/test_financial_accuracy.py

# 4. Try the CLI
python src/cli.py
```

That's it. If `verify_setup.py` passes and the CLI launches, LedgerMate is working.
