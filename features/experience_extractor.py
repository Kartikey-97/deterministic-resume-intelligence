"""
features/experience_extractor.py  — v12 (The Absolute Final Nuke)

Fixes:
1. The "Bachelor Startup" Bug: Adds academic words to the generic dictionary so 
   degrees are no longer mistaken for valid company names.
2. Aggressive Academic Classifier: Instantly trashes any role block containing "bachelor", "degree", etc.
3. Bulletproof Spatial Shield: Bypasses `re.escape` space bugs using token splitting.
4. Cross-Scan Shield: Applies the spatial shield to Extra Sections.
"""

import re
from datetime import datetime
from collections import deque

MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "may": 5, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "oct": 10, "nov": 11, "dec": 12
}

INTERN_KEYWORDS        = ["intern", "internship", "trainee", "apprentice"]

_DESCRIPTION_STARTS = {
    "experienced", "skilled", "developed", "built", "worked", "contributed",
    "implemented", "designed", "created", "managed", "led", "responsible",
    "demonstrated", "gained", "utilized", "performed", "assisted",
    "collaborated", "supported", "involved", "participated", "completed",
    "focused", "passionate", "dedicated", "motivated", "proficient",
}

_TIER1_EDU = [
    "b.tech", "btech", "m.tech", "mtech", "b.voc",
    "bachelor of", "master of", "diploma in",
    "higher secondary", "secondary school", "senior secondary",
    "college of engineering", "college of technology",
    "institute of technology", "institute of management",
    "institute of engineering",
    "cgpa", " gpa", "sgpa", "aggregate",
    "b.sc", "b.com", "m.sc", "m.com",
    "b tech", "b.e", "b e",
    "semester", "coursework", "pursuing", "batch of",
]

_TIER25_SUFFIX = re.compile(
    r'\b(university|institute|college|school|academy|polytechnic|vidyapeeth)\b',
    re.IGNORECASE
)
_TIER2_EDU = ["university", "vidyalaya", "inter college"]

_EDU_BUFFER_BLOCK = re.compile(
    r'\b(university|college|institute|school|academy|polytechnic|vidyapeeth|'
    r'pursuing|semester|batch|enrolled|cgpa|sgpa|gpa|aggregate|coursework)\b',
    re.IGNORECASE
)
_LOCATION_ONLY    = re.compile(r'^[A-Za-z\s,\.]+,\s*[A-Za-z\s]+$')


def is_education_bleed(text: str) -> bool:
    ll = text.lower()
    if any(kw in ll for kw in _TIER1_EDU): return True
    if len(ll.split()) <= 5 and _TIER25_SUFFIX.search(ll): return True
    if not re.search(r'\b(19|20)\d{2}\b', ll): return False
    if any(kw in ll for kw in _TIER2_EDU): return True
    if re.search(r'\binstitute\b', ll): return True
    if re.search(r'\bcollege\b', ll): return True
    if re.search(r'\bschool\b', ll): return True
    return False


def _has_intern_kw(text: str) -> bool:
    return any(re.search(r"\b" + re.escape(kw) + r"\b", text.lower()) for kw in INTERN_KEYWORDS)


def _is_edu_line_for_buffer(line: str) -> bool:
    s = line.strip()
    if _EDU_BUFFER_BLOCK.search(s): return True
    words = s.split()
    if len(words) <= 4 and _LOCATION_ONLY.match(s) and not _has_intern_kw(s): return True
    return False


def _should_use_as_lookback(line: str) -> bool:
    s = line.strip()
    if not s or len(s) < 3: return False
    if re.match(r'^[-•*▪>]', s): return False
    if re.search(r'\b(19|20)\d{2}\b', s): return False
    if _is_edu_line_for_buffer(s): return False
    if _has_intern_kw(s): return True
    if len(s.split()) > 7: return False
    first = s.split()[0].lower().rstrip('.,;:')
    if first in _DESCRIPTION_STARTS: return False
    return True


_GENERIC_ROLE_WORDS = {
    "developer", "engineer", "analyst", "designer", "manager", "consultant",
    "intern", "trainee", "student", "researcher", "architect", "specialist",
    "lead", "senior", "junior", "associate", "assistant", "coordinator",
    "mern", "mean", "full", "stack", "frontend", "backend", "web", "mobile",
    "software", "hardware", "data", "ml", "ai", "cloud", "devops",
    "python", "java", "javascript", "react", "node", "angular", "flutter",
    "android", "ios", "machine", "learning", "deep", "neural", "language",
    "processing", "computer", "vision", "security", "programmer", "coder",
    "technical", "and", "the", "for", "at", "in", "of", "to", "with",
    "science", "technology", "commerce", "arts", "engineering", "business",
    "information", "systems", "management", "studies", "mathematics",
    "physics", "chemistry", "electronics", "electrical", "mechanical",
    "civil", "biomedical", "biochemistry", "biotechnology",
    "pursuing", "undergraduate", "postgraduate", "graduate",
    # V12 NEW: Kill the "Bachelor Startup" Bug
    "bachelor", "master", "doctorate", "phd", "degree", "diploma", 
    "school", "university", "college", "institute", "academy"
}


def _has_employer_in_pre_date(block: str) -> bool:
    m = re.search(r'((?:[a-zA-Z]{3,}\s+)?\d{2,4}|\d{2}/\d{4})\s*[-–to]+', block, re.IGNORECASE)
    if not m: return False
    pre = block[:m.start()].strip()
    pre = re.sub(r'^[\(\[\{•\-\*▪>]+\s*', '', pre).strip()
    if not pre: return False
    words = [w.lower().rstrip('.,;:()') for w in pre.split() if len(w) > 2]
    
    if len(words) > 6: return False
    if not words: return False
    return any(w not in _GENERIC_ROLE_WORDS for w in words)


def get_baseline_year(text_block: str) -> int:
    years = [int(y) for y in re.findall(r'\b(19\d{2}|20\d{2})\b', text_block)]
    return max(years) if years else datetime.now().year


def parse_month(text: str):
    return MONTHS.get(text.lower()[:3], None)


def parse_date(token: str, baseline_year: int):
    token = token.strip().lower()
    if "present" in token or "current" in token or "now" in token:
        now = datetime.now()
        return datetime(now.year, now.month, 1)
    m = re.match(r"([a-z]{3,})\s+(\d{4})", token)
    if m: return datetime(int(m.group(2)), parse_month(m.group(1)) or 1, 1)
    m = re.match(r"(\d{2})/(\d{4})", token)
    if m: return datetime(int(m.group(2)), int(m.group(1)), 1)
    m = re.match(r"(\d{4})", token)
    if m: return datetime(int(m.group(1)), 1, 1)
    return None


def extract_durations(text_block: str) -> list:
    durations = []
    baseline_year = get_baseline_year(text_block)
    date_pattern = (
        r"((?:[a-zA-Z]{3,}\s+)?\d{2,4}|\d{2}/\d{4})"
        r"\s*[-–to]+"
        r"\s*([a-zA-Z]{3,}\s+\d{4}|\d{2}/\d{4}|\d{2,4}|present|current|now)"
    )
    for match in re.findall(date_pattern, text_block, re.IGNORECASE):
        start = parse_date(match[0], baseline_year)
        end = parse_date(match[1], baseline_year)
        if start and end and end >= start:
            durations.append(max((end.year - start.year) * 12 + (end.month - start.month), 1))
    if not durations:
        m = re.search(r'\((\d{1,2})\s*months?\)', text_block, re.IGNORECASE)
        if m:
            months = int(m.group(1))
            if 1 <= months <= 24: durations.append(months)
    return durations


def block_has_date(block: str) -> bool:
    return bool(re.search(r"((?:[a-zA-Z]{3,}\s+)?\d{2,4}|\d{2}/\d{4})\s*[-–to]+", block, re.IGNORECASE))


def _has_explicit_duration(block: str) -> bool:
    m = re.search(r'\((\d{1,2})\s*months?\)', block, re.IGNORECASE)
    return bool(m) and 1 <= int(m.group(1)) <= 24 if m else False


def classify_role(text: str) -> str:
    t = text.lower()
    
    # V12 NEW: Aggressive phrase-level academic matches
    for kw in ["student", "studying", "pursuing", "enrolled", "undergraduate", 
               "postgraduate", "b.tech", "btech", "mca", "mba", 
               "b tech", "b.e", "bachelor", "degree", "diploma", "class 10", "class 12", "master", "phd"]:
        if kw in t: return "academic"

    date_m = re.search(r'((?:[a-zA-Z]{3,}\s+)?\d{2,4}|\d{2}/\d{4})\s*[-–to]+', text, re.IGNORECASE)
    if date_m:
        pre = text[:date_m.start()].strip().lower()
        for kw in ["scholar", "semester", "coursework", "university", "college", "institute"]:
            if re.search(r"\b" + re.escape(kw) + r"\b", pre, re.IGNORECASE): return "academic"
        for kw in INTERN_KEYWORDS:
            if re.search(r"\b" + re.escape(kw) + r"\b", pre, re.IGNORECASE): return "intern"
            
        full_m = re.search(
            r'((?:[a-zA-Z]{3,}\s+)?\d{2,4}|\d{2}/\d{4})\s*[-–to]+'
            r'\s*(?:[a-zA-Z]{3,}\s+\d{4}|\d{2}/\d{4}|\d{2,4}|present|current|now)',
            text, re.IGNORECASE
        )
        if full_m:
            post_clean = re.split(r'[•\*▪]\s', text[full_m.end():full_m.end() + 60].strip())[0]
            for kw in INTERN_KEYWORDS:
                if re.search(r"\b" + re.escape(kw) + r"\b", post_clean.lower()): return "intern"
    else:
        first_ten = " ".join(text.split()[:10]).lower()
        for kw in ["scholar", "semester"]:
            if re.search(r"\b" + kw + r"\b", first_ten, re.IGNORECASE): return "academic"
        for kw in INTERN_KEYWORDS:
            if re.search(r"\b" + re.escape(kw) + r"\b", first_ten, re.IGNORECASE): return "intern"

    return "fulltime"


_RANGE_SPLIT = (
    r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|[a-zA-Z]{3,}|\d{2}/)?"
    r"\s*\d{4}\s*[-–to]+"
    r"\s*(?:[a-zA-Z]{3,}\s*\d{4}|\d{2}/\d{4}|\d{4}|present|current|now)"
)
_SINGLE_DATE = r'\b\d{2}/\d{4}\b|\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4}\b'
_EXPLICIT_DUR_PAT = r'\(\d{1,2}\s*months?\)'


def _build_role_blocks(lines: list) -> list:
    roles, block = [], ""
    _lookback_buf = deque(maxlen=2)

    for line in lines:
        stripped = line.strip()
        if len(stripped) < 5: continue

        is_range = bool(re.search(_RANGE_SPLIT, stripped.lower()))
        is_single = not is_range and bool(re.search(_SINGLE_DATE, stripped.lower()))
        is_dur = not is_range and not is_single and bool(re.search(_EXPLICIT_DUR_PAT, stripped, re.IGNORECASE))

        if is_range or is_single or is_dur:
            if block:
                if block_has_date(block): roles.append(block)
                elif _has_explicit_duration(block): roles.append(block)
                else:
                    for w in block.strip().split("\n"):
                        w = w.strip()
                        if w and _should_use_as_lookback(w): _lookback_buf.append(w)

            eligible = [l for l in _lookback_buf if _should_use_as_lookback(l)]
            lookback = " ".join(eligible).strip() if eligible else ""
            block = (lookback + " " + stripped).strip() if lookback else stripped
            _lookback_buf.clear()
        else:
            block += " " + stripped
            if _should_use_as_lookback(stripped): _lookback_buf.append(stripped)

    if block:
        if block_has_date(block): roles.append(block)
        elif _has_intern_kw(block): roles.append(block)
        elif _has_explicit_duration(block): roles.append(block)

    return roles


def _scan_extra_sections(sections: dict) -> list:
    extra_roles = []
    targets = {"certifications": False, "projects": True}
    
    global_lines = []
    for sec in sections.values():
        global_lines.extend(sec.get("lines", []))
    spatial_map = " \n ".join(global_lines)

    for sec_name, require_intern_heading in targets.items():
        sec_data = sections.get(sec_name, {})
        lines = [l.strip() for l in sec_data.get("lines", []) if len(l.strip()) >= 4]
        if not lines: continue
        if require_intern_heading:
            headings = sec_data.get("headings_found", [])
            if not any("intern" in h.lower() for h in headings): continue
        used = set()
        for i, line in enumerate(lines):
            if i in used or not block_has_date(line): continue
            
            # V12: Token-based Spatial Shield for Cross-Scan
            survives_shield = True
            date_matches = re.finditer(
                r'((?:[a-zA-Z]{3,}\s+)?\d{2,4}|\d{2}/\d{4})\s*[-–to]+'
                r'\s*(?:[a-zA-Z]{3,}\s+\d{4}|\d{2}/\d{4}|\d{2,4}|present|current|now)',
                line, re.IGNORECASE
            )
            for date_m in date_matches:
                raw_date_str = date_m.group(0)
                tokens = raw_date_str.split()
                spatial_pat = r'[\s\n]+'.join(re.escape(t) for t in tokens)
                sm = re.search(spatial_pat, spatial_map, re.IGNORECASE)
                if sm:
                    s_start, s_end = max(0, sm.start() - 250), min(len(spatial_map), sm.end() + 250)
                    window = spatial_map[s_start:s_end]
                    if re.search(r'\b(b\.?tech|bachelor|degree|university|college|cbse|diploma|high\s+school|ssc|hsc|student|class)\b', window, re.IGNORECASE):
                        survives_shield = False
                        break
            if not survives_shield:
                continue

            ctx_start, ctx_end = max(0, i - 2), min(len(lines), i + 3)
            context = " ".join(lines[ctx_start:ctx_end])
            has_training = bool(re.search(r'\btraining\b', context, re.IGNORECASE))
            has_intern = _has_intern_kw(context)
            intern_heading = any("intern" in h.lower() for h in sec_data.get("headings_found", []))
            
            if has_training or has_intern or intern_heading:
                extra_roles.append(context)
                for j in range(ctx_start, ctx_end): used.add(j)
                
    return extra_roles


def extract_experience(sections: dict) -> dict:
    raw_lines = sections.get("experience", {}).get("lines", [])

    if not raw_lines:
        return {"total_experience_years": 0, "internship_count": 0,
                "fulltime_count": 0, "roles_detected": []}

    raw_lines = [
        l.replace('\xa0', ' ').replace('\u200b', '').replace('\u202f', ' ').replace('\u2009', ' ').replace('\u00ad', '')
        for l in raw_lines
    ]

    experience_lines = [l for l in raw_lines if not is_education_bleed(l)]
    roles = _build_role_blocks(experience_lines)
    roles = [r for r in roles if not is_education_bleed(r)]

    spatial_map = " \n ".join(raw_lines)
    filtered_roles = []
    
    for r in roles:
        if block_has_date(r):
            survives = True
            date_matches = re.finditer(
                r'((?:[a-zA-Z]{3,}\s+)?\d{2,4}|\d{2}/\d{4})\s*[-–to]+'
                r'\s*(?:[a-zA-Z]{3,}\s+\d{4}|\d{2}/\d{4}|\d{2,4}|present|current|now)',
                r, re.IGNORECASE
            )
            for date_m in date_matches:
                raw_date_str = date_m.group(0)
                # V12: Token-based Spatial Shield
                tokens = raw_date_str.split()
                spatial_pat = r'[\s\n]+'.join(re.escape(t) for t in tokens)
                
                sm = re.search(spatial_pat, spatial_map, re.IGNORECASE)
                if sm:
                    s_start = max(0, sm.start() - 250)
                    s_end   = min(len(spatial_map), sm.end() + 250)
                    window  = spatial_map[s_start:s_end]
                    if re.search(r'\b(b\.?tech|bachelor|degree|university|college|cbse|diploma|high\s+school|ssc|hsc|student|class)\b', window, re.IGNORECASE):
                        survives = False
                        break

            if not survives:
                continue

            if _has_employer_in_pre_date(r) or _has_intern_kw(r):
                filtered_roles.append(r)
        else:
            filtered_roles.append(r)

    roles = filtered_roles
    roles.extend(_scan_extra_sections(sections))

    total_fulltime_months = 0
    internship_count      = 0
    fulltime_count        = 0
    role_details          = []

    for role in roles:
        role_type = classify_role(role)
        durations = extract_durations(role)
        duration  = max(durations) if durations else 0

        # V12: Instantly bypass the duration loop if it's academic!
        if role_type == "academic":
            continue
        elif role_type == "intern":
            internship_count += 1
        else:
            if duration > 42 and not _has_employer_in_pre_date(role):
                continue
            fulltime_count        += 1
            total_fulltime_months += duration

        role_details.append({"type": role_type, "duration_months": duration})

    total_years = min(round(total_fulltime_months / 12, 2), 5.0)

    return {
        "total_experience_years": total_years,
        "internship_count":       internship_count,
        "fulltime_count":         fulltime_count,
        "roles_detected":         role_details
    }