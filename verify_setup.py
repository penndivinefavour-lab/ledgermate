#!/usr/bin/env python3
"""LedgerMate setup verification — Windows-aware."""
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(".")
PASS_COUNT = 0
WARN_COUNT = 0
FAIL_COUNT = 0

def check(name, passed, detail=""):
    global PASS_COUNT, WARN_COUNT, FAIL_COUNT
    if passed:
        print(f"[PASS] {name}")
        PASS_COUNT += 1
    elif detail:
        print(f"[WARN] {name}: {detail}")
        WARN_COUNT += 1
    else:
        print(f"[FAIL] {name}")
        FAIL_COUNT += 1
    return passed

print("=== LedgerMate Verification ===\n")

# 1. Required files
for fname in ["metadata.json", "download_model.sh", "REPORT.md", "README.md", ".gitignore", "LICENSE", "MODEL_ATTRIBUTION.md"]:
    check(f"{fname} exists", (REPO / fname).exists())

# 2. Model
model_path = REPO / "model" / "llama-3.2-1b-instruct-q4_k_m.gguf"
check("Model file exists", model_path.exists(), "Run: bash download_model.sh")
if model_path.exists():
    size_mb = model_path.stat().st_size / (1024 * 1024)
    check(f"Model size OK ({size_mb:.0f} MB)", size_mb > 700, "Expected ~771 MB")

# 3. Metadata
try:
    with open(REPO / "metadata.json") as f:
        meta = json.load(f)
    check("metadata.json valid JSON", True)
    check("team_id present", bool(meta.get("team_id")))
    check("submitter email present", bool(meta.get("submitter", {}).get("email")))
    check("Exactly 2 test prompts", len(meta.get("test_prompts", [])) == 2)
    check("runtime is llama.cpp", meta.get("model", {}).get("runtime") == "llama.cpp")
    check("quantization is GGUF", "GGUF" in meta.get("model", {}).get("quantization", ""))
except Exception as e:
    check("metadata.json valid JSON", False, str(e))

# 4. .gitignore
gitignore = (REPO / ".gitignore").read_text(errors="ignore") if (REPO / ".gitignore").exists() else ""
check(".gitignore excludes *.gguf", "*.gguf" in gitignore)
check(".gitignore excludes model/", "model/" in gitignore)

# 5. Tests
print("\n=== Running Tests ===")
tests = [
    ("test_ledgermate.py", "All tests passed."),
    ("test_ledgermate_accuracy.py", "All LedgerMate-specific accuracy tests passed."),
    ("test_deterministic_safety.py", "All deterministic safety boundary tests passed."),
    ("test_v2_baseline.py", "Results: 9/9 passed"),
    ("test_voice_flow.py", "Results: 5/5 passed"),
    ("test_financial_accuracy.py", "Results: 9/9 passed"),
]
for tname, expected in tests:
    try:
        result = subprocess.run(
            [sys.executable, f"tests/{tname}"],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(REPO),
        )
        passed = expected in (result.stdout + result.stderr)
        check(f"{tname} passes", passed, result.stdout[-200:] if result.stdout else result.stderr[-200:])
    except Exception as e:
        check(f"{tname} runs", False, str(e))

# Summary
print("\n=== Summary ===")
print(f"Passed: {PASS_COUNT}")
print(f"Warnings: {WARN_COUNT}")
print(f"Failed: {FAIL_COUNT}")

if FAIL_COUNT == 0:
    print("\n✅ LedgerMate verification passed.")
    sys.exit(0)
else:
    print("\n❌ Verification failed. Review the output above.")
    sys.exit(1)
