# LedgerMate — Python Environment Guide
## Date: 2026-08-24

## Supported Python Versions

- **Primary:** Python 3.12 (tested, recommended)
- **Also compatible:** Python 3.11
- **Not recommended for development:** Python 3.13, 3.14 (may have dependency compatibility issues)

## Verified Environment

**Machine:** Dell Vostro 3500, Windows 11 Pro  
**Python:** 3.12.10 (via py launcher or direct install)  
**Virtual environment:** `.venv312/` (project-local)  
**pip:** 25.0.1  

## Quick Setup

```powershell
# 1. Verify Python 3.12
py -3.12 --version

# 2. Create virtual environment
py -3.12 -m venv .venv312

# 3. Activate
.venv312\Scripts\Activate.ps1

# 4. Install dependencies
pip install -r requirements.txt

# 5. Verify
python --version
pip list
```

## Running Tests

```powershell
# From activated .venv312
python tests/test_ledgermate.py
python tests/test_ledgermate_accuracy.py
python tests/test_deterministic_safety.py
python tests/test_v2_baseline.py
python tests/test_voice_flow.py
python tests/test_financial_accuracy.py
```

## Running the CLI

```powershell
# From activated .venv312
python src/ledgermate/cli.py
```

## Running Verification

```powershell
# From activated .venv312
python verify_setup.py
```

## Windows Notes

- Use `py -3.12` to explicitly invoke Python 3.12
- If `python` points to 3.14, use the full path: `C:\Users\USER\AppData\Local\Programs\Python\Python312\python.exe`
- PowerShell may block venv activation; run: `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`

## WSL Notes

- WSL Ubuntu 22.04 available but stopped
- For competition profiling, use WSL with llama.cpp build
- Windows testing uses native Python 3.12 + .venv312

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| python-dotenv | >=1.0.0 | Config loading |
| pydantic | >=2.0.0 | Data validation |
| rich | >=13.0.0 | TUI formatting |
| sounddevice | >=0.4.6 | Audio recording (optional) |
| numpy | >=1.24.0 | Audio processing (optional) |

**Note:** `llama-cpp-python` is NOT required for LedgerMate. The project uses the `llama-cli` subprocess directly, not the Python binding.

## Known Limitations

- Whisper CLI hangs on Windows (documented in STT_LIMITATION.md)
- llama-cpp-python cannot build on Windows without C++ toolchain (not needed)
- WSL distributions are stopped by default; start with `wsl --start` if needed
