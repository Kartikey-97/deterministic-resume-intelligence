import os
import re

# 1. Ingestion & Cleaning
from ingestion.extractor import extract_text
from utils.text_cleaner import clean_text

# 2. Segmentation
from segmentation.section_detector import segment_resume

# 3. Feature Extractors
from features.experience_extractor import extract_experience
from features.skill_extractor import extract_skills
from features.project_extractor import extract_projects
from features.education_extractor import extract_education
from features.achievement_extractor import extract_achievements
from features.extracurricular_extractor import extract_extracurricular
from features.minor_extraction import extract_minor_features
from features.school_extractor import extract_school_marks

# 4. Scoring Engine
from scoring.final_score import compute_final_score

# ==========================================
# PRE-PROCESSOR: DATE NORMALIZATION
# ==========================================
def normalize_resume_dates(raw_text: str) -> str:
    """
    Surgically repairs broken PDF dates without destroying URLs.
    Injects 'Jan' and 'Dec' for standalone years so the backend can calculate them.
    """
    text = raw_text
    
    # 1. Remove brackets that students use (e.g., [Oct 2025 - Nov 2025])
    text = re.sub(r'\[|\]', ' ', text)
    
    # 2. Fix Ruchi's specific weird format (1/July/2024 -> July 2024)
    months = r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*'
    text = re.sub(rf'\b\d{{1,2}}\s*/\s*({months})\s*/\s*(\d{{4}})\b', r'\1 \2', text, flags=re.IGNORECASE)
    
    # 3. Safe Dash to "to" Converter (Strictly bounds to numbers/months to protect URLs)
    # MM/YYYY - MM/YYYY
    text = re.sub(r'(\b\d{1,2}/\d{4}\b)\s*[-–—]\s*(\b\d{1,2}/\d{4}\b|\bPresent\b|\bCurrent\b)', r'\1 to \2', text, flags=re.IGNORECASE)
    # Month YYYY - Month YYYY
    text = re.sub(rf'(\b{months}\s+\d{{4}}\b)\s*[-–—]\s*(\b{months}\s+\d{{4}}\b|\bPresent\b|\bCurrent\b)', r'\1 to \2', text, flags=re.IGNORECASE)
    
    # 4. ABHISHEK KUMAR FIX: YYYY - YYYY -> Jan YYYY to Dec YYYY
    text = re.sub(r'(\b\d{4}\b)\s*[-–—]\s*(\b\d{4}\b)', r'Jan \1 to Dec \2', text)
    text = re.sub(r'(\b\d{4}\b)\s*[-–—]\s*(\bPresent\b|\bCurrent\b)', r'Jan \1 to \2', text, flags=re.IGNORECASE)

    # 5. Clean up "till present"
    text = re.sub(r'\btill present\b', 'Present', text, flags=re.IGNORECASE)
    
    return text


def infer_profession(text: str) -> str:
    """
    Deterministic Weighted Voting Classifier.
    """
    text_lower = text.lower()
    
    categories = {
        "AI & Machine Learning": ["machine learning", "artificial intelligence", "data scientist", "nlp", "deep learning", "computer vision", "tensorflow", "keras"],
        "Cybersecurity": ["cybersecurity", "security analyst", "penetration testing", "infosec", "red team", "firewall"],
        "DevOps & Cloud": ["devops", "aws", "cloud architect", "kubernetes", "docker", "azure", "ci/cd"],
        
        # Supercharged Software Engineering to override single "AWS" mentions
        "Software Engineering": ["software engineer", "developer", "full stack", "frontend", "backend", "programmer", "react", "node", "mern", "java", "javascript", "python", "express", "mongodb", "sql", "api", "html", "css", "tailwind"],
        
        "Information Technology": ["information technology", "it support", "sysadmin", "help desk", "network administrator"],
        "Engineering (Core)": ["mechanical engineer", "civil engineer", "electrical engineer", "hardware engineer"],
        "Finance & Banking": ["accountant", "accounting", "finance", "banking", "investment", "cfa", "auditor", "payables", "ledger", "tax"],
        "Legal & Advocate": ["advocate", "lawyer", "attorney", "legal", "paralegal", "litigation"],
        "Business Development": ["business development", "b2b", "strategic partnerships", "sales strategy"],
        "Consultant": ["consultant", "management consulting", "strategy consultant"],
        "Human Resources (HR)": ["hr", "human resources", "recruiter", "talent acquisition", "payroll"],
        "Sales & Marketing": ["sales", "account executive", "marketing", "seo", "digital marketing"],
        "Healthcare & Medical": ["healthcare", "physician", "doctor", "nursing", "clinical", "medical", "hospital"],
        "Education & Teaching": ["teacher", "educator", "professor", "tutor", "instructional"],
        "Design & Creative": ["designer", "ui/ux", "graphic design", "art director", "photoshop", "figma"]
    }

    scores = {}
    for category, keywords in categories.items():
        score = 0
        for k in keywords:
            if re.search(r'\b' + re.escape(k) + r'\b', text_lower):
                score += 1
        scores[category] = score
        
    best_match = max(scores, key=scores.get)
    if scores[best_match] == 0:
        return "General / Uncategorized"
        
    return best_match

# ==========================================
# MASTER ORCHESTRATOR
# ==========================================
def process_resume(pdf_path: str, custom_weights: dict = None) -> dict:
    """
    The master orchestrator. 
    Takes a PDF path, runs the entire deterministic pipeline, and returns the final score.
    """
    try:
        # 1. Ingestion
        ingestion_result = extract_text(pdf_path)
        
        if isinstance(ingestion_result, dict):
            raw_text = ingestion_result.get("raw_text", "")
            fraud_flags = ingestion_result.get("fraud_flags", [])
        else:
            raw_text = ingestion_result
            fraud_flags = []
            
        # 2. Date Repair Pre-Processing
        raw_text = normalize_resume_dates(raw_text)
        
        # 3. Clean and Segment
        cleaned_text = clean_text(raw_text)
        sections = segment_resume(cleaned_text)
        
        # 4. Feature Extraction
        features = {
            "experience": extract_experience(sections),
            "skills": extract_skills(sections),
            "projects": extract_projects(sections),
            "education": extract_education(sections),
            "achievements": extract_achievements(sections),
            "extracurricular": extract_extracurricular(sections),
            "minor": extract_minor_features(sections, cleaned_text),
            "school": extract_school_marks(sections)
        }
        
        # 5. Core Math & Scoring Engine
        score_data = compute_final_score(features, custom_weights)
        
        # 6. Build the Final Output Payload
        score_data["profession"] = infer_profession(cleaned_text)
        score_data["extracted_data"] = features
        score_data["raw_text"] = cleaned_text
        score_data["status"] = "success"
        score_data["fraud_flags"] = fraud_flags
        
        # --- FRAUD CHECK INTERCEPT ---
        if "invisible_text" in fraud_flags or "microscopic_text" in fraud_flags:
            score_data["breakdown"]["WARNING"] = "Hidden/Microscopic text detected and ignored. Please remove this."
            score_data["status"] = "WARNING_ISSUED"

        return score_data

    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")
        return {
            "status": "error",
            "error_message": str(e),
            "total_score": 0,
            "breakdown": {},
            "fresher": True,
            "completeness": 0,
            "fraud_flags": [],
            "profession": "Error Processing",
            "extracted_data": {},
            "raw_text": "Error extracting text."
        }