"""Build one master CSV per state from all date folders."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

from scraper.formatter import normalize_row
from scraper.organize import collect_all_rows, _dedupe_rows, _write_xlsx
from scraper.storage import (
    BY_STATE_DIR,
    CSV_COLUMNS,
    DATA_DIR,
    by_state_dir,
    list_data_dates,
    resolve_state_code,
)


def build_state_masters() -> dict[str, int]:
    by_state_dir()
    buckets: dict[str, list[dict[str, str]]] = defaultdict(list)

    dates = list_data_dates()
    print(f"Scanning {len(dates)} date folders...")

    for d in sorted(dates):
        folder = DATA_DIR / d
        rows = collect_all_rows(folder)
        print(f"  {d}: {len(rows)} rows")
        for row in rows:
            clean = normalize_row(row)
            code = resolve_state_code(clean)
            if not clean.get("search_state"):
                clean["search_state"] = code
            if not clean.get("state"):
                clean["state"] = code if code != "UNKNOWN" else ""
            buckets[code].append(clean)

    # Also include any existing by_state files so we don't drop live scraper output
    if BY_STATE_DIR.exists():
        for csv_file in sorted(BY_STATE_DIR.glob("*.csv")):
            try:
                with csv_file.open(encoding="utf-8-sig", newline="") as f:
                    for row in csv.DictReader(f):
                        clean = normalize_row(row)
                        code = resolve_state_code(clean) or csv_file.stem.upper()
                        buckets[code].append(clean)
            except (PermissionError, OSError):
                print(f"  [SKIP] locked: {csv_file.name}")

    counts: dict[str, int] = {}
    print()
    print("Writing state master files -> data/by_state/")
    for code in sorted(buckets):
        cleaned = _dedupe_rows(buckets[code])
        cleaned.sort(key=lambda r: (r.get("city", ""), r.get("name", "")))
        out = BY_STATE_DIR / f"{code}.csv"
        try:
            with out.open("w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
                writer.writeheader()
                writer.writerows(cleaned)
            counts[code] = len(cleaned)
            print(f"  {code}.csv  ->  {len(cleaned)} leads")
        except (PermissionError, OSError) as exc:
            print(f"  [SKIP] {code}.csv locked: {exc}")

    # Combined upload file
    all_rows: list[dict[str, str]] = []
    for code in sorted(counts):
        path = BY_STATE_DIR / f"{code}.csv"
        if not path.exists():
            continue
        with path.open(encoding="utf-8-sig", newline="") as f:
            all_rows.extend(list(csv.DictReader(f)))

    all_rows = _dedupe_rows([normalize_row(r) for r in all_rows])
    all_rows.sort(key=lambda r: (r.get("state", ""), r.get("city", ""), r.get("name", "")))

    combined_csv = DATA_DIR / "ALL_STATES_COMBINED.csv"
    with combined_csv.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_rows)

    combined_xlsx = DATA_DIR / "ALL_STATES_COMBINED.xlsx"
    try:
        _write_xlsx(all_rows, combined_xlsx)
        print(f"\nAlso created: {combined_xlsx.name}")
    except Exception as exc:
        print(f"\nExcel skipped: {exc}")

    print(f"Also created: {combined_csv.name} ({len(all_rows)} unique leads)")
    return counts


def main() -> None:
    print("=" * 60)
    print("  BUILD STATE MASTER CSV FILES")
    print("  Example: data/by_state/CA.csv , TX.csv , ...")
    print("  Close Excel files first!")
    print("=" * 60)
    print()
    counts = build_state_masters()
    print()
    print("=" * 60)
    print(f"  States written: {len(counts)}")
    print(f"  Total leads   : {sum(counts.values())}")
    print(f"  Folder        : {BY_STATE_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
