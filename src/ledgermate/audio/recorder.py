"""LedgerMate V2 — audio recording module."""
from __future__ import annotations

import queue
import threading
import wave
from pathlib import Path
from typing import Optional

import numpy as np

try:
    import sounddevice as sd

    AUDIO_AVAILABLE = True
except (ImportError, OSError):
    AUDIO_AVAILABLE = False

from ledgermate.config import Config


class AudioRecorder:
    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config()
        self._queue: queue.Queue[np.ndarray] = queue.Queue()
        self._stream: Optional[sd.InputStream] = None
        self._recording = False
        self._sample_rate = 16000
        self._channels = 1

    def _callback(self, indata, frames, time_info, status):
        if status:
            pass
        self._queue.put(indata.copy())

    def start(self, output_path: Path | None = None) -> Path:
        if not AUDIO_AVAILABLE:
            raise RuntimeError("sounddevice is not installed; audio recording unavailable")
        output_path = output_path or self.config.audio_dir / f"recording_{Path(__file__).stat().st_mtime_ns}.wav"
        self._output_path = output_path
        self._recording = True
        self._queue = queue.Queue()
        self._stream = sd.InputStream(
            samplerate=self._sample_rate, channels=self._channels, dtype="int16", callback=self._callback
        )
        self._stream.start()
        return output_path

    def stop(self) -> Path:
        if not self._stream:
            raise RuntimeError("Recording not started")
        self._recording = False
        self._stream.stop()
        self._stream.close()
        frames = []
        while not self._queue.empty():
            frames.append(self._queue.get())
        if frames:
            audio = np.concatenate(frames, axis=0)
            with wave.open(str(self._output_path), "wb") as wf:
                wf.setnchannels(self._channels)
                wf.setsampwidth(2)
                wf.setframerate(self._sample_rate)
                wf.writeframes(audio.tobytes())
        return self._output_path

    def cancel(self) -> None:
        if self._stream:
            self._recording = False
            self._stream.stop()
            self._stream.close()
            self._stream = None
        if hasattr(self, "_output_path") and self._output_path.exists():
            self._output_path.unlink()

    @property
    def available(self) -> bool:
        return AUDIO_AVAILABLE
