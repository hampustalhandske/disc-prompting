"""Makes every socket connection and DNS lookup fail, so a network call is a test failure."""
import socket


def _blocked(*args, **kwargs):
    raise RuntimeError("network access is blocked in tests")


socket.socket.connect = _blocked
socket.socket.connect_ex = _blocked
socket.getaddrinfo = _blocked
