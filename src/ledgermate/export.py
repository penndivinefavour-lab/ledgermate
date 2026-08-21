"""CSV and JSON export utilities."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable


def export_csv(transactions: Iterable[dict], path: str | Path) -> Path:
    rows = list(transactions)
    if not rows:
        raise ValueError("No transactions to export")
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return out


def export_json(transactions: Iterable[dict], path: str | Path) -> Path:
    rows = list(transactions)
    if not rows:
        raise ValueError("No transactions to export")
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    return out
