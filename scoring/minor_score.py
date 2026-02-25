def score_minor(minor_features, school_features):

    score = {}

    # Language (3)
    langs = minor_features["languages_detected"]
    score["language"] = min(len(langs), 3)

    # Online presence (3)
    online = minor_features["online_presence"]
    score["online"] = min(len(online), 3)

    # College ranking (2)
    tier = minor_features["college_tier"]
    if tier == 1:
        score["college"] = 2
    elif tier == 2:
        score["college"] = 1.5
    elif tier == 3:
        score["college"] = 1
    else:
        score["college"] = 0.5

    # School marks (2)
    school = school_features["school_score"]
    if school >= 90:
        score["school"] = 2
    elif school >= 80:
        score["school"] = 1.5
    elif school >= 70:
        score["school"] = 1
    else:
        score["school"] = 0.5

    return score