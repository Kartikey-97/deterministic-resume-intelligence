import os
import re

from ingestion.extractor import extract_text
from utils.text_cleaner import clean_text
from segmentation.section_detector import segment_resume
from features.experience_extractor import extract_experience
from features.skill_extractor import extract_skills
from features.project_extractor import extract_projects
from features.education_extractor import extract_education
from features.achievement_extractor import extract_achievements
from features.extracurricular_extractor import extract_extracurricular
from features.minor_extraction import extract_minor_features
from features.school_extractor import extract_school_marks
from scoring.final_score import compute_final_score


# ==========================================
# PRE-PROCESSOR: DATE NORMALIZATION  (v2)
# ==========================================
def normalize_resume_dates(raw_text: str) -> str:
    """
    Surgically repairs broken PDF date formats without destroying URLs.

    v2: strip ordinal suffixes (21st→21) and leading day numbers (10 Sep 2024→Sep 2024)
        so parse_date() never receives a bare day number as the end-date token.
    """
    text   = raw_text
    months = r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*'

    # 0a. Strip ordinals: "21st" → "21"
    text = re.sub(r'\b(\d{1,2})(st|nd|rd|th)\b', r'\1', text)

    # 0b. Strip leading day numbers: "10 Sep 2024" → "Sep 2024"
    text = re.sub(
        rf'\b\d{{1,2}}\s+({months})\s+(\d{{4}})\b',
        r'\1 \2', text, flags=re.IGNORECASE
    )

    # 1. Remove brackets: [Oct 2025]
    text = re.sub(r'\[|\]', ' ', text)

    # 2. Fix slashed format: "1/July/2024" → "July 2024"
    text = re.sub(
        rf'\b\d{{1,2}}\s*/\s*({months})\s*/\s*(\d{{4}})\b',
        r'\1 \2', text, flags=re.IGNORECASE
    )

    # 3. Dash → "to" for MM/YYYY and Month YYYY forms
    text = re.sub(
        r'(\b\d{1,2}/\d{4}\b)\s*[-–—]\s*(\b\d{1,2}/\d{4}\b|\bPresent\b|\bCurrent\b)',
        r'\1 to \2', text, flags=re.IGNORECASE
    )
    text = re.sub(
        rf'(\b{months}\s+\d{{4}}\b)\s*[-–—]\s*(\b{months}\s+\d{{4}}\b|\bPresent\b|\bCurrent\b)',
        r'\1 to \2', text, flags=re.IGNORECASE
    )

    # 4. YYYY - YYYY → Jan YYYY to Dec YYYY
    text = re.sub(r'(\b\d{4}\b)\s*[-–—]\s*(\b\d{4}\b)',
                  r'Jan \1 to Dec \2', text)
    text = re.sub(
        r'(\b\d{4}\b)\s*[-–—]\s*(\bPresent\b|\bCurrent\b)',
        r'Jan \1 to \2', text, flags=re.IGNORECASE
    )

    # 5. "till present" → "Present"
    text = re.sub(r'\btill present\b', 'Present', text, flags=re.IGNORECASE)

    return text


# ==========================================
# PROFESSION CLASSIFIER  (v4 — final)
# ==========================================
def infer_profession(text: str) -> str:
    """
    Normalised weighted keyword voting.

    Score = (hits / sqrt(keyword_count)) × weight

    v4 changes:
    - Added "front-end web developer", "front end web developer" → Frontend
      (fixes Sagar Gour: his summary says "Front-End Web Developer")
    - Added minimum 2-hit guard for Cybersecurity, AI & ML, DevOps, and Embedded.
      One cert mention (e.g. "Coursera: Networks and Cybersecurity") must NOT
      classify a candidate as Cybersecurity.
      (fixes Dhruv Bansal: 1 cert hit → fall back to Software Engineering)
    - Lowered DevOps weight and tightened keywords so docker+ci/cd alone
      doesn't classify a full-stack dev as DevOps.
    """
    text_lower = text.lower()

    categories = {
        # ── High specificity, high weight ─────────────────────────────────
        "Embedded & IoT": {
            "kw": [
                "embedded systems", "iot", "internet of things",
                "esp32", "arduino", "raspberry pi", "microcontroller",
                "firmware", "rtos", "plc", "scada", "sensor integration",
                "hardware engineer", "smart helmet", "smart device",
                "esp8266", "stm32", "arm cortex"
            ],
            "w": 3.5, "min_hits": 2
        },
        "AI & Machine Learning": {
            "kw": [
                "machine learning", "deep learning", "neural network",
                "nlp", "natural language processing", "computer vision",
                "tensorflow", "pytorch", "keras", "scikit-learn",
                "data science", "data scientist", "reinforcement learning",
                "llm", "generative ai", "ai/ml", "aiml",
                "lstm", "gru", "cnn", "transformer", "bert",
                "ai trainer", "ml engineer", "ml pipeline",
                "dqn", "openai gym", "mfcc", "feature extraction"
            ],
            "w": 3.0, "min_hits": 2
        },
        "Cybersecurity": {
            "kw": [
                "cybersecurity", "penetration testing", "pentesting",
                "ethical hacking", "infosec", "red team", "blue team",
                "soc analyst", "security analyst", "vulnerability assessment",
                "ctf", "exploit", "malware analysis", "forensics", "osint"
            ],
            "w": 3.0, "min_hits": 2   # ← requires 2 hits; 1 cert keyword doesn't count
        },
        "Mobile Developer": {
            "kw": [
                "android developer", "ios developer", "flutter developer",
                "react native developer", "mobile application developer",
                "mobile developer", "kotlin developer", "swift developer",
                "android application", "ios application"
            ],
            "w": 3.0, "min_hits": 2
        },

        # ── Full Stack — weight 3.0 so it beats DevOps for generalist devs ─
        "Full Stack Developer": {
            "kw": [
                "full stack", "full-stack", "fullstack",
                "full stack web", "full-stack web",
                "mern", "mean", "mevn",
                "frontend and backend", "end-to-end development",
                "full stack developer", "full-stack developer",
                "software development intern",
                "web application developer",
                "mern stack developer"
            ],
            "w": 3.0, "min_hits": 1
        },

        # ── Frontend — includes "web" variants to catch Sagar/Vibhor ──────
        "Frontend Developer": {
            "kw": [
                "frontend developer", "front-end developer",
                "frontend engineer", "front-end engineer",
                "front-end web developer",       # ← FIX: Sagar's exact phrase
                "front end web developer",
                "ui developer", "ui/ux developer",
                "shopify", "liquid", "theme customization",
                "website designer", "web designer",
                "gsap animation", "animation developer",
                "react developer", "vue developer", "angular developer"
            ],
            "w": 2.0, "min_hits": 1
        },

        # ── Backend ────────────────────────────────────────────────────────
        "Backend Developer": {
            "kw": [
                "backend developer", "back-end developer",
                "backend engineer", "back-end engineer",
                "rest api design", "api developer",
                "spring boot developer", "django developer",
                "flask developer", "fastapi developer",
                "microservices architect", "server-side developer",
                "node.js developer", "express developer"
            ],
            "w": 2.0, "min_hits": 1
        },

        # ── DevOps — very specific; docker+ci/cd alone is NOT DevOps ──────
        "DevOps & Cloud": {
            "kw": [
                "devops engineer", "site reliability engineer", "sre",
                "kubernetes", "k8s", "terraform", "ansible",
                "jenkins pipeline", "helm charts",
                "infrastructure as code", "cloud architect",
                "aws certified", "azure devops engineer",
                "cloud engineer", "platform engineer",
                "container orchestration"
            ],
            "w": 1.2, "min_hits": 2
        },

        # ── Data Engineering ───────────────────────────────────────────────
        "Data Engineer": {
            "kw": [
                "data engineer", "data pipeline", "etl",
                "apache spark", "hadoop", "kafka",
                "data warehouse", "dbt", "airflow",
                "databricks", "snowflake"
            ],
            "w": 3.0, "min_hits": 2
        },

        # ── Fallback ───────────────────────────────────────────────────────
        "Software Engineering": {
            "kw": [
                "software engineer", "software developer",
                "software engineering", "programmer"
            ],
            "w": 0.8, "min_hits": 1
        },
    }

    scores    = {}
    hit_counts = {}

    for category, cfg in categories.items():
        hits = sum(
            1 for k in cfg["kw"]
            if re.search(r'\b' + re.escape(k) + r'\b', text_lower)
        )
        hit_counts[category] = hits
        # Only score if minimum hit requirement is met
        min_h = cfg.get("min_hits", 1)
        if hits >= min_h:
            scores[category] = (hits / (len(cfg["kw"]) ** 0.5)) * cfg["w"]
        else:
            scores[category] = 0

    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "Software Engineering"


# ==========================================
# MASTER ORCHESTRATOR
# ==========================================
def process_resume(pdf_path: str, custom_weights: dict = None) -> dict:
    try:
        ingestion_result = extract_text(pdf_path)

        if isinstance(ingestion_result, dict):
            raw_text    = ingestion_result.get("raw_text", "")
            fraud_flags = ingestion_result.get("fraud_flags", [])
        else:
            raw_text    = ingestion_result
            fraud_flags = []

        raw_text     = normalize_resume_dates(raw_text)
        cleaned_text = clean_text(raw_text)
        sections     = segment_resume(cleaned_text)

        features = {
            "experience":      extract_experience(sections),
            "skills":          extract_skills(sections),
            "projects":        extract_projects(sections),
            "education":       extract_education(sections),
            "achievements":    extract_achievements(sections),
            "extracurricular": extract_extracurricular(sections),
            "minor":           extract_minor_features(sections, cleaned_text),
            "school":          extract_school_marks(sections)
        }

        score_data = compute_final_score(features, custom_weights)

        score_data["profession"]     = infer_profession(cleaned_text)
        score_data["extracted_data"] = features
        score_data["raw_text"]       = cleaned_text
        score_data["status"]         = "success"
        score_data["fraud_flags"]    = fraud_flags

        if "invisible_text" in fraud_flags or "microscopic_text" in fraud_flags:
            score_data["breakdown"]["WARNING"] = (
                "Hidden/Microscopic text detected and ignored."
            )
            score_data["status"] = "WARNING_ISSUED"

        return score_data

    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")
        return {
            "status":         "error",
            "error_message":  str(e),
            "total_score":    0,
            "breakdown":      {},
            "fresher":        True,
            "completeness":   0,
            "fraud_flags":    [],
            "profession":     "Error Processing",
            "extracted_data": {},
            "raw_text":       "Error extracting text."
        }