"""Merge all scraped date folders into one upload-ready file."""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from scraper.formatter import normalize_row
from scraper.organize import ORGANIZED_CSV, collect_all_rows, _dedupe_rows, _write_xlsx
from scraper.storage import CSV_COLUMNS, DATA_DIR, list_data_dates

OUTPUT_CSV = "ALL_LEADS_COMBINED.csv"
OUTPUT_XLSX = "ALL_LEADS_COMBINED.xlsx"


def merge_all() -> tuple[int, Path, Path]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str]] = []

    dates = list_data_dates()
    print(f"Found {len(dates)} date folders")
    for d in sorted(dates):
        folder = DATA_DIR / d
        day_rows = collect_all_rows(folder)
        print(f"  {d}: {len(day_rows)} raw rows")
        rows.extend(day_rows)

    cleaned = _dedupe_rows([normalize_row(r) for r in rows])
    cleaned.sort(key=lambda r: (r.get("state", ""), r.get("city", ""), r.get("name", "")))

    # Also write per-state count summary
    by_state: dict[str, int] = defaultdict(int)
    for row in cleaned:
        st = row.get("state") or row.get("search_state") or "UNKNOWN"
        by_state[st] += 1

    csv_path = DATA_DIR / OUTPUT_CSV
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(cleaned)

    xlsx_path = DATA_DIR / OUTPUT_XLSX
    try:
        _write_xlsx(cleaned, xlsx_path)
    except Exception as exc:
        print(f"Excel write skipped: {exc}")
        xlsx_path = Path("")

    print()
    print("States included:")
    for st in sorted(by_state):
        print(f"  {st}: {by_state[st]}")
    print()
    print(f"TOTAL unique leads: {len(cleaned)}")
    print(f"Generated: {datetime.now().isoformat(timespec='seconds')}")
    return len(cleaned), csv_path, xlsx_path


def main() -> None:
    print("=" * 60)
    print("  MERGING ALL SCRAPED DATA INTO ONE FILE")
    print("  Close Excel / CSV files first if open")
    print("=" * 60)
    print()
    count, csv_path, xlsx_path = merge_all()
    print()
    print("=" * 60)
    print(f"  DONE — {count} unique leads")
    print(f"  CSV  : {csv_path}")
    if xlsx_path:
        print(f"  Excel: {xlsx_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
