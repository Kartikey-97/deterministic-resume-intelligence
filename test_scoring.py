from ingestion.extractor import extract_fitz
from utils.text_cleaner import clean_text
from segmentation.section_detector import segment_resume

# Feature extractors
from features.skill_extractor import extract_skills
from features.experience_extractor import extract_experience
from features.project_extractor import extract_projects
from features.education_extractor import extract_education
from features.minor_extraction import extract_minor_features
from features.achievement_extractor import extract_achievements
from features.extracurricular_extractor import extract_extracurricular
from features.school_extractor import extract_school_marks

# Scoring
from scoring.final_score import compute_final_score


def test_resume(file_path):

    print("=" * 60)
    print("Testing scoring for:", file_path)

    # -----------------------------
    # Extraction
    # -----------------------------
    raw = extract_fitz(file_path)
    clean = clean_text(raw)
    sections = segment_resume(clean)

    # -----------------------------
    # Feature pipeline
    # -----------------------------
    skills = extract_skills(sections)
    experience = extract_experience(sections)
    projects = extract_projects(sections)
    education = extract_education(sections)
    minor = extract_minor_features(sections, clean)
    achievements = extract_achievements(sections)
    extra = extract_extracurricular(sections)
    school = extract_school_marks(sections)

    features = {
        "skills": skills,
        "experience": experience,
        "projects": projects,
        "education": education,
        "minor": minor,
        "achievements": achievements,
        "extracurricular": extra,
        "school": school
    }

    # -----------------------------
    # Scoring
    # -----------------------------
    result = compute_final_score(features)

    print("\nFinal Score:", result["total_score"])
    print("\nBreakdown:")
    for k, v in result["breakdown"].items():
        print(f"{k}: {v}")

    print()


if __name__ == "__main__":
    # Test multiple resumes
    test_resume("data/sample/Resume-Sample-2.pdf")
    test_resume("data/sample/10265057.pdf")
    test_resume("data/sample/10219099.pdf")
    test_resume("data/sample/12022566.pdf")
