import ipaddress
import socket
from urllib.parse import urlparse


def normalize_domain(url_or_domain: str) -> str:
    """Extract and normalize a domain from a URL or bare domain string.

    Returns a lowercase domain without www prefix, port, or path.
    Handles punycode (IDN) domains.
    """
    text = url_or_domain.strip()
    if not text:
        raise ValueError("Empty URL/domain")

    # Add scheme if missing so urlparse works
    if "://" not in text:
        text = "https://" + text

    parsed = urlparse(text)
    host = parsed.hostname
    if not host:
        raise ValueError(f"Cannot extract domain from: {url_or_domain}")

    # Encode IDN to punycode then back to get canonical form
    try:
        host = host.encode("idna").decode("ascii")
    except (UnicodeError, UnicodeDecodeError):
        pass  # already ASCII or invalid — keep as-is

    host = host.lower()
    if host.startswith("www."):
        host = host[4:]

    return host


def check_ssrf(domain: str) -> None:
    """Block requests to private/reserved IP ranges and localhost."""
    blocked_hosts = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}
    if domain in blocked_hosts:
        raise ValueError(f"Blocked domain (loopback): {domain}")

    try:
        infos = socket.getaddrinfo(domain, None)
    except socket.gaierror:
        return  # DNS failure — let the caller handle connection errors

    for family, _, _, _, sockaddr in infos:
        ip_str = sockaddr[0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            continue
        if ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local:
            raise ValueError(f"Blocked domain (resolves to private IP {ip_str}): {domain}")
