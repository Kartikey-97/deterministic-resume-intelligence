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

def get_baseline_year(text_block):
    years = [int(y) for y in re.findall(r'\b(19\d{2}|20\d{2})\b', text_block)]
    return max(years) if years else datetime.now().year

def parse_month(text):
    text = text.lower()[:3]
    return MONTHS.get(text, None)

def parse_date(token, baseline_year):
    token = token.strip().lower()
    
    if "present" in token or "current" in token or "now" in token:
        now = datetime.now()
        return datetime(now.year, now.month, 1)

    m = re.match(r"([a-z]{3,})\s+(\d{4})", token)
    if m:
        month = parse_month(m.group(1))
        year = int(m.group(2))
        return datetime(year, month or 1, 1)

    m = re.match(r"(\d{2})/(\d{4})", token)
    if m:
        return datetime(int(m.group(2)), int(m.group(1)), 1)

    m = re.match(r"(\d{4})", token)
    if m:
        return datetime(int(m.group(1)), 1, 1)

    return None

def extract_durations(text_block):
    durations = []
    baseline_year = get_baseline_year(text_block)
    
    date_pattern = r"((?:[a-zA-Z]{3,}\s+)?\d{2,4}|\d{2}/\d{4})\s*[-–to]+\s*([a-zA-Z]{3,}\s+\d{4}|\d{2}/\d{4}|\d{2,4}|present|current|now)"
    for match in re.findall(date_pattern, text_block, re.IGNORECASE):
        start = parse_date(match[0], baseline_year)
        end = parse_date(match[1], baseline_year)
        
        if start and end and end >= start:
            months = (end.year - start.year) * 12 + (end.month - start.month)
            durations.append(max(months, 1)) 
            
    return durations

def classify_role(text):
    t = text.lower()
    for kw in INTERN_KEYWORDS:
        if re.search(r"\b" + re.escape(kw) + r"\b", t):
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
    block = ""
    split_pattern = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|[a-zA-Z]{3,}|\d{2}/)?\s*\d{4}\s*[-–to]+\s*(?:[a-zA-Z]{3,}\s*\d{4}|\d{2}/\d{4}|\d{4}|present|current|now)"
    
    for line in experience_lines:
        if len(line.strip()) < 5:
            continue
        if re.search(split_pattern, line.lower()):
            if block:
                roles.append(block)
            block = line
        else:
            block += " " + line
            
    if block:
        roles.append(block)

    # THE FIX: Separate full-time math from internship math
    total_fulltime_months = 0 
    internship_count = 0
    fulltime_count = 0
    role_details = []

    for role in roles:
        role_type = classify_role(role)
        durations = extract_durations(role)
        duration = max(durations) if durations else 0
        
        if role_type == "intern":
            internship_count += 1
            # We explicitly do NOT add intern duration to total fulltime experience
        else:
            fulltime_count += 1
            total_fulltime_months += duration
            
        role_details.append({
            "type": role_type,
            "duration_months": duration
        })

    # Total years now only reflects true full-time seniority
    total_years = round(total_fulltime_months / 12, 2)
    total_years = min(total_years, 5.0) 

    return {
        "total_experience_years": total_years,
        "internship_count": internship_count,
        "fulltime_count": fulltime_count,
        "roles_detected": role_details
    }