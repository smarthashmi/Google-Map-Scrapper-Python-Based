# USA Google Maps Scraper - Auto Repair Leads

A fast **command-line** Python scraper for Google Maps business data (USA only). No web server, no Flask — runs directly on your PC.

## Features

- **Auto repair niche** with 30+ predefined keywords (brake repair, oil change, body shop, mobile mechanic, etc.)
- **USA-only** searches across cities and states
- **Resume support** — if your PC shuts down, run `start.bat` again and continue where you left off
- **Data organized by date** — `data/2026-07-09/all_results.csv`
- **Interactive menu** — pick keyword packs, locations, and settings
- **History viewer** — see how much data was scraped, which cities/states, and dates

## Quick Start

1. **Run setup once** (installs Python packages + Chromium browser):
   ```
   Double-click setup.bat
   ```

2. **Start scraping**:
   ```
   Double-click start.bat
   ```

3. **Check history**:
   ```
   Double-click history.bat
   ```

## Data Output

Each day creates a folder:

```
data/
  2026-07-09/
    all_results.csv          <- all businesses for the day
    auto_repair_shop_Chicago_IL.csv
    brake_repair_shop_Houston_TX.csv
    ...
```

### CSV Columns

| Column | Description |
|--------|-------------|
| scraped_at | Timestamp |
| search_keyword | Keyword used |
| search_place | City or county searched |
| search_type | `city` or `county` |
| search_state | State abbreviation |
| name | Business name |
| address | Full address |
| phone | Phone number |
| website | Website URL |
| rating | Google rating |
| review_count | Number of reviews |
| category | Business category |
| hours | Opening hours |
| google_maps_url | Direct Maps link |
| place_id | Unique place identifier |

## Resume / Checkpoint

Progress is saved in `state/checkpoint.json` after every search. If interrupted:

1. Run `start.bat`
2. Choose **Yes** when asked to resume

## Keyword Packs

| Pack | Description |
|------|-------------|
| 1 | Full Auto Repair (30 keywords) |
| 2 | Core Repair Shops (10) |
| 3 | Body & Collision (5) |
| 4 | Maintenance & Quick Service (8) |
| 5 | Specialty & Mobile (6) |
| C | Custom keywords |
| M | Mix multiple packs |

## Location Coverage

| Option | Coverage |
|--------|----------|
| 1 | Top 50 US cities |
| 2 | Top 100 US cities |
| 3 | ~150 major cities |
| 4 | Full USA — all counties + cities (~3,500) |
| S | Single state — all counties + cities in that state |
| C | Single custom city |

Default is option **4** for maximum USA coverage.

## Requirements

- Windows 10/11
- Python 3.10+
- Internet connection

## Notes

- Google Maps layout changes occasionally; selectors may need updates over time.
- Use reasonable `max results per search` to avoid rate limiting.
- Run `headless = No` if you want to see the browser (useful for debugging).
- Scraping is for personal/research use; respect Google's terms of service.

## Command Line

```bash
python -m scraper.main          # Interactive menu
python -m scraper.main history    # View stats
python -m scraper.main files      # List data folders
```
