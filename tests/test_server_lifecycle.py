"""Server lifecycle and port-handling tests."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ledgermate.api import _port_in_use, _safe_default_port


def test_safe_default_port_uses_preferred_when_available():
    s = __import__("socket").socket(__import__("socket").AF_INET, __import__("socket").SOCK_STREAM)
    s.setsockopt(__import__("socket").SOL_SOCKET, __import__("socket").SO_REUSEADDR, 1)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    try:
        host, chosen = _safe_default_port("127.0.0.1", port)
    finally:
        s.close()
    assert host == "127.0.0.1"
    assert chosen == port


def test_safe_default_port_falls_back_when_preferred_is_occupied():
    s = __import__("socket").socket(__import__("socket").AF_INET, __import__("socket").SOCK_STREAM)
    s.setsockopt(__import__("socket").SOL_SOCKET, __import__("socket").SO_REUSEADDR, 1)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.listen(1)
    try:
        host, chosen = _safe_default_port("127.0.0.1", port)
    finally:
        s.close()
    assert host == "127.0.0.1"
    assert chosen != port
