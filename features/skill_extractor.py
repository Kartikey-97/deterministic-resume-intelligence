import re
from rapidfuzz import fuzz
from features.skill_taxonomy import SKILL_TAXONOMY


def extract_skills(sections):

    detected = {}

    # Collect skills from multiple high-signal sections
    skill_lines = []
    for sec in ["skills", "projects", "experience", "certifications"]:
        skill_lines.extend(sections.get(sec, {}).get("lines", []))

    # Join text
    skill_text = " ".join(skill_lines).lower()

    # Tokenize once
    tokens = set(skill_text.split())

    # Domain-based extraction
    for domain, skills in SKILL_TAXONOMY.items():

        detected[domain] = []

        for skill, variations in skills.items():

            found = False

            # Exact match first (production-safe)
            for v in variations:
                pattern = r"\b" + re.escape(v) + r"\b"
                if re.search(pattern, skill_text):
                    detected[domain].append(skill)
                    found = True
                    break

            # Fuzzy fallback only if needed
            if not found:
                for v in variations:

                    # Reduce noise and speed up
                    if any(v_part in tokens for v_part in v.split()):
                        score = fuzz.partial_ratio(v, skill_text)
                    else:
                        score = 0

                    if score > 85:
                        detected[domain].append(skill)
                        break

    return detected