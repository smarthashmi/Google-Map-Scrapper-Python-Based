"""USA cities, counties, and states for geographic search coverage."""

from __future__ import annotations

import json
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent / "data" / "usa_geo.json"

# Legacy top cities list (for quick presets 1-3)
USA_CITIES = [
    ("New York", "NY"), ("Los Angeles", "CA"), ("Chicago", "IL"), ("Houston", "TX"),
    ("Phoenix", "AZ"), ("Philadelphia", "PA"), ("San Antonio", "TX"), ("San Diego", "CA"),
    ("Dallas", "TX"), ("San Jose", "CA"), ("Austin", "TX"), ("Jacksonville", "FL"),
    ("Fort Worth", "TX"), ("Columbus", "OH"), ("Charlotte", "NC"), ("San Francisco", "CA"),
    ("Indianapolis", "IN"), ("Seattle", "WA"), ("Denver", "CO"), ("Washington", "DC"),
    ("Boston", "MA"), ("Nashville", "TN"), ("Detroit", "MI"), ("Oklahoma City", "OK"),
    ("Portland", "OR"), ("Las Vegas", "NV"), ("Memphis", "TN"), ("Louisville", "KY"),
    ("Baltimore", "MD"), ("Milwaukee", "WI"), ("Albuquerque", "NM"), ("Tucson", "AZ"),
    ("Fresno", "CA"), ("Sacramento", "CA"), ("Kansas City", "MO"), ("Mesa", "AZ"),
    ("Atlanta", "GA"), ("Omaha", "NE"), ("Colorado Springs", "CO"), ("Raleigh", "NC"),
    ("Miami", "FL"), ("Long Beach", "CA"), ("Virginia Beach", "VA"), ("Oakland", "CA"),
    ("Minneapolis", "MN"), ("Tampa", "FL"), ("Tulsa", "OK"), ("Arlington", "TX"),
    ("New Orleans", "LA"), ("Wichita", "KS"), ("Cleveland", "OH"), ("Bakersfield", "CA"),
    ("Aurora", "CO"), ("Anaheim", "CA"), ("Honolulu", "HI"), ("Santa Ana", "CA"),
    ("Riverside", "CA"), ("Corpus Christi", "TX"), ("Lexington", "KY"), ("Henderson", "NV"),
    ("Stockton", "CA"), ("Saint Paul", "MN"), ("Cincinnati", "OH"), ("St. Louis", "MO"),
    ("Pittsburgh", "PA"), ("Greensboro", "NC"), ("Lincoln", "NE"), ("Anchorage", "AK"),
    ("Plano", "TX"), ("Orlando", "FL"), ("Irvine", "CA"), ("Newark", "NJ"),
    ("Durham", "NC"), ("Chula Vista", "CA"), ("Toledo", "OH"), ("Fort Wayne", "IN"),
    ("St. Petersburg", "FL"), ("Laredo", "TX"), ("Jersey City", "NJ"), ("Chandler", "AZ"),
    ("Madison", "WI"), ("Lubbock", "TX"), ("Scottsdale", "AZ"), ("Reno", "NV"),
    ("Buffalo", "NY"), ("Gilbert", "AZ"), ("Glendale", "AZ"), ("North Las Vegas", "NV"),
    ("Winston-Salem", "NC"), ("Chesapeake", "VA"), ("Norfolk", "VA"), ("Fremont", "CA"),
    ("Garland", "TX"), ("Irving", "TX"), ("Hialeah", "FL"), ("Richmond", "VA"),
    ("Boise", "ID"), ("Spokane", "WA"), ("Baton Rouge", "LA"), ("Tacoma", "WA"),
    ("San Bernardino", "CA"), ("Modesto", "CA"), ("Fontana", "CA"), ("Des Moines", "IA"),
    ("Moreno Valley", "CA"), ("Fayetteville", "NC"), ("Birmingham", "AL"), ("Rochester", "NY"),
    ("Salt Lake City", "UT"), ("Grand Rapids", "MI"), ("Huntsville", "AL"), ("Amarillo", "TX"),
    ("Mobile", "AL"), ("Little Rock", "AR"), ("Augusta", "GA"), ("Columbus", "GA"),
    ("Knoxville", "TN"), ("Shreveport", "LA"), ("Grand Prairie", "TX"), ("Tallahassee", "FL"),
    ("Overland Park", "KS"), ("Port St. Lucie", "FL"), ("Cape Coral", "FL"), ("Sioux Falls", "SD"),
    ("Providence", "RI"), ("Charleston", "SC"), ("Fort Collins", "CO"), ("Savannah", "GA"),
    ("Eugene", "OR"), ("Hartford", "CT"), ("Billings", "MT"), ("Manchester", "NH"),
    ("Wilmington", "DE"), ("Charleston", "WV"), ("Burlington", "VT"), ("Fargo", "ND"),
    ("Cheyenne", "WY"), ("Jackson", "MS"), ("Montgomery", "AL"),
]

USA_STATES = [
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
    "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho",
    "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana",
    "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota",
    "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada",
    "New Hampshire", "New Jersey", "New Mexico", "New York",
    "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon",
    "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
    "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington",
    "West Virginia", "Wisconsin", "Wyoming", "District of Columbia",
]

STATE_NAME_TO_ABBR = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID",
    "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
    "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN",
    "Mississippi": "MS", "Missouri": "MO", "Montana": "MT", "Nebraska": "NE",
    "Nevada": "NV", "New Hampshire": "NH", "New Jersey": "NJ",
    "New Mexico": "NM", "New York": "NY", "North Carolina": "NC",
    "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK", "Oregon": "OR",
    "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
    "Vermont": "VT", "Virginia": "VA", "Washington": "WA",
    "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY",
    "District of Columbia": "DC",
}

# Location tuple: [place_name, state_abbr, location_type]  type = city | county
Location = list[str]

_geo_cache: dict | None = None


def _load_geo() -> dict:
    global _geo_cache
    if _geo_cache is None:
        with DATA_FILE.open(encoding="utf-8") as f:
            _geo_cache = json.load(f)
    return _geo_cache


def build_county_city_locations(state_abbrs: list[str] | None = None) -> list[Location]:
    """Build search targets: every county + major cities per state."""
    geo = _load_geo()
    locations: list[Location] = []
    states = state_abbrs or sorted(geo["locations"].keys())

    for st in states:
        data = geo["locations"].get(st)
        if not data:
            continue
        for county in data.get("counties", []):
            locations.append([county, st, "county"])
        for city in data.get("cities", []):
            locations.append([city, st, "city"])

    return locations


def build_state_locations(state_name_or_abbr: str) -> list[Location]:
    """All counties + cities for one state."""
    abbr = state_name_or_abbr.upper()
    if len(abbr) != 2:
        abbr = STATE_NAME_TO_ABBR.get(state_name_or_abbr.title(), "")
        if not abbr:
            for name, code in STATE_NAME_TO_ABBR.items():
                if name.lower() == state_name_or_abbr.lower():
                    abbr = code
                    break
    if not abbr:
        return []
    return build_county_city_locations([abbr])


def _legacy_city_locations(cities: list[tuple[str, str]]) -> list[Location]:
    return [[city, state, "city"] for city, state in cities]


def get_location_stats(locations: list[Location]) -> dict[str, int]:
    counties = sum(1 for loc in locations if len(loc) > 2 and loc[2] == "county")
    cities = sum(1 for loc in locations if len(loc) > 2 and loc[2] == "city")
    states = len({loc[1] for loc in locations if len(loc) > 1})
    return {"counties": counties, "cities": cities, "states": states, "total": len(locations)}


def get_full_usa_count() -> int:
    return len(build_county_city_locations())


def build_all_states_locations() -> list[Location]:
    """All 50 states + DC — every county and major city. No manual input needed."""
    return build_county_city_locations()


LOCATION_PRESETS = {
    "1": {
        "name": "ALL 50 STATES - Every County + City (~3,500 locations)",
        "builder": build_all_states_locations,
    },
    "2": {
        "name": "Top 50 US Cities (quick test)",
        "builder": lambda: _legacy_city_locations(USA_CITIES[:50]),
    },
    "3": {
        "name": "Top 100 US Cities",
        "builder": lambda: _legacy_city_locations(USA_CITIES[:100]),
    },
    "4": {
        "name": "All Major Cities (~120)",
        "builder": lambda: _legacy_city_locations(USA_CITIES),
    },
}


def format_location(place: str, state: str, loc_type: str = "city") -> str:
    if state:
        return f"{place}, {state}, USA"
    return f"{place}, USA"


def location_label(place: str, state: str, loc_type: str = "city") -> str:
    kind = "County" if loc_type == "county" else "City"
    return f"{place}, {state} ({kind})"


def normalize_location(raw: list[str]) -> Location:
    """Support legacy [city, state] and new [place, state, type] formats."""
    if len(raw) >= 3:
        return [raw[0], raw[1], raw[2]]
    return [raw[0], raw[1] if len(raw) > 1 else "", "city"]
