"""Extract public emails from business websites."""

from __future__ import annotations

import re
from html import unescape
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

EMAIL_RE = re.compile(
    r"(?:mailto:)?([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})",
    re.IGNORECASE,
)

# Ignore tracking / template / placeholder emails
SKIP_DOMAINS = {
    "example.com",
    "example.org",
    "domain.com",
    "email.com",
    "sentry.io",
    "wixpress.com",
    "sentry-next.wixpress.com",
    "googleapis.com",
    "google.com",
    "gstatic.com",
    "cloudflare.com",
    "schema.org",
    "w3.org",
    "jquery.com",
    "wordpress.org",
    "wordpress.com",
    "squarespace.com",
    "godaddy.com",
    "shopify.com",
    "myshopify.com",
}

SKIP_PREFIXES = (
    "noreply@",
    "no-reply@",
    "donotreply@",
    "do-not-reply@",
    "mailer-daemon@",
    "postmaster@",
    "webmaster@",
)

CONTACT_PATHS = (
    "",
    "/contact",
    "/contact-us",
    "/contactus",
    "/about",
    "/about-us",
)


def _is_valid_email(email: str) -> bool:
    email = email.strip().lower()
    if "@" not in email or "." not in email.split("@")[-1]:
        return False
    if email.startswith(SKIP_PREFIXES):
        return False
    domain = email.split("@", 1)[1]
    if domain in SKIP_DOMAINS:
        return False
    if any(domain.endswith("." + d) for d in SKIP_DOMAINS):
        return False
    # Skip image/file-looking emails
    if email.endswith((".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".css", ".js")):
        return False
    return True


def _fetch_html(url: str, timeout: int = 8) -> str:
    req = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml",
        },
        method="GET",
    )
    with urlopen(req, timeout=timeout) as resp:
        raw = resp.read(400_000)  # cap ~400KB
        charset = "utf-8"
        content_type = resp.headers.get_content_charset()
        if content_type:
            charset = content_type
        return raw.decode(charset, errors="ignore")


def _emails_from_html(html: str) -> list[str]:
    text = unescape(html)
    found: list[str] = []
    seen: set[str] = set()
    for match in EMAIL_RE.finditer(text):
        email = match.group(1).strip().lower()
        if email in seen or not _is_valid_email(email):
            continue
        seen.add(email)
        found.append(email)
    return found


def _prefer_business_email(emails: list[str], website: str) -> str:
    if not emails:
        return ""
    host = ""
    try:
        host = urlparse(website).netloc.lower().removeprefix("www.")
    except Exception:
        pass

    # Prefer emails matching the website domain
    if host:
        for email in emails:
            domain = email.split("@", 1)[1]
            if host == domain or host.endswith("." + domain) or domain.endswith("." + host):
                return email

    # Prefer info/contact/service style addresses
    for prefix in ("info@", "contact@", "service@", "sales@", "office@", "hello@", "support@"):
        for email in emails:
            if email.startswith(prefix):
                return email

    return emails[0]


def find_email_from_website(website: str) -> str:
    """Visit business website (homepage + contact pages) and return best public email."""
    if not website:
        return ""

    website = website.strip()
    if website.startswith("//"):
        website = "https:" + website
    if not website.startswith(("http://", "https://")):
        website = "https://" + website

    parsed = urlparse(website)
    if not parsed.netloc:
        return ""

    base = f"{parsed.scheme}://{parsed.netloc}"
    collected: list[str] = []

    for path in CONTACT_PATHS:
        url = urljoin(base + "/", path.lstrip("/")) if path else website
        try:
            html = _fetch_html(url)
        except (HTTPError, URLError, TimeoutError, OSError, ValueError):
            continue
        except Exception:
            continue

        emails = _emails_from_html(html)
        for email in emails:
            if email not in collected:
                collected.append(email)

        # Stop early if we already have a good match
        best = _prefer_business_email(collected, website)
        if best and (best.split("@")[1] in urlparse(website).netloc.lower() or best.startswith(("info@", "contact@"))):
            return best

    return _prefer_business_email(collected, website)
