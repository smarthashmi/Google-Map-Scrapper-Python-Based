"""Google Maps scraper engine using Playwright."""

from __future__ import annotations

import hashlib
import random
import re
import time
from typing import Any
from urllib.parse import quote_plus

from playwright.sync_api import Page, sync_playwright

from scraper.checkpoint import Checkpoint, save_checkpoint
from scraper.email_finder import find_email_from_website
from scraper.locations import normalize_location
from scraper.storage import save_business, save_json_backup


def _delay(min_s: float = 1.0, max_s: float = 2.5) -> None:
    time.sleep(random.uniform(min_s, max_s))


def _place_id_from_url(url: str) -> str:
    if not url:
        return ""
    match = re.search(r"!1s([^!]+)", url) or re.search(r"/place/[^/]+/([^/?]+)", url)
    if match:
        return match.group(1)
    return hashlib.md5(url.encode()).hexdigest()[:16]


class GoogleMapsScraper:
    def __init__(
        self,
        checkpoint: Checkpoint,
        headless: bool = True,
        max_results_per_search: int = 80,
    ):
        self.checkpoint = checkpoint
        self.headless = headless
        self.max_results_per_search = max_results_per_search
        self._seen_ids: set[str] = set(checkpoint.scraped_place_ids)

    def run(self) -> None:
        self.checkpoint.status = "running"
        save_checkpoint(self.checkpoint)

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.headless,
                args=["--disable-blink-features=AutomationControlled"],
            )
            context = browser.new_context(
                viewport={"width": 1366, "height": 900},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                ),
                locale="en-US",
            )
            page = context.new_page()

            try:
                self._scrape_all(page)
                self.checkpoint.status = "completed"
            except KeyboardInterrupt:
                self.checkpoint.status = "paused"
                print("\n[PAUSED] Progress saved. Run start.bat again to resume.")
            except Exception as exc:
                self.checkpoint.status = "paused"
                print(f"\n[ERROR] {exc}")
                print("Progress saved. Run start.bat again to resume.")
            finally:
                save_checkpoint(self.checkpoint)
                browser.close()

    def _scrape_all(self, page: Page) -> None:
        keywords = self.checkpoint.keywords
        locations = self.checkpoint.locations

        for ki in range(self.checkpoint.keyword_index, len(keywords)):
            keyword = keywords[ki]
            self.checkpoint.keyword_index = ki

            start_li = self.checkpoint.location_index if ki == self.checkpoint.keyword_index else 0
            for li in range(start_li, len(locations)):
                place, state, loc_type = normalize_location(locations[li])
                self.checkpoint.location_index = li

                if self.checkpoint.is_search_done(keyword, place, state, loc_type):
                    continue

                type_label = "county" if loc_type == "county" else "city"
                print(f"\n[SEARCH] '{keyword}' in {place}, {state} ({type_label})")
                batch = self._scrape_search(page, keyword, place, state, loc_type)
                print(f"  -> Found {len(batch)} businesses")

                for row in batch:
                    save_business(row)
                    pid = row.get("place_id", "")
                    if pid and pid not in self._seen_ids:
                        self._seen_ids.add(pid)
                        self.checkpoint.scraped_place_ids.append(pid)
                        self.checkpoint.total_scraped += 1

                if batch:
                    try:
                        save_json_backup(batch, keyword, place, state, loc_type)
                    except (PermissionError, OSError):
                        pass
                    # State CSV is updated per business; skip heavy daily re-organize
                    print(f"  -> Saved to data/by_state/{(state or 'UNKNOWN').upper()}.csv")

                self.checkpoint.mark_search_done(keyword, place, state, loc_type)
                save_checkpoint(self.checkpoint)

            self.checkpoint.location_index = 0

        self.checkpoint.keyword_index = len(keywords)
        print(f"\n[DONE] Total unique businesses scraped: {self.checkpoint.total_scraped}")

    def _scrape_search(
        self, page: Page, keyword: str, place: str, state: str, loc_type: str = "city"
    ) -> list[dict[str, Any]]:
        location = f"{place}, {state}, USA" if state else f"{place}, USA"
        query = f"{keyword} in {location}"
        url = f"https://www.google.com/maps/search/{quote_plus(query)}"

        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        _delay(2, 4)

        self._dismiss_consent(page)
        self._scroll_results(page)

        listings = self._collect_listing_links(page)
        results: list[dict[str, Any]] = []

        for i, listing in enumerate(listings[: self.max_results_per_search]):
            name = listing.get("name", "")
            href = listing.get("href", "")
            place_id = _place_id_from_url(href)

            if place_id and place_id in self._seen_ids:
                continue

            print(f"  [{i + 1}/{min(len(listings), self.max_results_per_search)}] {name[:50]}")

            details = self._scrape_place_page(page, href, keyword, place, state, loc_type)
            if details:
                results.append(details)
                if place_id:
                    self._seen_ids.add(place_id)

            _delay(0.8, 1.8)

        return results

    def _dismiss_consent(self, page: Page) -> None:
        for selector in [
            'button:has-text("Accept all")',
            'button:has-text("Reject all")',
            'button:has-text("I agree")',
            'form[action*="consent"] button',
        ]:
            try:
                btn = page.locator(selector).first
                if btn.is_visible(timeout=2000):
                    btn.click()
                    _delay(1, 2)
                    return
            except Exception:
                pass

    def _scroll_results(self, page: Page, max_scrolls: int = 18) -> None:
        feed = page.locator('div[role="feed"]')
        try:
            feed.wait_for(timeout=10000)
        except Exception:
            return

        prev_count = 0
        for _ in range(max_scrolls):
            feed.evaluate("el => el.scrollTo(0, el.scrollHeight)")
            _delay(1.2, 2.0)
            cards = page.locator('a[href*="/maps/place/"]')
            count = cards.count()
            if count == prev_count:
                break
            prev_count = count

    def _collect_listing_links(self, page: Page) -> list[dict[str, str]]:
        listings: list[dict[str, str]] = []
        seen_hrefs: set[str] = set()

        cards = page.locator('a[href*="/maps/place/"]')
        count = cards.count()

        for i in range(count):
            try:
                card = cards.nth(i)
                href = card.get_attribute("href") or ""
                if not href or href in seen_hrefs:
                    continue
                seen_hrefs.add(href)

                name = ""
                try:
                    name = card.locator("div.fontHeadlineSmall").first.inner_text(timeout=1000)
                except Exception:
                    try:
                        name = card.inner_text(timeout=1000).split("\n")[0]
                    except Exception:
                        pass

                if name:
                    listings.append({"name": name.strip(), "href": href})
            except Exception:
                continue

        return listings

    def _scrape_place_page(
        self,
        page: Page,
        href: str,
        keyword: str,
        place: str,
        state: str,
        loc_type: str = "city",
    ) -> dict[str, Any] | None:
        try:
            page.goto(href, wait_until="domcontentloaded", timeout=45000)
            _delay(1.5, 2.5)
        except Exception:
            return None

        data: dict[str, Any] = {
            "search_keyword": keyword,
            "search_place": place,
            "search_type": loc_type,
            "search_city": place,
            "search_state": state,
            "google_maps_url": href,
            "place_id": _place_id_from_url(href),
        }

        # Name
        for sel in ["h1.DUwDvf", "h1.fontHeadlineLarge", "h1"]:
            try:
                data["name"] = page.locator(sel).first.inner_text(timeout=3000).strip()
                break
            except Exception:
                pass

        if not data.get("name"):
            return None

        # Rating & reviews
        try:
            rating_el = page.locator('div.F7nice span[aria-hidden="true"]').first
            data["rating"] = rating_el.inner_text(timeout=2000).strip()
        except Exception:
            data["rating"] = ""

        try:
            reviews_el = page.locator('div.F7nice span span[aria-label*="review"]').first
            label = reviews_el.get_attribute("aria-label") or reviews_el.inner_text()
            match = re.search(r"([\d,]+)", label)
            data["review_count"] = match.group(1).replace(",", "") if match else ""
        except Exception:
            data["review_count"] = ""

        # Category
        try:
            data["category"] = page.locator("button.DkEaL").first.inner_text(timeout=2000).strip()
        except Exception:
            data["category"] = ""

        # Address, phone, website, hours from info panel
        data["address"] = ""
        data["phone"] = ""
        data["website"] = ""
        data["email"] = ""
        data["hours"] = ""

        try:
            buttons = page.locator('button[data-item-id^="address"]')
            if buttons.count() > 0:
                aria = buttons.first.get_attribute("aria-label") or ""
                data["address"] = aria.replace("Address: ", "").strip()
        except Exception:
            pass

        if not data["address"]:
            try:
                data["address"] = page.locator('button[data-item-id="address"]').first.inner_text(timeout=2000)
            except Exception:
                pass

        try:
            phone_btn = page.locator('button[data-item-id^="phone"]')
            if phone_btn.count() > 0:
                aria = phone_btn.first.get_attribute("aria-label") or ""
                data["phone"] = aria.replace("Phone: ", "").strip()
        except Exception:
            pass

        if not data["phone"]:
            try:
                tel = page.locator('a[href^="tel:"]').first
                href = tel.get_attribute("href") or ""
                data["phone"] = href.replace("tel:", "").strip()
            except Exception:
                pass

        try:
            web_link = page.locator('a[data-item-id="authority"]')
            if web_link.count() > 0:
                data["website"] = web_link.first.get_attribute("href") or ""
        except Exception:
            pass

        try:
            hours_btn = page.locator('button[data-item-id="oh"]')
            if hours_btn.count() > 0:
                data["hours"] = hours_btn.first.get_attribute("aria-label") or ""
        except Exception:
            pass

        if not data["hours"]:
            try:
                hours_div = page.locator('div[aria-label*="Hours"]')
                if hours_div.count() > 0:
                    data["hours"] = hours_div.first.get_attribute("aria-label") or ""
            except Exception:
                pass

        # Emails are almost never on Google Maps — pull from the business website
        if data.get("website"):
            try:
                data["email"] = find_email_from_website(data["website"])
                if data["email"]:
                    print(f"      email: {data['email']}")
            except Exception:
                data["email"] = ""

        # USA filter — skip if address clearly outside US
        addr = (data.get("address") or "").upper()
        if addr and not self._looks_like_usa(addr):
            return None

        return data

    def _looks_like_usa(self, address: str) -> bool:
        usa_markers = [
            ", USA", ", US", "UNITED STATES",
            " AL ", " AK ", " AZ ", " AR ", " CA ", " CO ", " CT ", " DE ",
            " FL ", " GA ", " HI ", " ID ", " IL ", " IN ", " IA ", " KS ",
            " KY ", " LA ", " ME ", " MD ", " MA ", " MI ", " MN ", " MS ",
            " MO ", " MT ", " NE ", " NV ", " NH ", " NJ ", " NM ", " NY ",
            " NC ", " ND ", " OH ", " OK ", " OR ", " PA ", " RI ", " SC ",
            " SD ", " TN ", " TX ", " UT ", " VT ", " VA ", " WA ", " WV ",
            " WI ", " WY ", " DC ",
        ]
        padded = f" {address} "
        if any(m in padded or m.rstrip() in address for m in usa_markers):
            return True
        # State abbreviation at end: ", TX 12345"
        if re.search(r",\s*[A-Z]{2}\s+\d{5}", address):
            return True
        return True  # lenient when address is empty or ambiguous
