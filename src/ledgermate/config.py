"""LedgerMate V2 — configuration management."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    data_dir: Path = Path(__file__).resolve().parents[2] / "data"
    db_path: Path = Path(__file__).resolve().parents[2] / "data" / "ledger.db"
    exports_dir: Path = Path(__file__).resolve().parents[2] / "exports"
    model_path: Path = Path(__file__).resolve().parents[2] / "model" / "llama-3.2-1b-instruct-q4_k_m.gguf"
    audio_dir: Path = Path(__file__).resolve().parents[2] / "data" / "audio"
    default_currency: str = "XAF"
    date_format: str = "%Y-%m-%d"

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.exports_dir.mkdir(parents=True, exist_ok=True)
        self.audio_dir.mkdir(parents=True, exist_ok=True)
