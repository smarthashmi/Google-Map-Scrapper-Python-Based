"""Data storage organized by state (one CSV per state)."""

from __future__ import annotations

import csv
import json
import re
import time
from datetime import date, datetime
from pathlib import Path
from typing import Any

from scraper.formatter import normalize_row

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
BY_STATE_DIR = DATA_DIR / "by_state"

FALLBACK_MASTER = "all_results_live.csv"
PENDING_FILE = "pending_rows.jsonl"
WRITE_RETRIES = 3
RETRY_DELAY_SEC = 0.4

_file_lock_warned = False

CSV_COLUMNS = [
    "name",
    "phone",
    "website",
    "email",
    "address",
    "street",
    "city",
    "state",
    "zip",
    "rating",
    "review_count",
    "category",
    "hours_status",
    "hours_detail",
    "google_maps_url",
    "search_keyword",
    "search_place",
    "search_type",
    "search_state",
    "scraped_at",
    "place_id",
]

US_STATE_ABBRS = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID",
    "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS",
    "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK",
    "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV",
    "WI", "WY", "DC",
}


def today_folder() -> Path:
    folder = DATA_DIR / date.today().isoformat()
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def by_state_dir() -> Path:
    BY_STATE_DIR.mkdir(parents=True, exist_ok=True)
    return BY_STATE_DIR


def resolve_state_code(row: dict[str, Any]) -> str:
    """Pick best 2-letter state code for file naming."""
    for key in ("search_state", "state"):
        val = (row.get(key) or "").strip().upper()
        if val in US_STATE_ABBRS:
            return val

    addr = (row.get("address") or "").upper()
    match = re.search(r",\s*([A-Z]{2})\s+\d{5}", addr)
    if match and match.group(1) in US_STATE_ABBRS:
        return match.group(1)

    return "UNKNOWN"


def state_csv_path(state_code: str) -> Path:
    code = (state_code or "UNKNOWN").upper()
    if code not in US_STATE_ABBRS:
        code = "UNKNOWN"
    return by_state_dir() / f"{code}.csv"


def _safe_slug(text: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in text).strip("_")[:60]


def session_csv_path(keyword: str, place: str, state: str, loc_type: str = "city") -> Path:
    folder = today_folder()
    slug = _safe_slug(f"{keyword}_{loc_type}_{place}_{state}")
    return folder / f"{slug}.csv"


def master_csv_path() -> Path:
    return today_folder() / "all_results.csv"


def fallback_master_csv_path() -> Path:
    return today_folder() / FALLBACK_MASTER


def pending_rows_path() -> Path:
    return today_folder() / PENDING_FILE


def _warn_file_locked(path: Path) -> None:
    global _file_lock_warned
    if _file_lock_warned:
        return
    _file_lock_warned = True
    print()
    print("  [WARNING] Cannot write to locked file:")
    print(f"            {path}")
    print("  Close Excel / CSV viewers and keep scraping.")
    print("  Data is still saved to data/by_state/<STATE>.csv when possible.")
    print()


def _append_row(path: Path, row: dict[str, Any]) -> bool:
    clean = normalize_row(row)
    exists = path.exists()

    for attempt in range(WRITE_RETRIES):
        try:
            with path.open("a", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
                if not exists:
                    writer.writeheader()
                writer.writerow({col: clean.get(col, "") for col in CSV_COLUMNS})
            return True
        except PermissionError:
            if attempt < WRITE_RETRIES - 1:
                time.sleep(RETRY_DELAY_SEC)
            continue
        except OSError:
            if attempt < WRITE_RETRIES - 1:
                time.sleep(RETRY_DELAY_SEC)
            continue
    return False


def _append_pending(row: dict[str, Any]) -> None:
    path = pending_rows_path()
    clean = normalize_row(row)
    try:
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(clean, ensure_ascii=False) + "\n")
    except (PermissionError, OSError):
        pass


def _write_row(path: Path, row: dict[str, Any]) -> bool:
    return _append_row(path, row)


def save_business(row: dict[str, Any]) -> None:
    """Save one business into the state master CSV (primary) + daily files."""
    row = dict(row)
    row.setdefault("scraped_at", datetime.now().isoformat(timespec="seconds"))

    state_code = resolve_state_code(row)
    # Ensure search_state is filled for consistent columns
    if not (row.get("search_state") or "").strip():
        row["search_state"] = state_code

    # PRIMARY: one file per state  ->  data/by_state/CA.csv
    state_path = state_csv_path(state_code)
    if not _write_row(state_path, row):
        _warn_file_locked(state_path)
        _append_pending(row)

    # Daily master (optional backup)
    master = master_csv_path()
    if not _write_row(master, row):
        _warn_file_locked(master)
        _write_row(fallback_master_csv_path(), row)


def save_json_backup(
    rows: list[dict[str, Any]], keyword: str, place: str, state: str, loc_type: str = "city"
) -> Path:
    folder = today_folder()
    slug = _safe_slug(f"{keyword}_{loc_type}_{place}_{state}")
    path = folder / f"{slug}.json"
    cleaned = [normalize_row(r) for r in rows]
    try:
        path.write_text(json.dumps(cleaned, indent=2, ensure_ascii=False), encoding="utf-8")
    except (PermissionError, OSError):
        pass
    return path


def refresh_organized_exports() -> None:
    """Optional daily organized export — skipped during scrape for speed."""
    return


def list_data_dates() -> list[str]:
    if not DATA_DIR.exists():
        return []
    dates = sorted(
        [p.name for p in DATA_DIR.iterdir() if p.is_dir() and p.name[:4].isdigit()],
        reverse=True,
    )
    return dates


def count_records_for_date(date_str: str) -> int:
    folder = DATA_DIR / date_str
    organized = folder / "leads_organized.csv"
    master = folder / "all_results.csv"
    target = organized if organized.exists() else master
    if target.exists():
        with target.open(encoding="utf-8-sig") as f:
            return max(0, sum(1 for _ in f) - 1)
    total = 0
    for csv_file in folder.glob("*.csv"):
        if csv_file.name in ("all_results.csv", "leads_organized.csv"):
            continue
        with csv_file.open(encoding="utf-8-sig") as f:
            total += max(0, sum(1 for _ in f) - 1)
    return total


def summarize_date(date_str: str) -> dict[str, Any]:
    folder = DATA_DIR / date_str
    if not folder.exists():
        return {"date": date_str, "total": 0, "places": [], "states": [], "keywords": [], "counties": 0, "cities": 0}

    places: set[str] = set()
    states: set[str] = set()
    keywords: set[str] = set()
    counties = 0
    cities = 0
    total = 0

    organized = folder / "leads_organized.csv"
    master = folder / "all_results.csv"
    files = [organized] if organized.exists() else ([master] if master.exists() else list(folder.glob("*.csv")))

    for csv_file in files:
        if not csv_file.exists():
            continue
        with csv_file.open(encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                total += 1
                place = row.get("search_place") or row.get("search_city", "")
                loc_type = row.get("search_type", "city")
                if place:
                    places.add(place)
                if loc_type == "county":
                    counties += 1
                else:
                    cities += 1
                st = row.get("search_state") or row.get("state", "")
                if st:
                    states.add(st)
                if row.get("search_keyword"):
                    keywords.add(row["search_keyword"])

    return {
        "date": date_str,
        "total": total,
        "places": sorted(places),
        "states": sorted(states),
        "keywords": sorted(keywords),
        "counties": counties,
        "cities": cities,
        "file_count": len(list(folder.glob("*.csv"))),
    }
