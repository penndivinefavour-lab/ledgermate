"""LedgerMate V2 — local speech-to-text provider."""
from __future__ import annotations

import subprocess
import tempfile
import threading
from pathlib import Path
from typing import Optional

from ledgermate.providers.base import STTProvider, Transcript


class LocalSTTProvider(STTProvider):
    name = "local_stt"
    available = False
    supports_streaming = False

    def __init__(self, model: str = "tiny") -> None:
        self.model = model
        self._check_availability()

    def _check_availability(self) -> None:
        try:
            subprocess.run(["whisper", "--help"], capture_output=True, check=True)
            self.available = True
        except (FileNotFoundError, subprocess.CalledProcessError):
            self.available = False

    def transcribe(self, audio_path: Path) -> Transcript:
        if not self.available:
            raise RuntimeError("Whisper is not installed or unavailable")
        with tempfile.TemporaryDirectory() as tmpdir:
            proc = subprocess.run(
                ["whisper", str(audio_path), "--model", self.model, "--output_dir", tmpdir, "--output_format", "txt"],
                capture_output=True,
                text=True,
                check=True,
                timeout=300,
            )
            txt_path = Path(tmpdir) / (audio_path.stem + ".txt")
            text = txt_path.read_text(encoding="utf-8").strip() if txt_path.exists() else ""
        return Transcript(raw=text, current=text, edited=None, final=None)

    def transcribe_stream(self, audio_path: Path) -> Transcript:
        return self.transcribe(audio_path)
