"""Server lifecycle and port-handling tests."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import socket
from ledgermate.api import _port_in_use, _safe_default_port


def test_can_bind_reflects_real_bind_state():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.listen(1)
    try:
        assert _port_in_use("127.0.0.1", port) is True
    finally:
        s.close()
    assert _port_in_use("127.0.0.1", port) is False


def test_safe_default_port_uses_preferred_when_available():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    host, chosen = _safe_default_port("127.0.0.1", port)
    assert host == "127.0.0.1"
    assert chosen == port


def test_safe_default_port_falls_back_when_preferred_is_occupied():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.listen(1)
    try:
        host, chosen = _safe_default_port("127.0.0.1", port)
    finally:
        s.close()
    assert host == "127.0.0.1"
    assert chosen != port
