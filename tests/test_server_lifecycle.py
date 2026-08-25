"""Server lifecycle and port-handling tests."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import socket
from ledgermate.api import _can_bind, _safe_default_port


def test_can_bind_reflects_real_bind_state():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.listen(1)
    try:
        assert _can_bind("127.0.0.1", port) is False
    finally:
        s.close()
    assert _can_bind("127.0.0.1", port) is True


def test_safe_default_port_uses_preferred_when_available():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    host, chosen = _safe_default_port("127.0.0.1", port)
    assert host == "127.0.0.1"
    assert chosen == port


def test_safe_default_port_falls_back_when_preferred_is_occupied():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.listen(1)
    try:
        host, chosen = _safe_default_port("127.0.0.1", port)
    finally:
        s.close()
    assert host == "127.0.0.1"
    assert chosen != port
