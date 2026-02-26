def score_experience(exp_features):
    years = exp_features["total_experience_years"]
    roles = exp_features.get("roles_detected", [])
    
    # 1. Ignore roles where the parser failed to find a date (duration = 0)
    fulltime_jobs = [r for r in roles if r["type"] == "fulltime" and r["duration_months"] > 0]
    
    # Count true short stints
    short_stints = sum(1 for r in fulltime_jobs if r["duration_months"] < 6)
    
    # Calculate base score
    if years == 0:
        base = 0
    elif years < 1:
        base = 2
    elif years < 3:
        base = 3
    elif years < 5:
        base = 4
    else:
        base = 5
        
    # THE HR MENTOR'S PENALTY (Safely Applied)
    # If they have 3+ valid full-time jobs and the majority are < 6 months
    if len(fulltime_jobs) >= 3 and short_stints >= 2:
        # Reduce their score, but do not let it drop below 0
        base = max(0, base - 2) 
        
    return base