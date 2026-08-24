"""LedgerMate CLI — package entry bridge."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from ledgermate.cli import run_cli

if __name__ == "__main__":
    run_cli()
