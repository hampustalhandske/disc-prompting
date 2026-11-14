"""Makes every socket connection and DNS lookup fail, and logs each attempt.

When the env var NETBLOCK_LOG names a file, one line per attempt is appended to it, so a
caller that swallows the error still leaves evidence.
"""
import os
import socket


def _blocked(*args, **kwargs):
    log = os.environ.get("NETBLOCK_LOG")
    if log:
        with open(log, "a") as f:
            f.write(f"{args[:2]}\n")
    raise RuntimeError("network access is blocked in tests")


socket.socket.connect = _blocked
socket.socket.connect_ex = _blocked
socket.getaddrinfo = _blocked
