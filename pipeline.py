import os

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

def process_resume(pdf_path: str) -> dict:
    """
    The master orchestrator. 
    Takes a PDF path, runs the entire deterministic pipeline, and returns the final score.
    """
    try:
        # Step 1: Text Ingestion
        ingestion_result = extract_text(pdf_path)
        
        # Safety check: Handle both the new dict format and old string format gracefully
        if isinstance(ingestion_result, dict):
            raw_text = ingestion_result.get("raw_text", "")
            fraud_flags = ingestion_result.get("fraud_flags", [])
        else:
            raw_text = ingestion_result
            fraud_flags = []
            
        # Step 2: Cleaning
        cleaned_text = clean_text(raw_text)
        
        # Step 3: Section Segmentation
        sections = segment_resume(cleaned_text)
        
        # Step 4: Feature Extraction
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
        
        # Step 5: Deterministic Scoring
        score_data = compute_final_score(features)
        
        # Step 6: Apply Fraud Penalties & Finalize
        score_data["status"] = "success"
        score_data["fraud_flags"] = fraud_flags
        
        # Immediate penalty if fraud is detected
        if "invisible_text" in fraud_flags:
            score_data["total_score"] = 0 
            # Inject a flag into the breakdown so it's visibly obvious in the Streamlit UI
            score_data["breakdown"]["FRAUD_PENALTY"] = "Triggered (Invisible Text)"
            score_data["status"] = "FRAUD_DETECTED"

        return score_data

    except Exception as e:
        # If a weird PDF breaks the parser, we catch it so the whole Streamlit app doesn't crash
        print(f"Error processing {pdf_path}: {e}")
        return {
            "status": "error",
            "error_message": str(e),
            "total_score": 0,
            "breakdown": {},
            "fresher": True,
            "completeness": 0,
            "fraud_flags": []
        }