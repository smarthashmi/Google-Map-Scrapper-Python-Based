"""Checkpoint management for resume-after-shutdown support."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = PROJECT_ROOT / "state"
CHECKPOINT_FILE = STATE_DIR / "checkpoint.json"


@dataclass
class Checkpoint:
    session_id: str = ""
    started_at: str = ""
    last_updated: str = ""
    keywords: list[str] = field(default_factory=list)
    locations: list[list[str]] = field(default_factory=list)  # [[place, state, type], ...]
    keyword_index: int = 0
    location_index: int = 0
    completed_searches: list[str] = field(default_factory=list)
    scraped_place_ids: list[str] = field(default_factory=list)
    total_scraped: int = 0
    headless: bool = True
    max_results_per_search: int = 80
    status: str = "idle"  # idle | running | paused | completed

    def search_key(self, keyword: str, place: str, state: str, loc_type: str = "city") -> str:
        return f"{keyword}||{place}|{state}|{loc_type}"

    def is_search_done(self, keyword: str, place: str, state: str, loc_type: str = "city") -> bool:
        key = self.search_key(keyword, place, state, loc_type)
        if key in self.completed_searches:
            return True
        # Backward compat with older 2-part search keys
        legacy = f"{keyword}||{place}|{state}" if state else f"{keyword}||{place}"
        return legacy in self.completed_searches

    def mark_search_done(self, keyword: str, place: str, state: str, loc_type: str = "city") -> None:
        key = self.search_key(keyword, place, state, loc_type)
        if key not in self.completed_searches:
            self.completed_searches.append(key)

    def touch(self) -> None:
        self.last_updated = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Checkpoint:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


def ensure_state_dir() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def load_checkpoint() -> Checkpoint | None:
    ensure_state_dir()
    if not CHECKPOINT_FILE.exists():
        return None
    try:
        data = json.loads(CHECKPOINT_FILE.read_text(encoding="utf-8"))
        return Checkpoint.from_dict(data)
    except (json.JSONDecodeError, TypeError):
        return None


def save_checkpoint(checkpoint: Checkpoint) -> None:
    ensure_state_dir()
    checkpoint.touch()
    CHECKPOINT_FILE.write_text(
        json.dumps(checkpoint.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def clear_checkpoint() -> None:
    if CHECKPOINT_FILE.exists():
        CHECKPOINT_FILE.unlink()


def has_resumable_session() -> bool:
    cp = load_checkpoint()
    return cp is not None and cp.status in ("running", "paused") and (
        cp.keyword_index < len(cp.keywords) or cp.location_index < len(cp.locations)
    )
