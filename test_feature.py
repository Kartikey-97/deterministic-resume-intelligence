import os
from ingestion.extractor import extract_text, extract_fitz, extract_pdfplumber
from utils.text_cleaner import clean_text
from segmentation.section_detector import segment_resume
from features.skill_extractor import extract_skills
from features.experience_extractor import extract_experience


SAMPLE_FOLDER = "data/sample"


def feat():
  files2 = "data/sample/10985403.pdf"
  print("=" * 50)
  print("Testing", files2)
  try:
    # Extract and clean
    text2 = clean_text(extract_fitz(files2))
  
  except Exception as e:
        print("Failed cause of : ", e)
    
  sections = segment_resume(text2)

  skills = extract_skills(sections)

  print("\nSkill section lines:\n")
  print(sections["skills"]["lines"])

  print("\nExtracted skills:\n")
  print(skills)

  experience = extract_experience(sections)

  print("\nExtracted experience:\n")
  print(experience)



if __name__ == "__main__":
    feat()