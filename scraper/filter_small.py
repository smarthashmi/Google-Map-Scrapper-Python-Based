"""Filter out Inc/Corp businesses — keep small shops easy to dial."""

from __future__ import annotations

import csv
import re
from pathlib import Path

from scraper.formatter import normalize_row
from scraper.organize import _dedupe_rows, _write_xlsx
from scraper.storage import BY_STATE_DIR, CSV_COLUMNS, DATA_DIR

SMALL_DIR = DATA_DIR / "by_state_small"
REMOVED_DIR = DATA_DIR / "by_state_removed_corp"

# Match corporate legal endings in business names
CORP_NAME_RE = re.compile(
    r"""
    (?:^|[\s,.\-/&(])
    (?:
        Inc\.? |
        Incorporated |
        Corp\.? |
        Corporation |
        Ltd\.? |
        Limited |
        PLC |
        P\.?C\.? |
        Holdings |
        Enterprises? \s+ Inc\.? |
        Group \s+ Inc\.?
    )
    (?:$|[\s,.\-/&)] )
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Extra brand/corporate keywords often not small local shops
CORP_KEYWORDS_RE = re.compile(
    r"\b("
    r"pep\s*boys|jiffy\s*lube|midas|firestone|goodyear|"
    r"discount\s*tire|les\s*schwab|valvoline|meineke|"
    r"aamco|monro|take\s*5|oil\s*can\s*henry|"
    r"napa\s*auto\s*parts|autozone|o'?reilly|"
    r"walmart|costco|sears|dealer\s*group"
    r")\b",
    re.IGNORECASE,
)


def is_corporate(name: str) -> bool:
    text = (name or "").strip()
    if not text:
        return False
    if CORP_NAME_RE.search(text):
        return True
    if CORP_KEYWORDS_RE.search(text):
        return True
    return False


def has_phone(row: dict[str, str]) -> bool:
    phone = re.sub(r"\D", "", row.get("phone") or "")
    return len(phone) >= 10


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def filter_rows(
    rows: list[dict[str, str]],
    require_phone: bool = True,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    keep: list[dict[str, str]] = []
    removed: list[dict[str, str]] = []

    for row in rows:
        clean = normalize_row(row)
        name = clean.get("name", "")
        if is_corporate(name):
            removed.append(clean)
            continue
        if require_phone and not has_phone(clean):
            removed.append(clean)
            continue
        keep.append(clean)

    keep = _dedupe_rows(keep)
    removed = _dedupe_rows(removed)
    keep.sort(key=lambda r: (r.get("state", ""), r.get("city", ""), r.get("name", "")))
    return keep, removed


def run(require_phone: bool = True) -> None:
    SMALL_DIR.mkdir(parents=True, exist_ok=True)
    REMOVED_DIR.mkdir(parents=True, exist_ok=True)

    sources = sorted(BY_STATE_DIR.glob("*.csv")) if BY_STATE_DIR.exists() else []
    if not sources:
        print("No files in data/by_state/. Run build_state_files.bat first.")
        return

    all_keep: list[dict[str, str]] = []
    all_removed: list[dict[str, str]] = []
    total_in = 0

    print("Filtering Inc / Corp / chain businesses...")
    if require_phone:
        print("Also keeping only leads with a phone number (easy to dial).")
    print()

    for src in sources:
        rows = _read_csv(src)
        total_in += len(rows)
        keep, removed = filter_rows(rows, require_phone=require_phone)

        _write_csv(SMALL_DIR / src.name, keep)
        _write_csv(REMOVED_DIR / src.name, removed)

        all_keep.extend(keep)
        all_removed.extend(removed)
        print(f"  {src.name:12}  in={len(rows):5}  keep={len(keep):5}  removed={len(removed):5}")

    all_keep = _dedupe_rows(all_keep)
    all_keep.sort(key=lambda r: (r.get("state", ""), r.get("city", ""), r.get("name", "")))
    all_removed = _dedupe_rows(all_removed)

    combined = DATA_DIR / "SMALL_BUSINESSES_DIAL.csv"
    removed_combined = DATA_DIR / "REMOVED_INC_CORP.csv"
    _write_csv(combined, all_keep)
    _write_csv(removed_combined, all_removed)

    xlsx = DATA_DIR / "SMALL_BUSINESSES_DIAL.xlsx"
    try:
        _write_xlsx(all_keep, xlsx)
    except Exception as exc:
        print(f"Excel skipped: {exc}")
        xlsx = None

    print()
    print("=" * 60)
    print(f"  Input leads     : {total_in}")
    print(f"  Small / dialable: {len(all_keep)}")
    print(f"  Removed         : {len(all_removed)}")
    print(f"  State files     : {SMALL_DIR}")
    print(f"  Dial list CSV   : {combined}")
    if xlsx:
        print(f"  Dial list Excel : {xlsx}")
    print(f"  Removed list    : {removed_combined}")
    print("=" * 60)


def main() -> None:
    import sys

    require_phone = "--keep-no-phone" not in sys.argv
    print("=" * 60)
    print("  REMOVE INC / CORP — KEEP SMALL BUSINESSES")
    print("=" * 60)
    print()
    run(require_phone=require_phone)


if __name__ == "__main__":
    main()
