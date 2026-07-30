"""Predefined search keywords for auto repair and related small businesses."""

AUTO_REPAIR_KEYWORDS = [
    "auto repair shop",
    "car repair",
    "auto mechanic",
    "automotive repair",
    "brake repair shop",
    "oil change service",
    "transmission repair",
    "auto body shop",
    "collision repair center",
    "tire shop",
    "wheel alignment service",
    "muffler repair",
    "engine repair shop",
    "car maintenance service",
    "auto glass repair",
    "diesel repair shop",
    "mobile mechanic",
    "quick lube",
    "car diagnostic service",
    "AC repair auto",
    "radiator repair",
    "exhaust repair shop",
    "suspension repair",
    "auto electrical repair",
    "fleet vehicle repair",
    "truck repair shop",
    "motorcycle repair shop",
    "smog check station",
    "car detailing and repair",
    "pre-owned car service center",
]

# Grouped presets for the interactive menu
KEYWORD_PRESETS = {
    "1": {
        "name": "Full Auto Repair Pack (30 keywords)",
        "keywords": AUTO_REPAIR_KEYWORDS,
    },
    "2": {
        "name": "Core Repair Shops (10 keywords)",
        "keywords": AUTO_REPAIR_KEYWORDS[:10],
    },
    "3": {
        "name": "Body & Collision (5 keywords)",
        "keywords": [
            "auto body shop",
            "collision repair center",
            "dent repair shop",
            "paint and body shop",
            "frame straightening shop",
        ],
    },
    "4": {
        "name": "Maintenance & Quick Service (8 keywords)",
        "keywords": [
            "oil change service",
            "quick lube",
            "tire shop",
            "wheel alignment service",
            "brake repair shop",
            "car wash and lube",
            "smog check station",
            "car battery replacement",
        ],
    },
    "5": {
        "name": "Specialty & Mobile (6 keywords)",
        "keywords": [
            "mobile mechanic",
            "diesel repair shop",
            "truck repair shop",
            "motorcycle repair shop",
            "fleet vehicle repair",
            "auto electrical repair",
        ],
    },
}


def get_preset_menu_text() -> str:
    lines = ["", "  PREDEFINED KEYWORD PACKS:", "  " + "-" * 40]
    for key, preset in KEYWORD_PRESETS.items():
        lines.append(f"  [{key}] {preset['name']}")
    lines.append("  [C] Custom keywords (type your own)")
    lines.append("  [M] Mix: pick multiple packs")
    return "\n".join(lines)
