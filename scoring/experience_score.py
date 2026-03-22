import math


def score_experience(exp_features: dict) -> float:
    """
    Returns a score from 0 to 5.0 representing full-time work experience.

    ── Why the old formula was wrong ──────────────────────────────────────
    The original used a coarse step function:
        0yr → 0,  <1yr → 2,  <3yr → 3,  <5yr → 4,  5yr+ → 5

    This caused two problems for a fresher hiring context:
      1. 0.08yr (1 month) and 0.92yr (11 months) both scored 2 — identical.
         A 5-month real dev job (Shivam) scored the same as a 1-week stint.
      2. The difference between 0yr and 1yr was only 2 points, yet the
         difference between 3yr and 5yr was also only 1 point. The curve
         rewarded early experience less than it rewarded seniority — the
         opposite of what fresher HR wants.

    ── The fix: square-root curve calibrated to the fresher market ────────
    Formula: min(sqrt(years / 3.0) × 5, 5.0)

    This gives:
      0.08yr  → 0.82 pts  (honest: 1 month is barely worth anything)
      0.42yr  → 1.87 pts  (Shivam 5mo dev: now meaningfully above zero)
      0.92yr  → 2.77 pts  (Abhinaya ~1yr: clear signal)
      1.92yr  → 4.00 pts  (ABHISHEK ~2yr: 80% of max — correct for 2yr FT)
      3.00yr  → 5.00 pts  (cap hit at 3yr for fresher market)
      5.00yr  → 5.00 pts  (capped — same as 3yr, by design)

    The cap at 3yr reflects that in a fresher hiring pool, 3yr+ seniority
    should be scored identically — the differentiator becomes skills and
    projects, not raw time.

    ── Job-hopping penalty (unchanged from original) ──────────────────────
    3+ validated full-time jobs with the majority lasting <6 months signals
    instability. Score is reduced by 2 points (but never below 0).
    """
    years = exp_features.get("total_experience_years", 0)
    roles = exp_features.get("roles_detected", [])

    # Only count roles where the parser found a real date range
    fulltime_jobs = [r for r in roles if r.get("type") == "fulltime"
                     and r.get("duration_months", 0) > 0]
    short_stints  = sum(1 for r in fulltime_jobs if r.get("duration_months", 0) < 6)

    # ── Square-root curve (calibrated: ceiling = 3yr → 5.0) ──────────────
    if years <= 0:
        base = 0.0
    else:
        base = min(math.sqrt(years / 3.0) * 5.0, 5.0)

    # ── Job-hopping penalty ───────────────────────────────────────────────
    if len(fulltime_jobs) >= 3 and short_stints >= 2:
        base = max(0.0, base - 2.0)

    return round(base, 2)