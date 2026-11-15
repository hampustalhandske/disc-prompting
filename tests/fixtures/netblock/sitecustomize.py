"""Makes every socket connection and DNS lookup fail, and logs each attempt.

When the env var NETBLOCK_LOG names a file, one line per attempt is appended to it, so a
caller that swallows the error still leaves evidence. When NETBLOCK_LOADED names a file,
it is created on import, so a test can prove the blocker was active.
"""
import os
import socket

if os.environ.get("NETBLOCK_LOADED"):
    open(os.environ["NETBLOCK_LOADED"], "w").close()


def _blocked(*args, **kwargs):
    log = os.environ.get("NETBLOCK_LOG")
    if log:
        with open(log, "a") as f:
            f.write(f"{args[:2]}\n")
    raise RuntimeError("network access is blocked in tests")


socket.socket.connect = _blocked
socket.socket.connect_ex = _blocked
socket.getaddrinfo = _blocked
