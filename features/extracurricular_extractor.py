import re

EXTRA_KEYWORDS = [
    "leader", "captain", "volunteer",
    "organizer", "coordinator",
    "club", "society", "community",
    "ngo", "event"
]

def extract_extracurricular(sections):

    lines = sections.get("extra_curricular", {}).get("lines", [])

    if not lines:
        return {
            "has_extra": False,
            "leadership_score": 0
        }

    text = " ".join(lines).lower()

    leadership = sum(
        1 for k in EXTRA_KEYWORDS if k in text
    )

    return {
        "has_extra": True,
        "leadership_score": min(leadership, 5)
    }