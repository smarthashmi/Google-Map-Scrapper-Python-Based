"""CLI entry point with interactive menu, resume, and scraping controls."""

from __future__ import annotations

import sys
import uuid
from datetime import datetime

from scraper.checkpoint import (
    Checkpoint,
    clear_checkpoint,
    has_resumable_session,
    load_checkpoint,
    save_checkpoint,
)
from scraper.history_view import print_data_locations, print_history
from scraper.keywords import KEYWORD_PRESETS, get_preset_menu_text
from scraper.locations import (
    LOCATION_PRESETS,
    USA_STATES,
    build_all_states_locations,
    build_state_locations,
    get_location_stats,
    location_label,
    normalize_location,
)
from scraper.maps_scraper import GoogleMapsScraper


BANNER = r"""
  ============================================================
       USA GOOGLE MAPS SCRAPER - Auto Repair & More
  ============================================================
    * USA businesses only
    * Auto repair + related keywords
    * Resume after shutdown (checkpoint saved)
    * Data saved by date in /data folder
  ============================================================
"""


def _input(prompt: str, default: str = "") -> str:
    try:
        value = input(prompt).strip()
        return value if value else default
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)


def _pick_keywords() -> list[str]:
    print(get_preset_menu_text())
    choice = _input("\n  Select keyword pack [1]: ", "1").upper()

    if choice == "C":
        raw = _input("  Enter keywords (comma-separated): ")
        return [k.strip() for k in raw.split(",") if k.strip()]

    if choice == "M":
        picks = _input("  Enter pack numbers to combine (e.g. 1,3,4): ")
        keywords: list[str] = []
        for p in picks.split(","):
            p = p.strip()
            if p in KEYWORD_PRESETS:
                keywords.extend(KEYWORD_PRESETS[p]["keywords"])
        # dedupe preserving order
        seen: set[str] = set()
        unique = []
        for k in keywords:
            if k not in seen:
                seen.add(k)
                unique.append(k)
        return unique or KEYWORD_PRESETS["1"]["keywords"]

    if choice not in KEYWORD_PRESETS:
        choice = "1"
    preset = KEYWORD_PRESETS[choice]
    print(f"\n  Selected: {preset['name']}")
    print(f"  Keywords ({len(preset['keywords'])}):")
    for i, kw in enumerate(preset["keywords"][:8], 1):
        print(f"    {i}. {kw}")
    if len(preset["keywords"]) > 8:
        print(f"    ... +{len(preset['keywords']) - 8} more")
    return list(preset["keywords"])


def _pick_locations() -> list[list[str]]:
    print()
    print("  LOCATION COVERAGE (USA)")
    print("  " + "-" * 40)
    print("  [1] ALL 50 STATES - every county + city (RECOMMENDED)")
    print("      -> No typing needed. Scrapes all states automatically.")
    for key, preset in LOCATION_PRESETS.items():
        if key == "1":
            continue
        print(f"  [{key}] {preset['name']}")
    print("  [S] One state only (if you want a single state)")
    print("  [C] One custom city only")

    choice = _input("\n  Press ENTER for all 50 states [1]: ", "1").upper()

    if choice in ("", "1", "ALL", "USA"):
        locations = build_all_states_locations()
        stats = get_location_stats(locations)
        print(f"\n  Selected: ALL 50 STATES (automatic)")
        print(f"  Coverage: {stats['states']} states, {stats['counties']} counties, "
              f"{stats['cities']} cities ({stats['total']} searches per keyword)")
        print(f"  States   : {', '.join(USA_STATES[:10])} ... +{max(0, stats['states'] - 10)} more")
        return locations

    if choice == "C":
        city = _input("  City name: ")
        state = _input("  State (2-letter, e.g. TX): ").upper()
        return [[city, state, "city"]]

    if choice == "S":
        print()
        print("  Examples: Texas, TX, California, CA")
        state_in = _input("  State name or abbreviation: ")
        locations = build_state_locations(state_in)
        if not locations:
            print("  State not found. Using Texas as fallback.")
            locations = build_state_locations("TX")
        stats = get_location_stats(locations)
        print(f"\n  Selected: {state_in} -> {stats['counties']} counties + {stats['cities']} cities")
        return locations

    if choice not in LOCATION_PRESETS:
        choice = "1"
        locations = build_all_states_locations()
    else:
        preset = LOCATION_PRESETS[choice]
        locations = preset["builder"]()
    stats = get_location_stats(locations)
    preset_name = LOCATION_PRESETS.get(choice, LOCATION_PRESETS["1"])["name"]
    print(f"\n  Selected: {preset_name}")
    print(f"  Coverage: {stats['counties']} counties, {stats['cities']} cities, "
          f"{stats['states']} states ({stats['total']} searches per keyword)")
    return locations


def _pick_settings() -> bool:
    print()
    print("  SCRAPER SETTINGS")
    print("  " + "-" * 40)
    headless_in = _input("  Run headless (hidden browser)? [Y/n]: ", "Y").lower()
    return headless_in != "n"


def _confirm_start(keywords: list[str], locations: list[list[str]], resume: bool) -> bool:
    print()
    print("  READY TO START")
    print("  " + "-" * 40)
    mode = "RESUME previous session" if resume else "NEW session"
    print(f"  Mode      : {mode}")
    print(f"  Keywords  : {len(keywords)}")
    print(f"  Locations : {len(locations)}")
    print(f"  Est. searches: {len(keywords) * len(locations)}")
    print()
    if locations:
        loc = normalize_location(locations[0])
        sample = location_label(loc[0], loc[1], loc[2])
        print(f"  First search: '{keywords[0]}' in {sample}")
    ans = _input("  Start scraping? [Y/n]: ", "Y").lower()
    return ans != "n"


def _start_scraper(checkpoint: Checkpoint) -> None:
    headless = checkpoint.headless
    max_results = checkpoint.max_results_per_search or 80
    scraper = GoogleMapsScraper(
        checkpoint=checkpoint,
        headless=headless,
        max_results_per_search=max_results,
    )
    scraper.run()

    if checkpoint.status == "completed":
        ans = _input("\n  Session complete. Clear checkpoint for fresh start? [y/N]: ", "N").lower()
        if ans == "y":
            clear_checkpoint()
            print("  Checkpoint cleared.")


def run_all_states(auto: bool = False) -> None:
    """Start scraping all 50 states automatically — no location prompts."""
    print(BANNER)
    print("  >>> ALL 50 STATES MODE <<<")
    print("  Scrapes every county + city in all US states automatically.")
    print()

    if has_resumable_session():
        cp = load_checkpoint()
        print("  Resumable session found.")
        if auto:
            resume = True
            checkpoint = cp
        else:
            ans = _input("  Resume where you left off? [Y/n]: ", "Y").lower()
            resume = ans != "n"
            checkpoint = cp if resume else None
    else:
        resume = False
        checkpoint = None

    if not resume:
        if auto:
            keywords = list(KEYWORD_PRESETS["1"]["keywords"])
            headless = True
        else:
            keywords = _pick_keywords()
            headless = _pick_settings()

        locations = build_all_states_locations()
        stats = get_location_stats(locations)

        print()
        print("  ALL 50 STATES SELECTED (automatic)")
        print(f"  Keywords : {len(keywords)}")
        print(f"  Locations: {stats['total']} ({stats['states']} states, "
              f"{stats['counties']} counties, {stats['cities']} cities)")
        print(f"  Searches : {len(keywords) * stats['total']}")

        if not auto and not _confirm_start(keywords, locations, resume=False):
            print("  Cancelled.")
            return

        checkpoint = Checkpoint(
            session_id=str(uuid.uuid4())[:8],
            started_at=datetime.now().isoformat(timespec="seconds"),
            keywords=keywords,
            locations=locations,
            headless=headless,
            max_results_per_search=80,
            status="running",
        )
        save_checkpoint(checkpoint)
    else:
        assert checkpoint is not None
        print(f"\n  Resuming session {checkpoint.session_id}...")
        print(f"  Keywords: {len(checkpoint.keywords)}, Locations: {len(checkpoint.locations)}")

    _start_scraper(checkpoint)


def run_interactive() -> None:
    print(BANNER)

    resume = False
    checkpoint: Checkpoint | None = None

    if has_resumable_session():
        cp = load_checkpoint()
        print("  >>> RESUMABLE SESSION DETECTED <<<")
        print(f"  Last run  : {cp.last_updated if cp else 'N/A'}")
        print(f"  Progress  : {cp.total_scraped if cp else 0} businesses scraped so far")
        ans = _input("  Resume where you left off? [Y/n]: ", "Y").lower()
        if ans != "n" and cp:
            resume = True
            checkpoint = cp

    if not resume:
        print()
        print("  TIP: Use predefined packs for auto repair leads.")
        print("  TIP: Data saves to data/YYYY-MM-DD/ automatically.")
        keywords = _pick_keywords()
        locations = _pick_locations()
        headless = _pick_settings()

        if not _confirm_start(keywords, locations, resume=False):
            print("  Cancelled.")
            return

        checkpoint = Checkpoint(
            session_id=str(uuid.uuid4())[:8],
            started_at=datetime.now().isoformat(timespec="seconds"),
            keywords=keywords,
            locations=locations,
            headless=headless,
            max_results_per_search=80,
            status="running",
        )
        save_checkpoint(checkpoint)
    else:
        assert checkpoint is not None
        print(f"\n  Resuming session {checkpoint.session_id}...")
        print(f"  Keywords: {len(checkpoint.keywords)}, Locations: {len(checkpoint.locations)}")

    _start_scraper(checkpoint)


def main() -> None:
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd in ("history", "stats", "--history"):
            print_history()
            return
        if cmd in ("files", "--files"):
            print_data_locations()
            return
        if cmd in ("all-states", "allstates", "usa", "--all-states"):
            auto = "--auto" in [a.lower() for a in sys.argv[2:]]
            run_all_states(auto=auto)
            return
        if cmd in ("help", "--help", "-h"):
            print(__doc__)
            print("Usage:")
            print("  python -m scraper.main              Interactive menu")
            print("  python -m scraper.main all-states   All 50 states (no location prompt)")
            print("  python -m scraper.main all-states --auto   Fully automatic")
            print("  python -m scraper.main history       View stats")
            return

    run_interactive()


if __name__ == "__main__":
    main()
