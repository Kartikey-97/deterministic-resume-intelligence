import re

def extract_school_marks(sections):

    edu_lines = sections.get("education", {}).get("lines", [])

    if not edu_lines:
        return {
            "school_score": 0
        }

    text = " ".join(edu_lines).lower()

    # Look for 10th or 12th
    matches = re.findall(
        r"(10th|12th|ssc|hsc)[^0-9]*([4-9]\d(?:\.\d+)?)%",
        text
    )

    if not matches:
        return {"school_score": 0}

    best = max(float(m[1]) for m in matches)

    return {"school_score": best}