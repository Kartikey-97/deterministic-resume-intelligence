def score_internships(exp_features):
    count = exp_features["internship_count"]
    roles = exp_features.get("roles_detected", [])
    
    # 1. Ignore roles where the parser failed to find a date (duration = 0)
    internships = [r for r in roles if r["type"] == "intern" and r["duration_months"] > 0]
    
    valid_count = len(internships)
    total_intern_months = sum(r["duration_months"] for r in internships)
    
    # THE HR MENTOR'S PENALTY (Temporal Density)
    # If they have 4+ internships but average less than 1.5 months each, it's resume padding.
    if valid_count >= 4 and total_intern_months <= (valid_count * 1.5):
        return 0  # Wipe out their internship points completely (Neutralized)
        
    # --- Normal Saturation Curve ---
    if count == 0:
        return 0
    elif count == 1:
        return 10
    elif count == 2:
        return 16
    else: # 3+ internships
        return 20