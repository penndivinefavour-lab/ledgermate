"""Regression tests for llama.cpp executable discovery on Windows."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ledgermate.llm import _find_llama_executable, _validate_llama_executable


def test_find_llama_executable_returns_llama_cli():
    exe = _find_llama_executable()
    assert exe.endswith("llama-cli.exe") or exe.endswith("llama-cli")


def test_find_llama_executable_never_returns_cpl():
    exe = _find_llama_executable()
    assert not exe.lower().endswith(".cpl")


def test_validate_llama_executable_rejects_cpl():
    try:
        _validate_llama_executable("C:\Windows\System32\main.cpl")
        assert False, "Should have rejected .cpl file"
    except RuntimeError as exc:
        assert "Invalid llama.cpp executable" in str(exc)


def test_validate_llama_executable_rejects_nonexistent():
    try:
        _validate_llama_executable("C:\nonexistent\llama-cli.exe")
        assert False, "Should have rejected nonexistent path"
    except RuntimeError as exc:
        assert "not found" in str(exc)


def test_validate_llama_executable_rejects_directory():
    try:
        _validate_llama_executable("C:\Windows\System32")
        assert False, "Should have rejected directory"
    except RuntimeError as exc:
        assert "directory" in str(exc).lower()


if __name__ == "__main__":
    tests = [v for k, v in sorted(locals().items()) if k.startswith("test_") and callable(v)]
    failures = 0
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
        except Exception as exc:
            print(f"FAIL {test.__name__}: {exc}")
            failures += 1
    print(f"Results: {len(tests) - failures}/{len(tests)} passed")
    raise SystemExit(1 if failures else 0)
