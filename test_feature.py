import os
from ingestion.extractor import extract_text, extract_fitz, extract_pdfplumber
from utils.text_cleaner import clean_text
from segmentation.section_detector import segment_resume
from features.skill_extractor import extract_skills
from features.experience_extractor import extract_experience
from features.project_extractor import extract_projects
from features.education_extractor import extract_education
from features.minor_extraction import extract_minor_features
from features.achievement_extractor import extract_achievements
from features.extracurricular_extractor import extract_extracurricular
from features.school_extractor import extract_school_marks




SAMPLE_FOLDER = "data/sample"


def feat():
    file_path = "data/sample/Resume-Sample-2.pdf"
    print("=" * 50)
    print("Testing", file_path)

    try:
        # Extract and clean
        raw_text = extract_fitz(file_path)
        clean_text_data = clean_text(raw_text)

    except Exception as e:
        print("Failed because:", e)
        return

    # Segment
    sections = segment_resume(clean_text_data)

    # ------------------------
    # Feature extraction
    # ------------------------
    skills = extract_skills(sections)
    experience = extract_experience(sections)
    projects = extract_projects(sections)
    education = extract_education(sections)
    minor_features = extract_minor_features(sections, clean_text_data)
    achievements = extract_achievements(sections)
    extra = extract_extracurricular(sections)
    school = extract_school_marks(sections)

    # ------------------------
    # Build unified feature object
    # ------------------------
    features = {
    "skills": skills,
    "experience": experience,
    "projects": projects,
    "education": education,
    "minor": minor_features,
    "achievements": achievements,
    "extracurricular": extra,
    "school": school
}

    # ------------------------
    # Debug prints
    # ------------------------
    print("\nSkill section lines:\n", sections["skills"]["lines"])
    print("\nExtracted skills:\n", skills)

    print("\nExtracted experience:\n", experience)

    print("\nProjects:\n", projects)

    print("\nExtracted Education:\n", education)

    print("\nMinor Features:\n", minor_features)

    print("\nAchievements:\n", achievements)

    print("\nExtracurricular:\n", extra)

    print("\nschool:\n", school)

    print("\nFinal Structured Features:\n")


    print(features)






if __name__ == "__main__":
    feat()