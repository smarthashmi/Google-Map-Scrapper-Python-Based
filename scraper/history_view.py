"""Scraping history and statistics viewer."""

from __future__ import annotations

from pathlib import Path

from scraper.checkpoint import CHECKPOINT_FILE, load_checkpoint
from scraper.storage import DATA_DIR, list_data_dates, summarize_date


def print_history() -> None:
    print()
    print("=" * 60)
    print("  GOOGLE MAPS SCRAPER - HISTORY & STATS")
    print("=" * 60)

    cp = load_checkpoint()
    if cp:
        print()
        print("  LAST SESSION")
        print("  " + "-" * 40)
        print(f"  Status       : {cp.status}")
        print(f"  Started      : {cp.started_at or 'N/A'}")
        print(f"  Last updated : {cp.last_updated or 'N/A'}")
        print(f"  Total scraped: {cp.total_scraped}")
        print(f"  Progress     : keyword {cp.keyword_index + 1}/{len(cp.keywords)}, "
              f"location {cp.location_index + 1}/{len(cp.locations)}")
        print(f"  Searches done: {len(cp.completed_searches)}")
        if cp.keywords:
            print(f"  Keywords     : {', '.join(cp.keywords[:3])}"
                  f"{'...' if len(cp.keywords) > 3 else ''}")
    else:
        print()
        print("  No active checkpoint found.")

    dates = list_data_dates()
    print()
    print("  SCRAPED DATA BY DATE")
    print("  " + "-" * 40)

    if not dates:
        print("  No data saved yet. Run start.bat to begin scraping.")
        print()
        return

    grand_total = 0
    for date_str in dates:
        summary = summarize_date(date_str)
        grand_total += summary["total"]
        print()
        print(f"  Date    : {summary['date']}")
        print(f"  Records : {summary['total']}")
        print(f"  Files   : {summary['file_count']} CSV files")
        if summary["states"]:
            states_preview = ", ".join(summary["states"][:8])
            if len(summary["states"]) > 8:
                states_preview += f" (+{len(summary['states']) - 8} more)"
            print(f"  States  : {states_preview}")
        if summary.get("counties") or summary.get("cities"):
            print(f"  Searches: {summary.get('counties', 0)} county + {summary.get('cities', 0)} city lookups")
        if summary.get("places"):
            places_preview = ", ".join(summary["places"][:6])
            if len(summary["places"]) > 6:
                places_preview += f" (+{len(summary['places']) - 6} more)"
            print(f"  Places  : {places_preview}")
        if summary["keywords"]:
            kw_preview = ", ".join(summary["keywords"][:4])
            if len(summary["keywords"]) > 4:
                kw_preview += f" (+{len(summary['keywords']) - 4} more)"
            print(f"  Keywords: {kw_preview}")

    print()
    print("  " + "-" * 40)
    print(f"  GRAND TOTAL: {grand_total} records across {len(dates)} day(s)")
    print(f"  Data folder: {DATA_DIR}")
    print()


def print_data_locations() -> None:
    dates = list_data_dates()
    if not dates:
        print("No data folders found.")
        return
    print("\nData folders:")
    for d in dates:
        folder = DATA_DIR / d
        csv_files = list(folder.glob("*.csv"))
        print(f"  {d}/  ({len(csv_files)} files)")
        for f in sorted(csv_files)[:5]:
            print(f"    - {f.name}")
        if len(csv_files) > 5:
            print(f"    ... and {len(csv_files) - 5} more")
