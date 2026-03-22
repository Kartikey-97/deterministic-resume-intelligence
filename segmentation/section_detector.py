import re
from collections import defaultdict
from rapidfuzz import fuzz

SECTION_KEYWORDS = {
    "education": [
        "education", "academic background", "academics",
        "scholastic record", "educational qualifications", "scholastics",
        "educational background", "academic qualifications", "qualifications", "degree"
    ],
    "skills": [
        "skills", "technical skills", "core competencies", "technologies",
        "expertise", "tools", "it skills", "technical stack",
        "skills summary", "technical competencies", "competencies & interests"
    ],
    "experience": [
        "experience", "work history", "employment",
        "professional experience", "internships", "work experience",
        "career profile", "technical experience", "professional background",
        "career history", "work summary", "internship experience",
        "academic experience", "industry experience"
    ],
    "projects": [
        "projects", "personal projects", "academic projects",
        "key projects", "research projects", "projects worked on",
        "internship projects", "notable projects", "portfolio"
    ],
    "achievements": [
        "achievements", "awards", "honors", "accolades",
        "accomplishments", "certifications and awards",
        "honors and awards", "recognition"
    ],
    "certifications": [
        "certifications", "licenses", "certificates", "courses",
        "training", "professional development", "online courses",
        "relevant coursework", "coursework"
    ],
    "languages": [
        "languages", "linguistic proficiency", "language proficiency",
        "language skills", "languages known"
    ],
    "extra_curricular": [
        "extra-curricular", "extracurricular", "volunteer", "activities",
        "leadership", "positions of responsibility", "por",
        "co-curricular", "hobbies", "interests",
        "extracurricular activities"
    ],
    "summary": [
        "summary", "profile", "objective", "about me",
        "career overview", "professional overview",
        "professional summary", "career summary",
        "profile info", "about", "personal summary", "executive summary"
    ]
}


def normalize(s: str) -> str:
    return re.sub(r"[^a-z ]", "", s.lower()).strip()


def collapse_spaced_heading(line: str) -> str:
    """
    Converts spaced-letter headings like 'W O R K  E X P E R I E N C E'
    into 'WORK EXPERIENCE' so the fuzzy section matcher can recognise them.

    Heuristic: ≥6 tokens, ≥75% of which are single characters.
    This catches Abhinaya P's resume which uses this format throughout.
    """
    stripped = line.strip()
    words    = stripped.split()
    if len(words) >= 6 and (sum(1 for w in words if len(w) <= 2) / len(words)) >= 0.75:
        collapsed = re.sub(r'(?<=[A-Za-z]) (?=[A-Za-z])', '', stripped)
        collapsed = re.sub(r'\s{2,}', ' ', collapsed).strip()
        return collapsed
    return line

    # ── Pattern B: 'E DUCATION' → 'EDUCATION' ────────────────────────────
    # Trigger condition: at least one pair of [1-char-upper][ALL-CAPS-rest]
    has_b_pattern = any(
        i + 1 < len(words)
        and len(words[i]) == 1
        and words[i].isupper()
        and words[i + 1].isupper()
        and len(words[i + 1]) >= 2
        for i in range(len(words) - 1)
    )

    if has_b_pattern:
        result, i = [], 0
        while i < len(words):
            if (i + 1 < len(words)
                    and len(words[i]) == 1
                    and words[i].isupper()
                    and words[i + 1].isupper()
                    and len(words[i + 1]) >= 2):
                # Merge: 'E' + 'DUCATION' → 'EDUCATION'
                result.append(words[i] + words[i + 1])
                i += 2
            else:
                result.append(words[i])
                i += 1
        return " ".join(result)

    # ── Pattern A: 'W O R K  E X P E R I E N C E' → 'WORK EXPERIENCE' ───
    if len(words) >= 6 and (sum(1 for w in words if len(w) <= 2) / len(words)) >= 0.75:
        collapsed = re.sub(r'(?<=[A-Za-z]) (?=[A-Za-z])', '', stripped)
        collapsed = re.sub(r'\s{2,}', ' ', collapsed).strip()
        return collapsed

    return line


def heading_score(line: str) -> int:
    words = line.split()

    if len(words) > 7:
        return 0

    if re.search(r'\b(20\d{2}|19\d{2}|present|current|now)\b', line.lower()) and len(words) > 4:
        return 0

    if re.match(r'^[-•*▪>o\d]', line.strip()):
        return 0

    score = 0
    if len(words) <= 3:
        score += 1
    if not any(len(w) > 3 for w in words):
        return 0

    caps = sum(1 for w in words if w and w[0].isupper())
    if words and caps / len(words) >= 0.5:
        score += 1

    if not re.search(r"[.,]", line):
        score += 1

    if line.strip().endswith(":"):
        score += 1

    if line.isupper():
        score += 2

    return score


def detect_section(line: str):
    norm = normalize(line)
    if len(norm) < 3:
        return None, 0

    best_section = None
    best_score   = 0
    norm_wc      = len(norm.split())

    for section, keywords in SECTION_KEYWORDS.items():
        for k in keywords:
            score     = fuzz.token_set_ratio(norm, k)
            word_diff = abs(norm_wc - len(k.split()))
            if word_diff > 0:
                score -= min(word_diff * 10, 30)
            if score > best_score:
                best_score   = score
                best_section = section

    if best_score > 75:
        return best_section, best_score

    return None, 0


def segment_resume(text: str):
    lines = [line for line in text.split("\n") if line.strip()]

    sections = defaultdict(lambda: {
        "lines":          [],
        "confidence":     0,
        "headings_found": []
    })

    current = "general"

    for line in lines:
        # Collapse spaced headings (both Pattern A and Pattern B) before scoring
        collapsed = collapse_spaced_heading(line)

        h_score = heading_score(collapsed)

        if h_score >= 2:
            sec, conf = detect_section(collapsed)

            if sec:
                combined_conf = (0.7 * conf) + (0.3 * (h_score / 6 * 100))
                current       = sec

                if sections[sec]["confidence"] < combined_conf:
                    sections[sec]["confidence"] = combined_conf
                sections[sec]["headings_found"].append(line.strip())
                continue

        sections[current]["lines"].append(line)

    for sec, data in sections.items():
        if sec == "general" or data["confidence"] == 0:
            continue
        line_count         = len(data["lines"])
        variance           = min(5.5, line_count * 0.15)
        data["confidence"] = round(min(99.5, data["confidence"] + variance), 2)

    return sections