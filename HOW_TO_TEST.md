# LedgerMate — How to Test and Verify (Windows-First)
## Date: 2026-08-24
## Repository: https://github.com/penndivinefavour-lab/ledgermate

---

## STOP — READ THIS FIRST

**Before doing anything:**

1. **DO NOT** run `git clone` inside an existing LedgerMate folder.
   - If you already have `D:/ADTC2026_RESEARCH/ledgermate/`, do NOT clone into it.
   - Use a **fresh empty folder** like `D:/ADTC2026_RESEARCH/ledgermate-test/`
2. **DO NOT** use `python` in PowerShell — it does not exist on this machine.
3. **DO NOT** run `bash download_model.sh` in PowerShell — Bash is unavailable here.
4. **DO** use the commands exactly as written below.

---

## WHAT YOU WILL NEED

- **Python 3.11+** installed (https://www.python.org/downloads/)
- **Git for Windows** installed (https://git-scm.com/download/win)
- **Internet connection** for the initial model download only
- **8 GB free disk space** for the model file

---

## STEP 1 — CHECK PYTHON

Open **PowerShell** and run:

```powershell
py --version
```

**Expected:** `Python 3.11.16` or higher

**If you see an error:**
- Install Python from https://www.python.org/downloads/
- During install, check **"Add Python to PATH"**
- Close PowerShell and reopen it
- Run `py --version` again

---

## STEP 2 — GET THE REPOSITORY

### Option A: Download as ZIP (easiest)

1. Go to https://github.com/penndivinefavour-lab/ledgermate
2. Click the green **Code** button
3. Click **Download ZIP**
4. Extract the ZIP to `D:/ADTC2026_RESEARCH/ledgermate-test/`
5. Open PowerShell in that folder:
   ```powershell
   cd D:/ADTC2026_RESEARCH/ledgermate-test/ledgermate
   ```

### Option B: Clone with Git (if you know Git)

1. Open PowerShell in an **empty** folder:
   ```powershell
   cd D:/ADTC2026_RESEARCH/ledgermate-test
   git clone https://github.com/penndivinefavour-lab/ledgermate.git
   cd ledgermate
   ```

**IMPORTANT:** Do NOT run `git clone` inside an existing `ledgermate` folder. That creates a nested repository and breaks everything.

---

## STEP 3 — INSTALL DEPENDENCIES

In PowerShell, in the repository folder:

```powershell
py -m pip install -r requirements.txt
```

**Expected:** Installation completes without errors.

**Note:** This installs LedgerMate's Python dependencies, not the model.

---

## STEP 4 — DOWNLOAD THE MODEL

### Method A: Use Git Bash (preferred on Windows)

1. Right-click in the repository folder → **"Git Bash Here"**
2. Run:
   ```bash
   bash download_model.sh
   ```
3. Wait for download to complete (~771 MB)

**Expected output:**
```
Downloading https://huggingface.co/.../llama-3.2-1b-instruct-q4_k_m.gguf ...
Downloaded to model/llama-3.2-1b-instruct-q4_k_m.gguf
Verifying file...
Model file ready.
```

### Method B: PowerShell direct download (if Git Bash fails)

```powershell
$ProgressPreference = 'SilentlyContinue'
$url = "https://huggingface.co/hugging-quants/Llama-3.2-1B-Instruct-Q4_K_M-GGUF/resolve/main/llama-3.2-1b-instruct-q4_k_m.gguf"
$out = "D:/ADTC2026_RESEARCH/ledgermate/model/llama-3.2-1b-instruct-q4_k_m.gguf"
New-Item -ItemType Directory -Force -Path (Split-Path $out) | Out-Null
Invoke-WebRequest -Uri $url -OutFile $out
```

**Expected:** File appears at `model/llama-3.2-1b-instruct-q4_k_m.gguf`, ~771 MB

---

## STEP 5 — VERIFY SETUP

In PowerShell, in the repository folder:

```powershell
py verify_setup.py
```

**Expected output:**
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

**If this passes, LedgerMate is working. You're done.**

---

## STEP 6 — RUN TESTS MANUALLY (OPTIONAL)

If you want to run individual tests:

```powershell
$env:PYTHONPATH = "src"
py tests/test_ledgermate.py
py tests/test_ledgermate_accuracy.py
py tests/test_deterministic_safety.py
py tests/test_v2_baseline.py
py tests/test_voice_flow.py
py tests/test_financial_accuracy.py
```

**Expected:** Each says "passed" at the end.

---

## STEP 7 — TRY THE CLI (OPTIONAL)

```powershell
$env:PYTHONPATH = "src"
py src/cli.py
```

You should see:
```
ledgermate>
```

Try these commands:
```
ledgermate> help
ledgermate> balance
ledgermate> list
ledgermate> exit
```

---

## WHAT IF SOMETHING FAILS?

### "py : The term 'py' is not recognized"
- Python is not installed or not in PATH
- Install Python from https://www.python.org/downloads/
- Check "Add Python to PATH" during installation
- Restart PowerShell

### "pip install fails"
- Some packages require C++ compiler
- This is normal on Windows; core LedgerMate tests do not need those packages
- If `verify_setup.py` passes, you're fine

### "download_model.sh fails in PowerShell"
- PowerShell cannot run Bash scripts
- Use **Git Bash** (right-click → Git Bash Here)
- Or use the PowerShell direct download method in Step 4

### "ImportError: No module named 'ledgermate'"
- Set PYTHONPATH: `$env:PYTHONPATH = "src"`
- Or use: `py -m pytest tests/` from the repository root

### "model/ directory missing after download"
- Check internet connection
- Check disk space (need ~1 GB free)
- Try the PowerShell direct download method

---

## WHAT SUCCESS LOOKS LIKE

1. ✅ `py verify_setup.py` shows 18/18 checks passing
2. ✅ All 6 test files report "passed"
3. ✅ `py src/cli.py` starts without errors
4. ✅ Model file exists at `model/llama-3.2-1b-instruct-q4_k_m.gguf` (~771 MB)

---

## WHAT TO SEND HERMES IF SOMETHING BREAKS

If any step fails, copy and send:

1. The exact command you ran
2. The exact error message
3. The output of `py --version`
4. The output of `git --version`

Do not summarize — copy the exact text from PowerShell.

---

## IMPORTANT NOTES FOR COMPETITION

- The ADTC evaluator runs in a **Linux VM** with proper Bash and Python
- Your Windows testing experience does not affect competition evaluation
- The competition requires `bash download_model.sh` — test that in Git Bash or WSL
- Voice/STT features are **optional** and do not affect ADTC submission
- The core bookkeeping engine works 100% offline after model download

---

## FILES YOU SHOULD SEE

After successful setup:
```
ledgermate/
├── metadata.json          ← Team info, prompts
├── download_model.sh      ← Model download script
├── REPORT.md              ← Technical report
├── README.md              ← Project overview
├── .gitignore             ← Git ignore rules
├── LICENSE                ← MIT License
├── MODEL_ATTRIBUTION.md   ← Model license
├── submission.json        ← Profiler output
├── BENCHMARKS.md          ← Benchmark results
├── verify_setup.py        ← Verification script
├── HOW_TO_TEST.md         ← This file
├── src/ledgermate/        ← Source code
├── tests/                 ← Test suite
├── docs/                  ← Documentation
└── model/                 ← Model weights (downloaded, not in Git)
    └── llama-3.2-1b-instruct-q4_k_m.gguf
```

**Do NOT see:**
- `*.gguf` files in Git (they are ignored)
- `model/` directory in GitHub (it is ignored)
- Nested `ledgermate/ledgermate/` folders
