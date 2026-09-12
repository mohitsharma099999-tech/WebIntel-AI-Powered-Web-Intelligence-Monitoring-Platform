import ipaddress
import socket
from urllib.parse import urlparse

from fastapi import Header, HTTPException, status

from .config import settings


BLOCKED_NETS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),   # AWS metadata
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
]


def assert_public_url(url: str) -> None:
    """Block SSRF to internal / metadata endpoints."""
    host = urlparse(url).hostname
    if not host:
        raise HTTPException(400, "Invalid URL")
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        raise HTTPException(400, f"Cannot resolve host: {host}")

    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if any(ip in net for net in BLOCKED_NETS):
            raise HTTPException(400, f"Blocked internal address: {ip}")


async def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Optional API key check — enabled by setting API_KEY in env."""
    if settings.API_KEY and x_api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
