"""Backfill emails for existing scraped leads that have a website."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

from scraper.email_finder import find_email_from_website
from scraper.formatter import normalize_row
from scraper.storage import CSV_COLUMNS, DATA_DIR, list_data_dates


def backfill_file(csv_path: Path, limit: int = 0) -> tuple[int, int]:
    if not csv_path.exists():
        return 0, 0

    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    updated = 0
    checked = 0
    for row in rows:
        if limit and checked >= limit:
            break
        if (row.get("email") or "").strip():
            continue
        website = (row.get("website") or "").strip()
        if not website:
            continue

        checked += 1
        name = (row.get("name") or "")[:40]
        print(f"  [{checked}] {name} -> {website[:50]}")
        email = find_email_from_website(website)
        if email:
            row["email"] = email
            updated += 1
            print(f"      FOUND: {email}")
        else:
            print("      (no email found)")

    cleaned = [normalize_row(r) for r in rows]
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(cleaned)

    return checked, updated


def main() -> None:
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    dates = [date_arg] if date_arg else list_data_dates()
    if not dates:
        print("No data folders found.")
        return

    print("Backfilling emails from business websites...")
    print("Close Excel/CSV files first.\n")

    for d in dates[:3]:  # latest few days
        folder = DATA_DIR / d
        target = folder / "leads_organized.csv"
        if not target.exists():
            target = folder / "all_results.csv"
        if not target.exists():
            continue
        print(f"\n=== {d}: {target.name} ===")
        checked, updated = backfill_file(target)
        print(f"Checked {checked} websites, found {updated} emails")
        print(f"Saved -> {target}")


if __name__ == "__main__":
    main()
