import re
from datetime import datetime


MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "may": 5, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "oct": 10, "nov": 11, "dec": 12
}

INTERN_KEYWORDS = [
    "intern", "internship", "trainee", "apprentice"
]


def parse_month(text):
    text = text.lower()[:3]
    return MONTHS.get(text, None)


def parse_date(token):
    token = token.strip().lower()

    # Month + year
    m = re.match(r"([a-zA-Z]{3,})\s+(\d{4})", token)
    if m:
        month = parse_month(m.group(1))
        year = int(m.group(2))
        if month:
            return datetime(year, month, 1)

    # Year only
    m = re.match(r"(\d{4})", token)
    if m:
        year = int(m.group(1))
        return datetime(year, 1, 1)

    # Present / current
    if "present" in token or "current" in token:
        return datetime.now()

    return None


def extract_durations(text_block):

    durations = []

    # Regex for date ranges
    patterns = [
        r"([A-Za-z]{3,}\s+\d{4})\s*[-–]\s*([A-Za-z]{3,}\s+\d{4}|present|current)",
        r"(\d{4})\s*[-–]\s*(\d{4}|present|current)"
    ]

    for pattern in patterns:
        for match in re.findall(pattern, text_block, re.IGNORECASE):
            start = parse_date(match[0])
            end = parse_date(match[1])

            if start and end and end > start:
                months = (end.year - start.year) * 12 + (end.month - start.month)
                durations.append(months)

    return durations


def classify_role(text):

    t = text.lower()
    for kw in INTERN_KEYWORDS:
        if kw in t:
            return "intern"

    return "fulltime"


def extract_experience(sections):

    experience_lines = sections.get("experience", {}).get("lines", [])

    if not experience_lines:
        return {
            "total_experience_years": 0,
            "internship_count": 0,
            "fulltime_count": 0,
            "roles_detected": []
        }

    roles = []

    # Heuristic: group lines into blocks
    block = ""
    for line in experience_lines:
        if len(line.strip()) < 5:
            continue

        # detect new role if date present
        if re.search(r"\d{4}", line) and block:
            roles.append(block)
            block = line
        else:
            block += " " + line

    if block:
        roles.append(block)

    total_months = 0
    internship_count = 0
    fulltime_count = 0
    role_details = []

    for role in roles:

        role_type = classify_role(role)

        durations = extract_durations(role)
        duration = max(durations) if durations else 0

        total_months += duration

        if role_type == "intern":
            internship_count += 1
        else:
            fulltime_count += 1

        role_details.append({
            "type": role_type,
            "duration_months": duration
        })

    return {
        "total_experience_years": round(total_months / 12, 2),
        "internship_count": internship_count,
        "fulltime_count": fulltime_count,
        "roles_detected": role_details
    }