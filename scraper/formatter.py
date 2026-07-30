"""Clean and organize scraped business data for CSV/Excel export."""

from __future__ import annotations

import re
from typing import Any

# Strip icon / private-use unicode from Google Maps UI text
_ICON_RE = re.compile(r"[\ue000-\uf8ff\u200b-\u200f\ufeff]")
_WS_RE = re.compile(r"\s+")

_PHONE_DIGITS_RE = re.compile(r"\D")
_US_PHONE_RE = re.compile(
    r"^\+?1?[-.\s]?\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})$"
)

_ADDRESS_RE = re.compile(
    r"^(?P<street>.+?),\s*(?P<city>[^,]+),\s*(?P<state>[A-Z]{2})\s*"
    r"(?P<zip>\d{5}(?:-\d{4})?)?(?:,.*)?$",
    re.IGNORECASE,
)


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    text = _ICON_RE.sub("", text)
    text = text.replace("\r\n", " ").replace("\n", " ").replace("\r", " ")
    text = _WS_RE.sub(" ", text).strip()
    return text


def format_phone(raw: Any) -> str:
    text = clean_text(raw)
    if not text:
        return ""

    digits = _PHONE_DIGITS_RE.sub("", text)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) == 10:
        return f"({digits[0:3]}) {digits[3:6]}-{digits[6:10]}"

    match = _US_PHONE_RE.match(text)
    if match:
        return f"({match.group(1)}) {match.group(2)}-{match.group(3)}"
    return text


def format_website(raw: Any) -> str:
    url = clean_text(raw)
    if not url:
        return ""
    if url.startswith("//"):
        return f"https:{url}"
    return url


def parse_address(raw: Any) -> dict[str, str]:
    address = clean_text(raw)
    result = {"address": address, "street": "", "city": "", "state": "", "zip": ""}
    if not address:
        return result

    match = _ADDRESS_RE.match(address)
    if match:
        result["street"] = match.group("street").strip()
        result["city"] = match.group("city").strip()
        result["state"] = match.group("state").upper()
        result["zip"] = (match.group("zip") or "").strip()
    return result


def format_hours(raw: Any) -> tuple[str, str]:
    """Return (status, detail) e.g. ('Open', 'Closes 5:30 PM')."""
    text = clean_text(raw)
    if not text:
        return "", ""

    lowered = text.lower()
    if lowered.startswith("hours:"):
        text = text[6:].strip()
    if lowered.startswith("hours "):
        text = text[6:].strip()

    # Common patterns: "Open · Closes 5:30 PM" or "Open 24 hours"
    if "·" in text:
        parts = [p.strip() for p in text.split("·") if p.strip()]
        if len(parts) >= 2:
            return parts[0], " · ".join(parts[1:])
        if parts:
            return parts[0], ""

    if text.lower().startswith("open"):
        return "Open", text[4:].strip(" ·-") if len(text) > 4 else ""
    if text.lower().startswith("closed"):
        return "Closed", text[6:].strip(" ·-") if len(text) > 6 else ""

    return text, ""


def normalize_row(row: dict[str, Any]) -> dict[str, str]:
    """Normalize one business record for organized CSV/Excel output."""
    place = clean_text(row.get("search_place") or row.get("search_city", ""))
    search_state = clean_text(row.get("search_state", "")).upper()
    addr_parts = parse_address(row.get("address", ""))

    hours_status, hours_detail = format_hours(row.get("hours", ""))

    rating = clean_text(row.get("rating", ""))
    reviews = clean_text(row.get("review_count", ""))
    if reviews.isdigit():
        reviews = str(int(reviews))

    normalized = {
        "name": clean_text(row.get("name", "")),
        "phone": format_phone(row.get("phone", "")),
        "website": format_website(row.get("website", "")),
        "email": clean_text(row.get("email", "")),
        "address": addr_parts["address"],
        "street": addr_parts["street"],
        "city": addr_parts["city"],
        "state": addr_parts["state"] or search_state,
        "zip": addr_parts["zip"],
        "rating": rating,
        "review_count": reviews,
        "category": clean_text(row.get("category", "")),
        "hours_status": hours_status,
        "hours_detail": hours_detail,
        "google_maps_url": clean_text(row.get("google_maps_url", "")),
        "search_keyword": clean_text(row.get("search_keyword", "")),
        "search_place": place,
        "search_type": clean_text(row.get("search_type", "city")) or "city",
        "search_state": search_state,
        "scraped_at": clean_text(row.get("scraped_at", "")),
        "place_id": clean_text(row.get("place_id", "")),
    }
    return normalized
